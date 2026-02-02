"""Chatbotサービス"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import io
import logging

import pandas as pd
import pyarrow.parquet as pq
import vertexai
from vertexai.preview.generative_models import GenerativeModel

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.db.s3 import get_s3_client, get_bucket_name
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.services.dataset_service import get_dataset
from app.services.dashboard_service import get_referenced_datasets

logger = logging.getLogger(__name__)


RATE_LIMIT_TABLE = get_table_name("RateLimits")
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 10


class RateLimitExceeded(Exception):
    """レート制限超過エラー"""
    pass


async def check_rate_limit(user_id: str) -> None:
    """レート制限チェック
    
    Args:
        user_id: ユーザーID
        
    Raises:
        RateLimitExceeded: レート制限を超過した場合
    """
    client = await get_dynamodb_client()
    now = int(datetime.utcnow().timestamp())
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    
    # レート制限キー: chatbot_{user_id}
    rate_limit_key = f"chatbot_{user_id}"
    
    try:
        # 現在のレート制限状態を取得
        response = await client.get_item(
            TableName=RATE_LIMIT_TABLE,
            Key={"key": {"S": rate_limit_key}},
        )
        
        if "Item" in response:
            item = response["Item"]
            requests = []
            
            # リクエストタイムスタンプリストを取得
            if "requests" in item and "L" in item["requests"]:
                for req in item["requests"]["L"]:
                    if "N" in req:
                        timestamp = int(req["N"])
                        # ウィンドウ内のリクエストのみ保持
                        if timestamp > window_start:
                            requests.append(timestamp)
            
            # レート制限チェック
            if len(requests) >= RATE_LIMIT_MAX_REQUESTS:
                raise RateLimitExceeded(
                    f"Rate limit exceeded. Max {RATE_LIMIT_MAX_REQUESTS} requests per minute."
                )
            
            # 現在のリクエストを追加
            requests.append(now)
        else:
            # 初回リクエスト
            requests = [now]
        
        # レート制限状態を更新
        await client.put_item(
            TableName=RATE_LIMIT_TABLE,
            Item={
                "key": {"S": rate_limit_key},
                "requests": {"L": [{"N": str(ts)} for ts in requests]},
                "ttl": {"N": str(now + 3600)},  # 1時間後に自動削除
            },
        )
    except RateLimitExceeded:
        raise
    except Exception as e:
        # レート制限チェック失敗時は通過させる（可用性優先）
        logger.warning(f"Rate limit check failed for user {user_id}: {e}")


def _calculate_column_stats(df: pd.DataFrame, col: str) -> Dict[str, Any]:
    """列の統計情報を計算
    
    Args:
        df: DataFrame
        col: 列名
        
    Returns:
        列の統計情報
    """
    col_stats = {"column": str(col)}
    
    if pd.api.types.is_numeric_dtype(df[col]):
        col_stats["type"] = "numeric"
        if not df[col].isna().all():
            col_stats["min"] = float(df[col].min())
            col_stats["max"] = float(df[col].max())
            col_stats["mean"] = float(df[col].mean())
        else:
            col_stats["min"] = None
            col_stats["max"] = None
            col_stats["mean"] = None
        col_stats["null_count"] = int(df[col].isna().sum())
    else:
        col_stats["type"] = "categorical"
        col_stats["unique_count"] = int(df[col].nunique())
        col_stats["null_count"] = int(df[col].isna().sum())
        if not df[col].isna().all():
            top_values = df[col].value_counts().head(3).to_dict()
            col_stats["top_values"] = {str(k): int(v) for k, v in top_values.items()}
    
    return col_stats


async def generate_dataset_summary(dataset_id: str) -> Dict[str, Any]:
    """Datasetのサマリを生成
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        サマリ情報（スキーマ、サンプル行、統計情報）
    """
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    s3_client = await get_s3_client()
    bucket_name = get_bucket_name("datasets")
    
    try:
        response = await s3_client.get_object(Bucket=bucket_name, Key=dataset.s3_path)
        parquet_content = await response["Body"].read()
        
        parquet_buffer = io.BytesIO(parquet_content)
        table = pq.read_table(parquet_buffer)
        df = table.to_pandas()
        
        schema_info = [
            {
                "name": col.name,
                "dtype": col.dtype,
                "nullable": col.nullable,
            }
            for col in dataset.schema
        ]
        
        sample_rows = df.head(5).to_dict("records")
        stats = {str(col): _calculate_column_stats(df, col) for col in df.columns}
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "schema": schema_info,
            "sample_rows": sample_rows,
            "statistics": stats,
        }
    except Exception as e:
        raise ValueError(f"Failed to generate dataset summary: {e}")


def _format_numeric_stats(col_name: str, col_stats: Dict[str, Any]) -> str:
    """数値列の統計情報をフォーマット"""
    mean_val = col_stats.get('mean')
    mean_str = f"{mean_val:.2f}" if mean_val is not None else "N/A"
    return (
        f"- {col_name}: "
        f"min={col_stats.get('min')}, "
        f"max={col_stats.get('max')}, "
        f"mean={mean_str}"
    )


def _format_categorical_stats(col_name: str, col_stats: Dict[str, Any]) -> List[str]:
    """カテゴリ列の統計情報をフォーマット"""
    lines = [f"- {col_name}: {col_stats['unique_count']} unique values"]
    if 'top_values' in col_stats:
        top_str = ", ".join(f"{k}({v})" for k, v in col_stats['top_values'].items())
        lines.append(f"  Top values: {top_str}")
    return lines


def _build_prompt(message: str, dataset_summaries: List[Dict[str, Any]]) -> str:
    """プロンプトを構築
    
    Args:
        message: ユーザーの質問
        dataset_summaries: Datasetサマリのリスト
        
    Returns:
        構築されたプロンプト
    """
    prompt_parts = [
        "あなたはデータ分析アシスタントです。以下のデータセットに関する質問に回答してください。",
        "",
        "# データセット情報",
        ""
    ]
    
    for summary in dataset_summaries:
        prompt_parts.extend([
            f"## Dataset: {summary['dataset_name']}",
            f"- 行数: {summary['row_count']:,}",
            f"- 列数: {summary['column_count']}",
            "",
            "### スキーマ"
        ])
        
        for col in summary['schema']:
            prompt_parts.append(f"- {col['name']} ({col['dtype']})")
        prompt_parts.append("")
        
        prompt_parts.append("### サンプルデータ（先頭5行）")
        if summary['sample_rows']:
            headers = list(summary['sample_rows'][0].keys())
            prompt_parts.extend([
                " | ".join(headers),
                " | ".join(["---"] * len(headers))
            ])
            for row in summary['sample_rows']:
                prompt_parts.append(" | ".join(str(row.get(h, "")) for h in headers))
        prompt_parts.append("")
        
        prompt_parts.append("### 統計情報")
        for col_name, col_stats in summary['statistics'].items():
            if col_stats['type'] == 'numeric':
                prompt_parts.append(_format_numeric_stats(col_name, col_stats))
            else:
                prompt_parts.extend(_format_categorical_stats(col_name, col_stats))
        prompt_parts.append("")
    
    prompt_parts.extend([
        "# 質問",
        message,
        "",
        "回答は日本語で、簡潔かつ分かりやすく説明してください。"
    ])
    
    return "\n".join(prompt_parts)


async def chat(dashboard_id: str, message: str, user_id: str) -> Dict[str, Any]:
    """Vertex AIとチャット
    
    Args:
        dashboard_id: Dashboard ID
        message: ユーザーの質問
        user_id: ユーザーID
        
    Returns:
        チャット応答（answer, datasets_used）
        
    Raises:
        NotFoundError: Dashboardが見つからない場合
        RateLimitExceeded: レート制限を超過した場合
    """
    # レート制限チェック
    await check_rate_limit(user_id)
    
    # Dashboard参照Datasetを取得
    dataset_ids = await get_referenced_datasets(dashboard_id)
    
    if not dataset_ids:
        return {
            "answer": "このダッシュボードにはデータセットが関連付けられていません。",
            "datasets_used": [],
        }
    
    # 各Datasetのサマリを生成
    dataset_summaries = []
    for dataset_id in dataset_ids:
        try:
            summary = await generate_dataset_summary(dataset_id)
            dataset_summaries.append(summary)
        except Exception as e:
            # 個別のDataset取得エラーは無視（他のDatasetで回答）
            pass
    
    if not dataset_summaries:
        return {
            "answer": "データセットの情報を取得できませんでした。",
            "datasets_used": [],
        }
    
    # プロンプトを構築
    prompt = _build_prompt(message, dataset_summaries)
    
    # Vertex AIを初期化
    if not settings.vertex_ai_project_id:
        return {
            "answer": "Vertex AIが設定されていません。管理者に連絡してください。",
            "datasets_used": dataset_ids,
        }
    
    try:
        vertexai.init(
            project=settings.vertex_ai_project_id,
            location=settings.vertex_ai_location,
        )
        
        model = GenerativeModel(settings.vertex_ai_model)
        response = model.generate_content(prompt)
        
        answer = response.text if response.text else "回答を生成できませんでした。"
        
        return {
            "answer": answer,
            "datasets_used": dataset_ids,
        }
    except Exception as e:
        return {
            "answer": f"エラーが発生しました: {str(e)}",
            "datasets_used": dataset_ids,
        }
