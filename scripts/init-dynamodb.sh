#!/bin/bash
# DynamoDBテーブル初期化スクリプト

set -e

ENDPOINT="${DYNAMODB_ENDPOINT:-http://localhost:8000}"
REGION="${DYNAMODB_REGION:-ap-northeast-1}"
PREFIX="${DYNAMODB_TABLE_PREFIX:-bi_}"

echo "Initializing DynamoDB tables at $ENDPOINT..."

# AWS CLIがインストールされているか確認
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    echo "Please install AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi

# テーブル作成関数
create_table() {
    local table_name=$1
    local key_schema=$2
    local attribute_definitions=$3
    local gsi=$4
    
    echo "Creating table: $table_name"
    
    local create_cmd="aws dynamodb create-table \
        --table-name $table_name \
        --key-schema $key_schema \
        --attribute-definitions $attribute_definitions \
        --billing-mode PAY_PER_REQUEST \
        --endpoint-url $ENDPOINT \
        --region $REGION"
    
    if [ -n "$gsi" ]; then
        create_cmd="$create_cmd --global-secondary-indexes $gsi"
    fi
    
    $create_cmd || echo "Table $table_name may already exist"
}

# Users テーブル
create_table "${PREFIX}Users" \
    "AttributeName=userId,KeyType=HASH" \
    "AttributeName=userId,AttributeType=S"

# Groups テーブル
create_table "${PREFIX}Groups" \
    "AttributeName=groupId,KeyType=HASH" \
    "AttributeName=groupId,AttributeType=S"

# GroupMembers テーブル
create_table "${PREFIX}GroupMembers" \
    "AttributeName=groupId,KeyType=HASH AttributeName=userId,KeyType=RANGE" \
    "AttributeName=groupId,AttributeType=S AttributeName=userId,AttributeType=S"

# Datasets テーブル
create_table "${PREFIX}Datasets" \
    "AttributeName=datasetId,KeyType=HASH" \
    "AttributeName=datasetId,AttributeType=S AttributeName=ownerId,AttributeType=S AttributeName=createdAt,AttributeType=N" \
    "[{\"IndexName\":\"DatasetsByOwner\",\"KeySchema\":[{\"AttributeName\":\"ownerId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]"

# Transforms テーブル
create_table "${PREFIX}Transforms" \
    "AttributeName=transformId,KeyType=HASH" \
    "AttributeName=transformId,AttributeType=S AttributeName=ownerId,AttributeType=S AttributeName=createdAt,AttributeType=N" \
    "[{\"IndexName\":\"TransformsByOwner\",\"KeySchema\":[{\"AttributeName\":\"ownerId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]"

# Cards テーブル
create_table "${PREFIX}Cards" \
    "AttributeName=cardId,KeyType=HASH" \
    "AttributeName=cardId,AttributeType=S AttributeName=ownerId,AttributeType=S AttributeName=createdAt,AttributeType=N" \
    "[{\"IndexName\":\"CardsByOwner\",\"KeySchema\":[{\"AttributeName\":\"ownerId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]"

# Dashboards テーブル
create_table "${PREFIX}Dashboards" \
    "AttributeName=dashboardId,KeyType=HASH" \
    "AttributeName=dashboardId,AttributeType=S AttributeName=ownerId,AttributeType=S AttributeName=createdAt,AttributeType=N AttributeName=sharedUserId,AttributeType=S AttributeName=sharedGroupId,AttributeType=S" \
    "[{\"IndexName\":\"DashboardsByOwner\",\"KeySchema\":[{\"AttributeName\":\"ownerId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}},{\"IndexName\":\"DashboardsBySharedUser\",\"KeySchema\":[{\"AttributeName\":\"sharedUserId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"dashboardId\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}},{\"IndexName\":\"DashboardsBySharedGroup\",\"KeySchema\":[{\"AttributeName\":\"sharedGroupId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"dashboardId\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]"

# DashboardShares テーブル
create_table "${PREFIX}DashboardShares" \
    "AttributeName=shareId,KeyType=HASH" \
    "AttributeName=shareId,AttributeType=S AttributeName=dashboardId,AttributeType=S AttributeName=createdAt,AttributeType=N" \
    "[{\"IndexName\":\"SharesByDashboard\",\"KeySchema\":[{\"AttributeName\":\"dashboardId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]"

# FilterViews テーブル
create_table "${PREFIX}FilterViews" \
    "AttributeName=filterViewId,KeyType=HASH" \
    "AttributeName=filterViewId,AttributeType=S AttributeName=dashboardId,AttributeType=S AttributeName=createdAt,AttributeType=N" \
    "[{\"IndexName\":\"FilterViewsByDashboard\",\"KeySchema\":[{\"AttributeName\":\"dashboardId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"createdAt\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]"

# AuditLogs テーブル
create_table "${PREFIX}AuditLogs" \
    "AttributeName=logId,KeyType=HASH" \
    "AttributeName=logId,AttributeType=S AttributeName=timestamp,AttributeType=N AttributeName=targetId,AttributeType=S" \
    "[{\"IndexName\":\"LogsByTimestamp\",\"KeySchema\":[{\"AttributeName\":\"timestamp\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"logId\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}},{\"IndexName\":\"LogsByTarget\",\"KeySchema\":[{\"AttributeName\":\"targetId\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"timestamp\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]"

echo "DynamoDB tables initialization completed!"
