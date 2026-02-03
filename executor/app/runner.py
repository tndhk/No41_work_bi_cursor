"""実行エンジン"""
import io
import pandas as pd
import pyarrow.parquet as pq
from typing import Dict, Any, Optional
import traceback

from app.sandbox import sandbox_context, validate_code, SandboxError, build_safe_builtins
from app.db import get_s3_client, get_bucket_name
from app.resource_limiter import ResourceLimiter, TimeoutError
from app.config import settings


class ExecutionError(Exception):
    """実行エラー"""
    pass


class ExecutionTimeout(Exception):
    """実行タイムアウト"""
    pass


class ResourceLimitError(Exception):
    """リソース制限エラー"""
    pass


async def execute_card(
    code: str,
    dataset_path: str,
    filters: Dict[str, Any],
    params: Dict[str, Any] = None,
    timeout: int = 10,
) -> Dict[str, Any]:
    """Cardを実行"""
    # コード検証
    errors = validate_code(code)
    if errors:
        raise ExecutionError(f"Code validation failed: {', '.join(errors)}")
    
    # データセットを読み込む
    try:
        df = await load_dataset(dataset_path)
    except Exception as e:
        raise ExecutionError(f"Failed to load dataset: {e}")
    
    # フィルタを適用
    filtered_df = apply_filters(df, filters)
    
    # リソース制限を適用
    limiter = ResourceLimiter(
        timeout_seconds=settings.card_timeout_seconds,
        max_memory_mb=settings.card_max_memory_mb,
        max_file_size_mb=settings.card_max_file_size_mb,
    )
    
    # サンドボックス内でコードを実行
    try:
        with limiter.limit():
            with sandbox_context():
                # グローバル名前空間を準備
                namespace = {
                    "__builtins__": build_safe_builtins(),
                    "pd": pd,
                    "pandas": pd,
                    "dataset": filtered_df,
                    "filters": filters,
                    "params": params or {},
                }
                
                # コードを実行
                exec(code, namespace)
                
                # render関数を呼び出す
                if "render" not in namespace:
                    raise ExecutionError("render function not found in code")
                
                render_func = namespace["render"]
                result = render_func(filtered_df, filters, params or {})
                
                # 結果を検証
                if not isinstance(result, dict):
                    raise ExecutionError("render function must return a dict")
                
                if "html" not in result:
                    raise ExecutionError("render function must return dict with 'html' key")
                
                return {
                    "html": result.get("html", ""),
                    "used_columns": result.get("used_columns", []),
                    "filter_applicable": result.get("filter_applicable", []),
                }
    
    except TimeoutError as e:
        raise ExecutionTimeout(f"Execution timeout: {e}")
    except SandboxError as e:
        raise ExecutionError(f"Sandbox error: {e}")
    except Exception as e:
        raise ExecutionError(f"Execution error: {traceback.format_exc()}")


async def execute_transform(
    code: str,
    input_dataset_paths: Dict[str, str],
    timeout: int = 300,
) -> Dict[str, Any]:
    """Transformを実行"""
    # コード検証
    errors = validate_code(code)
    if errors:
        raise ExecutionError(f"Code validation failed: {', '.join(errors)}")
    
    # 入力データセットを読み込む
    inputs = {}
    try:
        for name, path in input_dataset_paths.items():
            inputs[name] = await load_dataset(path)
    except Exception as e:
        raise ExecutionError(f"Failed to load input dataset: {e}")
    
    # リソース制限を適用
    limiter = ResourceLimiter(
        timeout_seconds=settings.transform_timeout_seconds,
        max_memory_mb=settings.transform_max_memory_mb,
        max_file_size_mb=settings.transform_max_file_size_mb,
    )
    
    # サンドボックス内でコードを実行
    try:
        with limiter.limit():
            with sandbox_context():
                # グローバル名前空間を準備
                namespace = {
                    "__builtins__": build_safe_builtins(),
                    "pd": pd,
                    "pandas": pd,
                    "inputs": inputs,
                    "params": {},
                }
                
                # コードを実行
                exec(code, namespace)
                
                # transform関数を呼び出す
                if "transform" not in namespace:
                    raise ExecutionError("transform function not found in code")
                
                transform_func = namespace["transform"]
                result_df = transform_func(inputs, {})
                
                # 結果を検証
                if not isinstance(result_df, pd.DataFrame):
                    raise ExecutionError("transform function must return a DataFrame")
                
                return {
                    "dataframe": result_df,
                    "row_count": len(result_df),
                    "column_count": len(result_df.columns),
                    "columns": list(result_df.columns),
                }
    
    except TimeoutError as e:
        raise ExecutionTimeout(f"Execution timeout: {e}")
    except SandboxError as e:
        raise ExecutionError(f"Sandbox error: {e}")
    except Exception as e:
        raise ExecutionError(f"Execution error: {traceback.format_exc()}")


async def load_dataset(s3_path: str) -> pd.DataFrame:
    """S3からデータセットを読み込む"""
    s3_client = await get_s3_client()
    bucket_name = get_bucket_name("datasets")
    
    try:
        response = await s3_client.get_object(Bucket=bucket_name, Key=s3_path)
        parquet_content = await response["Body"].read()
        
        # Parquetを読み込む
        parquet_buffer = io.BytesIO(parquet_content)
        table = pq.read_table(parquet_buffer)
        df = table.to_pandas()
        
        return df
    except Exception as e:
        raise ExecutionError(f"Failed to load dataset from S3: {e}")


def apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """フィルタを適用"""
    filtered_df = df.copy()
    
    for filter_key, filter_value in filters.items():
        if filter_key not in filtered_df.columns:
            continue
        
        if isinstance(filter_value, list):
            # 複数選択
            filtered_df = filtered_df[filtered_df[filter_key].isin(filter_value)]
        elif isinstance(filter_value, dict):
            # 日付範囲など
            if "start" in filter_value and "end" in filter_value:
                start = filter_value["start"]
                end = filter_value["end"]
                filtered_df = filtered_df[
                    (filtered_df[filter_key] >= start) &
                    (filtered_df[filter_key] <= end)
                ]
        else:
            # 単一値
            filtered_df = filtered_df[filtered_df[filter_key] == filter_value]
    
    return filtered_df
