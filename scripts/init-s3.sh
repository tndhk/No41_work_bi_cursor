#!/bin/bash
# S3バケット初期化スクリプト

set -e

ENDPOINT="${S3_ENDPOINT:-http://localhost:9000}"
ACCESS_KEY="${S3_ACCESS_KEY:-minioadmin}"
SECRET_KEY="${S3_SECRET_KEY:-minioadmin}"
BUCKET_DATASETS="${S3_BUCKET_DATASETS:-bi-datasets}"
BUCKET_STATIC="${S3_BUCKET_STATIC:-bi-static}"

echo "Initializing S3 buckets at $ENDPOINT..."

# AWS CLIがインストールされているか確認
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# バケット作成関数
create_bucket() {
    local bucket_name=$1
    echo "Creating bucket: $bucket_name"
    
    aws s3 mb "s3://$bucket_name" \
        --endpoint-url "$ENDPOINT" \
        || echo "Bucket $bucket_name may already exist"
}

# 環境変数設定
export AWS_ACCESS_KEY_ID="$ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="$SECRET_KEY"

# バケット作成
create_bucket "$BUCKET_DATASETS"
create_bucket "$BUCKET_STATIC"

echo "S3 buckets initialization completed!"
