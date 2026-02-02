# Data Models and Schemas

**Last Updated:** 2026-02-02

## Entity Relationship Diagram

```
User
├── owns: Dataset[]
├── owns: Transform[]
├── owns: Card[]
├── owns: Dashboard[]
├── owns: FilterView[]
└── memberOf: Group[]

Group
└── members: User[]

Dataset
├── owner: User
└── source: Local CSV | S3 CSV | Transform

Transform
├── owner: User
├── inputs: Dataset[]
└── output: Dataset

Card
├── owner: User
└── dataset: Dataset

Dashboard
├── owner: User
├── cards: Card[]
├── filters: Filter[]
├── filterViews: FilterView[]
└── shares: Share[] (User | Group)

FilterView
├── owner: User
├── dashboard: Dashboard
└── filterState: FilterState
```

## Core Models

### User
```python
class User(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    created_at: datetime
    updated_at: datetime

class UserInDB(User):
    password_hash: str

class UserResponse(User):
    groups: list[dict] = []
```

### Group
```python
class Group(BaseModel):
    group_id: str
    name: str
    created_at: datetime
    updated_at: datetime

class GroupDetail(Group):
    members: list[User]
```

### Dataset
```python
class ColumnSchema(BaseModel):
    name: str
    dtype: str  # int64, float64, string, date, datetime, bool
    nullable: bool

class Dataset(BaseModel):
    dataset_id: str
    name: str
    owner_id: str
    source_type: str  # "local_csv" | "s3_csv" | "transform"
    source_config: dict
    schema: list[ColumnSchema]
    row_count: int
    column_count: int
    s3_path: str
    partition_column: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_import_at: Optional[datetime]
    last_import_by: Optional[str]
```

### Card
```python
class Card(BaseModel):
    card_id: str
    name: str
    owner_id: str
    dataset_id: str
    code: str  # Python code
    params: dict
    used_columns: list[str]
    filter_applicable: list[str]
    created_at: datetime
    updated_at: datetime
```

### Dashboard
```python
class DashboardCard(BaseModel):
    card_id: str
    x: int
    y: int
    w: int
    h: int

class Filter(BaseModel):
    id: str
    type: str  # "category" | "date_range"
    column: str
    label: str
    multi_select: bool = False

class Dashboard(BaseModel):
    dashboard_id: str
    name: str
    owner_id: str
    layout: dict  # Grid layout config
    filters: list[Filter]
    default_filter_view_id: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### Transform
```python
class Transform(BaseModel):
    transform_id: str
    name: str
    owner_id: str
    input_dataset_ids: list[str]
    output_dataset_id: Optional[str]
    code: str  # Python code
    params: dict
    schedule: Optional[str]  # cron format
    created_at: datetime
    updated_at: datetime
```

### FilterView
```python
class FilterView(BaseModel):
    filter_view_id: str
    dashboard_id: str
    name: str
    owner_id: str
    filter_state: dict  # Filter values
    is_shared: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
```

### DashboardShare
```python
class DashboardShare(BaseModel):
    share_id: str
    dashboard_id: str
    shared_to_type: str  # "user" | "group"
    shared_to_id: str
    permission: str  # "owner" | "editor" | "viewer"
    shared_by: str
    created_at: datetime
```

## DynamoDB Schema

### Table: bi_users
- **PK:** `userId` (String)
- **Attributes:** email, name, passwordHash, createdAt, updatedAt

### Table: bi_groups
- **PK:** `groupId` (String)
- **GSI:** GroupMembers (groupId, userId)
- **Attributes:** name, createdAt, updatedAt

### Table: bi_datasets
- **PK:** `datasetId` (String)
- **GSI:** DatasetsByOwner (ownerId, createdAt)
- **Attributes:** name, ownerId, sourceType, sourceConfig, schema, rowCount, columnCount, s3Path, partitionColumn, createdAt, updatedAt, lastImportAt, lastImportBy

### Table: bi_cards
- **PK:** `cardId` (String)
- **GSI:** CardsByOwner (ownerId, createdAt)
- **Attributes:** name, ownerId, datasetId, code, params, usedColumns, filterApplicable, createdAt, updatedAt

### Table: bi_dashboards
- **PK:** `dashboardId` (String)
- **GSI:** DashboardsByOwner (ownerId, createdAt)
- **GSI:** DashboardsBySharedUser (sharedUserId, dashboardId)
- **GSI:** DashboardsBySharedGroup (sharedGroupId, dashboardId)
- **Attributes:** name, ownerId, layout, filters, defaultFilterViewId, createdAt, updatedAt

### Table: bi_dashboard_shares
- **PK:** `shareId` (String)
- **GSI:** SharesByDashboard (dashboardId, createdAt)
- **Attributes:** dashboardId, sharedToType, sharedToId, permission, sharedBy, createdAt

### Table: bi_filter_views
- **PK:** `filterViewId` (String)
- **GSI:** FilterViewsByDashboard (dashboardId, createdAt)
- **Attributes:** dashboardId, name, ownerId, filterState, isShared, isDefault, createdAt, updatedAt

### Table: bi_transforms
- **PK:** `transformId` (String)
- **GSI:** TransformsByOwner (ownerId, createdAt)
- **Attributes:** name, ownerId, inputDatasetIds, outputDatasetId, code, params, schedule, createdAt, updatedAt

## S3 Storage Schema

### Bucket: bi-datasets
```
datasets/
  {datasetId}/
    data.parquet                    # Non-partitioned
    partitions/                     # Partitioned by date
      {date}/
        part-*.parquet
```

### Bucket: bi-static
```
index.html
assets/
  {hash}.js
  {hash}.css
```

## Data Types

### Column Types (Dataset Schema)
- `int64` - Integer
- `float64` - Floating point
- `string` - Text
- `date` - Date (YYYY-MM-DD)
- `datetime` - Timestamp
- `bool` - Boolean

### Filter Types
- `category` - Single or multi-select from distinct values
- `date_range` - Date range picker (start, end)

### Permission Types
- `owner` - Full control (edit, share, delete)
- `editor` - Can edit dashboard (layout, filters)
- `viewer` - Read-only access

## Data Flow

### Dataset Import
1. CSV uploaded/selected
2. Parse CSV → DataFrame
3. Infer column types
4. Convert to Parquet
5. Upload to S3
6. Save metadata to DynamoDB

### Card Execution
1. Dashboard filter values
2. Load Dataset from S3 (with partition pruning)
3. Apply filters
4. Send to Executor with card code
5. Executor returns HTML
6. Render in iframe

### Transform Execution
1. Load input Datasets from S3
2. Execute Python code
3. Generate output DataFrame
4. Convert to Parquet
5. Upload to S3
6. Save output Dataset metadata to DynamoDB
