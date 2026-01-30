"""Datasetサービス"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid
import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.db.s3 import get_s3_client, get_bucket_name
from app.core.exceptions import NotFoundError
from app.models.dataset import Dataset, DatasetCreate, DatasetUpdate, ColumnSchema, DatasetPreview


DATASETS_TABLE = get_table_name("Datasets")


def _item_to_dataset(item: dict) -> Dataset:
    """DynamoDBアイテムをDatasetモデルに変換"""
    from app.models.dataset import ColumnSchema
    
    schema_list = []
    if "schema" in item and "L" in item["schema"]:
        for col in item["schema"]["L"]:
            col_map = col.get("M", {})
            schema_list.append(ColumnSchema(
                name=col_map.get("name", {}).get("S", ""),
                dtype=col_map.get("dtype", {}).get("S", ""),
                nullable=col_map.get("nullable", {}).get("BOOL", True),
            ))
    
    return Dataset(
        dataset_id=item["datasetId"]["S"],
        name=item["name"]["S"],
        owner_id=item["ownerId"]["S"],
        source_type=item["sourceType"]["S"],
        source_config=_parse_map_attribute(item.get("sourceConfig", {})),
        schema=schema_list,
        row_count=int(item.get("rowCount", {}).get("N", "0")),
        column_count=int(item.get("columnCount", {}).get("N", "0")),
        s3_path=item["s3Path"]["S"],
        partition_column=item.get("partitionColumn", {}).get("S") if "partitionColumn" in item else None,
        created_at=datetime.fromtimestamp(int(item["createdAt"]["N"])),
        updated_at=datetime.fromtimestamp(int(item["updatedAt"]["N"])),
        last_import_at=datetime.fromtimestamp(int(item["lastImportAt"]["N"])) if "lastImportAt" in item else None,
        last_import_by=item.get("lastImportBy", {}).get("S") if "lastImportBy" in item else None,
    )


def _parse_map_attribute(attr: dict) -> Dict[str, Any]:
    """DynamoDBのMap属性をPython辞書に変換"""
    result = {}
    if "M" in attr:
        for key, value in attr["M"].items():
            if "S" in value:
                result[key] = value["S"]
            elif "N" in value:
                result[key] = float(value["N"]) if "." in value["N"] else int(value["N"])
            elif "BOOL" in value:
                result[key] = value["BOOL"]
            elif "M" in value:
                result[key] = _parse_map_attribute(value)
            elif "L" in value:
                result[key] = [_parse_map_attribute(v) if "M" in v else v.get("S", "") for v in value["L"]]
    return result


def _dict_to_dynamodb_item(data: dict) -> dict:
    """辞書をDynamoDBアイテム形式に変換"""
    item = {}
    for key, value in data.items():
        if isinstance(value, str):
            item[key] = {"S": value}
        elif isinstance(value, bool):
            item[key] = {"BOOL": value}
        elif isinstance(value, (int, float)):
            item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            item[key] = {"M": _dict_to_dynamodb_item(value)}
        elif isinstance(value, list):
            list_items = []
            for v in value:
                if isinstance(v, dict):
                    list_items.append({"M": _dict_to_dynamodb_item(v)})
                elif isinstance(v, list):
                    list_items.append({
                        "L": [
                            {"M": _dict_to_dynamodb_item(x)} if isinstance(x, dict)
                            else {"BOOL": x} if isinstance(x, bool)
                            else {"N": str(x)} if isinstance(x, (int, float))
                            else {"S": str(x)}
                            for x in v
                        ]
                    })
                elif isinstance(v, bool):
                    list_items.append({"BOOL": v})
                elif isinstance(v, (int, float)):
                    list_items.append({"N": str(v)})
                else:
                    list_items.append({"S": str(v)})
            item[key] = {"L": list_items}
        else:
            item[key] = {"S": str(value)}
    return item


def _schema_to_dynamodb(schema: List[ColumnSchema]) -> dict:
    """スキーマをDynamoDB形式に変換"""
    return [
        {
            "name": col.name,
            "dtype": col.dtype,
            "nullable": col.nullable,
        }
        for col in schema
    ]


async def create_dataset_from_local_csv(
    user_id: str,
    name: str,
    csv_content: bytes,
    encoding: str = "utf-8",
    delimiter: str = ",",
    has_header: bool = True,
) -> Dataset:
    """ローカルCSVからDatasetを作成"""
    # CSVを読み込む
    try:
        df = pd.read_csv(
            io.BytesIO(csv_content),
            encoding=encoding,
            sep=delimiter,
            header=0 if has_header else None,
        )
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")
    
    if df.empty:
        raise ValueError("CSV has no data")
    
    # スキーマを生成
    schema = [
        ColumnSchema(
            name=str(col),
            dtype=str(df[col].dtype),
            nullable=df[col].isna().any(),
        )
        for col in df.columns
    ]
    
    # Parquetに変換してS3に保存
    dataset_id = f"dataset_{uuid.uuid4().hex[:12]}"
    s3_path = f"datasets/{dataset_id}/data.parquet"
    
    parquet_buffer = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, parquet_buffer)
    parquet_buffer.seek(0)
    
    s3_client = await get_s3_client()
    bucket_name = get_bucket_name("datasets")
    await s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_path,
        Body=parquet_buffer.getvalue(),
    )
    
    # DynamoDBにメタデータを保存
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "datasetId": dataset_id,
        "name": name,
        "ownerId": user_id,
        "sourceType": "local_csv",
        "sourceConfig": {
            "encoding": encoding,
            "delimiter": delimiter,
            "has_header": has_header,
        },
        "schema": _schema_to_dynamodb(schema),
        "rowCount": len(df),
        "columnCount": len(df.columns),
        "s3Path": s3_path,
        "createdAt": now,
        "updatedAt": now,
        "lastImportAt": now,
        "lastImportBy": user_id,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=DATASETS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return Dataset(
        dataset_id=dataset_id,
        name=name,
        owner_id=user_id,
        source_type="local_csv",
        source_config=item_data["sourceConfig"],
        schema=schema,
        row_count=len(df),
        column_count=len(df.columns),
        s3_path=s3_path,
        partition_column=None,
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
        last_import_at=datetime.fromtimestamp(now),
        last_import_by=user_id,
    )


async def create_dataset_from_s3_csv(
    user_id: str,
    name: str,
    bucket: str,
    key: str,
    encoding: str = "utf-8",
    delimiter: str = ",",
    has_header: bool = True,
) -> Dataset:
    """S3 CSVからDatasetを作成"""
    # S3からCSVをダウンロード
    s3_client = await get_s3_client()
    try:
        response = await s3_client.get_object(Bucket=bucket, Key=key)
        csv_content = await response["Body"].read()
    except Exception as e:
        raise ValueError(f"Failed to download CSV from S3: {e}")
    
    # CSVを読み込む
    try:
        df = pd.read_csv(
            io.BytesIO(csv_content),
            encoding=encoding,
            sep=delimiter,
            header=0 if has_header else None,
        )
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")
    
    if df.empty:
        raise ValueError("CSV has no data")
    
    # スキーマを生成
    schema = [
        ColumnSchema(
            name=str(col),
            dtype=str(df[col].dtype),
            nullable=df[col].isna().any(),
        )
        for col in df.columns
    ]
    
    # Parquetに変換してS3に保存
    dataset_id = f"dataset_{uuid.uuid4().hex[:12]}"
    s3_path = f"datasets/{dataset_id}/data.parquet"
    
    parquet_buffer = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, parquet_buffer)
    parquet_buffer.seek(0)
    
    datasets_bucket = get_bucket_name("datasets")
    await s3_client.put_object(
        Bucket=datasets_bucket,
        Key=s3_path,
        Body=parquet_buffer.getvalue(),
    )
    
    # DynamoDBにメタデータを保存
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "datasetId": dataset_id,
        "name": name,
        "ownerId": user_id,
        "sourceType": "s3_csv",
        "sourceConfig": {
            "bucket": bucket,
            "key": key,
            "encoding": encoding,
            "delimiter": delimiter,
            "has_header": has_header,
        },
        "schema": _schema_to_dynamodb(schema),
        "rowCount": len(df),
        "columnCount": len(df.columns),
        "s3Path": s3_path,
        "createdAt": now,
        "updatedAt": now,
        "lastImportAt": now,
        "lastImportBy": user_id,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=DATASETS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return Dataset(
        dataset_id=dataset_id,
        name=name,
        owner_id=user_id,
        source_type="s3_csv",
        source_config=item_data["sourceConfig"],
        schema=schema,
        row_count=len(df),
        column_count=len(df.columns),
        s3_path=s3_path,
        partition_column=None,
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
        last_import_at=datetime.fromtimestamp(now),
        last_import_by=user_id,
    )


async def get_dataset(dataset_id: str) -> Optional[Dataset]:
    """Datasetを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=DATASETS_TABLE,
        Key={"datasetId": {"S": dataset_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_dataset(response["Item"])


async def list_datasets(
    owner_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    q: Optional[str] = None,
) -> Tuple[List[Dataset], int]:
    """Dataset一覧を取得"""
    client = await get_dynamodb_client()
    
    if owner_id:
        # GSIを使用してownerIdでクエリ
        response = await client.query(
            TableName=DATASETS_TABLE,
            IndexName="DatasetsByOwner",
            KeyConditionExpression="ownerId = :ownerId",
            ExpressionAttributeValues={
                ":ownerId": {"S": owner_id}
            },
            Limit=limit + offset,
            ScanIndexForward=False,  # 新しい順
        )
        items = response.get("Items", [])
    else:
        # Scan
        response = await client.scan(
            TableName=DATASETS_TABLE,
            Limit=limit + offset,
        )
        items = response.get("Items", [])
    
    datasets = [_item_to_dataset(item) for item in items]
    
    if q:
        datasets = [d for d in datasets if q.lower() in d.name.lower()]
    
    total = len(datasets)
    return datasets[offset:offset+limit], total


async def update_dataset(dataset_id: str, dataset_data: DatasetUpdate) -> Dataset:
    """Datasetを更新"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    if dataset_data.name is not None:
        update_expressions.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = {"S": dataset_data.name}
    
    if not update_expressions:
        return dataset
    
    now = int(datetime.utcnow().timestamp())
    update_expressions.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = {"N": str(now)}
    
    client = await get_dynamodb_client()
    update_expression = f"SET {', '.join(update_expressions)}"
    
    update_kwargs = {
        "TableName": DATASETS_TABLE,
        "Key": {"datasetId": {"S": dataset_id}},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    await client.update_item(**update_kwargs)
    
    return await get_dataset(dataset_id)


async def delete_dataset(dataset_id: str) -> None:
    """Datasetを削除"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    client = await get_dynamodb_client()
    
    # DynamoDBから削除
    await client.delete_item(
        TableName=DATASETS_TABLE,
        Key={"datasetId": {"S": dataset_id}},
    )
    
    # S3からも削除（オプション）
    # s3_client = await get_s3_client()
    # bucket_name = get_bucket_name("datasets")
    # try:
    #     await s3_client.delete_object(Bucket=bucket_name, Key=dataset.s3_path)
    # except Exception:
    #     pass  # エラーは無視


async def reimport_dataset(dataset_id: str, user_id: str) -> Dataset:
    """Datasetを再取り込み"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    # 元のスキーマを保存（変更検知用）
    old_schema = dataset.schema
    
    if dataset.source_type == "local_csv":
        raise ValueError("Local CSV reimport is not supported. Please upload again.")
    elif dataset.source_type == "s3_csv":
        config = dataset.source_config
        new_dataset = await create_dataset_from_s3_csv(
            user_id=user_id,
            name=dataset.name,
            bucket=config["bucket"],
            key=config["key"],
            encoding=config.get("encoding", "utf-8"),
            delimiter=config.get("delimiter", ","),
            has_header=config.get("has_header", True),
        )
    else:
        raise ValueError(f"Reimport not supported for source type: {dataset.source_type}")
    
    # スキーマ変更を検知
    schema_changed = False
    if len(old_schema) != len(new_dataset.schema):
        schema_changed = True
    else:
        for old_col, new_col in zip(old_schema, new_dataset.schema):
            if old_col.name != new_col.name or old_col.dtype != new_col.dtype:
                schema_changed = True
                break
    
    # 既存のDatasetを更新（新しいS3パスに更新）
    now = int(datetime.utcnow().timestamp())
    
    client = await get_dynamodb_client()
    await client.update_item(
        TableName=DATASETS_TABLE,
        Key={"datasetId": {"S": dataset_id}},
        UpdateExpression="SET s3Path = :s3Path, rowCount = :rowCount, columnCount = :columnCount, schema = :schema, lastImportAt = :lastImportAt, lastImportBy = :lastImportBy, updatedAt = :updatedAt",
        ExpressionAttributeValues={
            ":s3Path": {"S": new_dataset.s3_path},
            ":rowCount": {"N": str(new_dataset.row_count)},
            ":columnCount": {"N": str(new_dataset.column_count)},
            ":schema": _dict_to_dynamodb_item({"schema": _schema_to_dynamodb(new_dataset.schema)})["schema"],
            ":lastImportAt": {"N": str(now)},
            ":lastImportBy": {"S": user_id},
            ":updatedAt": {"N": str(now)},
        },
    )
    
    # スキーマ変更フラグを追加
    updated_dataset = await get_dataset(dataset_id)
    if schema_changed:
        # メタデータにスキーマ変更フラグを追加（一時的）
        updated_dataset.source_config["schema_changed"] = True
    
    return updated_dataset


async def get_dataset_preview(dataset_id: str, limit: int = 100) -> DatasetPreview:
    """Datasetプレビューを取得"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    # S3からParquetを読み込む
    s3_client = await get_s3_client()
    bucket_name = get_bucket_name("datasets")
    
    try:
        response = await s3_client.get_object(Bucket=bucket_name, Key=dataset.s3_path)
        parquet_content = await response["Body"].read()
        
        # Parquetを読み込む
        parquet_buffer = io.BytesIO(parquet_content)
        table = pq.read_table(parquet_buffer)
        df = table.to_pandas()
        
        # 先頭limit行を取得
        preview_df = df.head(limit)
        
        return DatasetPreview(
            columns=list(preview_df.columns),
            rows=preview_df.to_dict("records"),
            total_rows=len(df),
        )
    except Exception as e:
        raise ValueError(f"Failed to load dataset preview: {e}")
