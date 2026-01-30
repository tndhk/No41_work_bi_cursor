"""S3接続層のテスト"""
import pytest
from moto import mock_s3
import boto3

from app.db.s3 import get_s3_client, get_bucket_name


@pytest.fixture
def s3_mock():
    """S3モック"""
    with mock_s3():
        s3 = boto3.client("s3", region_name="ap-northeast-1")
        s3.create_bucket(Bucket="bi-datasets")
        s3.create_bucket(Bucket="bi-static")
        yield s3


@pytest.mark.asyncio
async def test_get_s3_client():
    """S3クライアントを取得できる"""
    client = await get_s3_client()
    assert client is not None


def test_get_bucket_name_datasets():
    """Datasetバケット名を取得できる"""
    bucket_name = get_bucket_name("datasets")
    assert bucket_name == "bi-datasets"


def test_get_bucket_name_static():
    """Staticバケット名を取得できる"""
    bucket_name = get_bucket_name("static")
    assert bucket_name == "bi-static"
