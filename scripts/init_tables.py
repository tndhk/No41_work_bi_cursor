#!/usr/bin/env python3
"""DynamoDB tables initialization script using aioboto3"""

import asyncio
import os
import aioboto3

ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8001")
REGION = os.getenv("DYNAMODB_REGION", "ap-northeast-1")
PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "bi_")


async def create_table(session, table_name, key_schema, attribute_definitions, gsi=None):
    """Create a DynamoDB table"""
    async with session.client(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    ) as dynamodb:
        try:
            params = {
                "TableName": table_name,
                "KeySchema": key_schema,
                "AttributeDefinitions": attribute_definitions,
                "BillingMode": "PAY_PER_REQUEST",
            }
            if gsi:
                params["GlobalSecondaryIndexes"] = gsi

            await dynamodb.create_table(**params)
            print(f"✓ Created table: {table_name}")
        except dynamodb.exceptions.ResourceInUseException:
            print(f"- Table {table_name} already exists")
        except Exception as e:
            print(f"✗ Error creating table {table_name}: {e}")


async def main():
    """Initialize all DynamoDB tables"""
    print(f"Initializing DynamoDB tables at {ENDPOINT}...")

    session = aioboto3.Session()

    # Users table
    await create_table(
        session,
        f"{PREFIX}Users",
        [{"AttributeName": "userId", "KeyType": "HASH"}],
        [{"AttributeName": "userId", "AttributeType": "S"}],
    )

    # Groups table
    await create_table(
        session,
        f"{PREFIX}Groups",
        [{"AttributeName": "groupId", "KeyType": "HASH"}],
        [{"AttributeName": "groupId", "AttributeType": "S"}],
    )

    # GroupMembers table
    await create_table(
        session,
        f"{PREFIX}GroupMembers",
        [
            {"AttributeName": "groupId", "KeyType": "HASH"},
            {"AttributeName": "userId", "KeyType": "RANGE"},
        ],
        [
            {"AttributeName": "groupId", "AttributeType": "S"},
            {"AttributeName": "userId", "AttributeType": "S"},
        ],
    )

    # Datasets table
    await create_table(
        session,
        f"{PREFIX}Datasets",
        [{"AttributeName": "datasetId", "KeyType": "HASH"}],
        [
            {"AttributeName": "datasetId", "AttributeType": "S"},
            {"AttributeName": "ownerId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "N"},
        ],
        [
            {
                "IndexName": "DatasetsByOwner",
                "KeySchema": [
                    {"AttributeName": "ownerId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

    # Transforms table
    await create_table(
        session,
        f"{PREFIX}Transforms",
        [{"AttributeName": "transformId", "KeyType": "HASH"}],
        [
            {"AttributeName": "transformId", "AttributeType": "S"},
            {"AttributeName": "ownerId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "N"},
        ],
        [
            {
                "IndexName": "TransformsByOwner",
                "KeySchema": [
                    {"AttributeName": "ownerId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

    # Cards table
    await create_table(
        session,
        f"{PREFIX}Cards",
        [{"AttributeName": "cardId", "KeyType": "HASH"}],
        [
            {"AttributeName": "cardId", "AttributeType": "S"},
            {"AttributeName": "ownerId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "N"},
        ],
        [
            {
                "IndexName": "CardsByOwner",
                "KeySchema": [
                    {"AttributeName": "ownerId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

    # Dashboards table
    await create_table(
        session,
        f"{PREFIX}Dashboards",
        [{"AttributeName": "dashboardId", "KeyType": "HASH"}],
        [
            {"AttributeName": "dashboardId", "AttributeType": "S"},
            {"AttributeName": "ownerId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "N"},
            {"AttributeName": "sharedUserId", "AttributeType": "S"},
            {"AttributeName": "sharedGroupId", "AttributeType": "S"},
        ],
        [
            {
                "IndexName": "DashboardsByOwner",
                "KeySchema": [
                    {"AttributeName": "ownerId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "DashboardsBySharedUser",
                "KeySchema": [
                    {"AttributeName": "sharedUserId", "KeyType": "HASH"},
                    {"AttributeName": "dashboardId", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "DashboardsBySharedGroup",
                "KeySchema": [
                    {"AttributeName": "sharedGroupId", "KeyType": "HASH"},
                    {"AttributeName": "dashboardId", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    )

    # DashboardShares table
    await create_table(
        session,
        f"{PREFIX}DashboardShares",
        [{"AttributeName": "shareId", "KeyType": "HASH"}],
        [
            {"AttributeName": "shareId", "AttributeType": "S"},
            {"AttributeName": "dashboardId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "N"},
        ],
        [
            {
                "IndexName": "SharesByDashboard",
                "KeySchema": [
                    {"AttributeName": "dashboardId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

    # FilterViews table
    await create_table(
        session,
        f"{PREFIX}FilterViews",
        [{"AttributeName": "filterViewId", "KeyType": "HASH"}],
        [
            {"AttributeName": "filterViewId", "AttributeType": "S"},
            {"AttributeName": "dashboardId", "AttributeType": "S"},
            {"AttributeName": "createdAt", "AttributeType": "N"},
        ],
        [
            {
                "IndexName": "FilterViewsByDashboard",
                "KeySchema": [
                    {"AttributeName": "dashboardId", "KeyType": "HASH"},
                    {"AttributeName": "createdAt", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

    # AuditLogs table
    await create_table(
        session,
        f"{PREFIX}AuditLogs",
        [{"AttributeName": "logId", "KeyType": "HASH"}],
        [
            {"AttributeName": "logId", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "N"},
            {"AttributeName": "targetId", "AttributeType": "S"},
        ],
        [
            {
                "IndexName": "LogsByTimestamp",
                "KeySchema": [
                    {"AttributeName": "timestamp", "KeyType": "HASH"},
                    {"AttributeName": "logId", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "LogsByTarget",
                "KeySchema": [
                    {"AttributeName": "targetId", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    )

    print("\nDynamoDB tables initialization completed!")


if __name__ == "__main__":
    asyncio.run(main())
