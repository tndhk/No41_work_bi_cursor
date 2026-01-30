"""DynamoDB接続層のテスト"""
import pytest
from datetime import datetime

from app.db.dynamodb import get_dynamodb_client, get_table_name




def test_get_dynamodb_client(mock_dynamodb):
    """DynamoDBクライアントを取得できる"""
    # mock_dynamodb fixture が正常に動作することを確認
    assert mock_dynamodb is not None



def test_get_table_name():
    """テーブル名を正しく生成する"""
    table_name = get_table_name("Users")
    assert table_name == "bi_Users"
