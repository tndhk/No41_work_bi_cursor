"""S3接続層のテスト"""
import pytest

from app.db.s3 import get_s3_client, get_bucket_name




def test_get_s3_client(mock_s3):
    """S3クライアントを取得できる"""
    # mock_s3 fixture が正常に動作することを確認
    assert mock_s3 is not None



def test_get_bucket_name_datasets():
    """Datasetバケット名を取得できる"""
    bucket_name = get_bucket_name("datasets")
    assert bucket_name == "bi-datasets"



def test_get_bucket_name_static():
    """Staticバケット名を取得できる"""
    bucket_name = get_bucket_name("static")
    assert bucket_name == "bi-static"
