# Backend Architecture

**Last Updated:** 2026-02-02

## Directory Structure

```
backend/app/
├── main.py                 # FastAPI app entry point
├── api/
│   ├── deps.py            # Dependency injection (auth)
│   └── routes/            # API route handlers
│       ├── auth.py        # Authentication endpoints
│       ├── users.py       # User management
│       ├── groups.py      # Group management
│       ├── datasets.py    # Dataset CRUD + import
│       ├── cards.py       # Card CRUD + preview
│       ├── dashboards.py  # Dashboard CRUD
│       ├── dashboard_shares.py  # Dashboard sharing
│       ├── filter_views.py      # Filter view management
│       ├── transforms.py        # Transform CRUD + execution
│       ├── chatbot.py          # Chatbot API
│       └── test_setup.py       # Test-only setup endpoint (guarded)
├── core/
│   ├── config.py          # Settings (Pydantic Settings)
│   ├── security.py        # JWT, password hashing
│   ├── exceptions.py      # Custom exceptions
│   ├── logging.py         # Logging setup
│   └── middleware.py      # Request ID middleware
├── db/
│   ├── dynamodb.py        # DynamoDB client
│   └── s3.py              # S3 client
├── models/                # Pydantic models
│   ├── user.py
│   ├── group.py
│   ├── dataset.py
│   ├── card.py
│   ├── dashboard.py
│   ├── transform.py
│   └── filter_view.py
└── services/              # Business logic
    ├── user_service.py
    ├── group_service.py
    ├── dataset_service.py
    ├── card_service.py
    ├── dashboard_service.py
    ├── dashboard_share_service.py
    ├── filter_view_service.py
    └── transform_service.py
```

## API Routes

### Authentication (`/api/auth`)
- `POST /login` - User login
- `GET /me` - Current user info

### Users (`/api/users`)
- `GET /users` - List users
- `GET /users/{id}` - Get user

### Groups (`/api/groups`)
- `GET /groups` - List groups
- `POST /groups` - Create group
- `GET /groups/{id}` - Get group
- `PUT /groups/{id}` - Update group
- `DELETE /groups/{id}` - Delete group
- `POST /groups/{id}/members` - Add member
- `DELETE /groups/{id}/members/{userId}` - Remove member

### Datasets (`/api/datasets`)
- `GET /datasets` - List datasets
- `POST /datasets` - Create (Local CSV import)
- `POST /datasets/s3-import` - S3 CSV import
- `GET /datasets/{id}` - Get dataset
- `PUT /datasets/{id}` - Update dataset
- `DELETE /datasets/{id}` - Delete dataset
- `POST /datasets/{id}/import` - Reimport
- `GET /datasets/{id}/preview` - Preview data

### Cards (`/api/cards`)
- `GET /cards` - List cards
- `POST /cards` - Create card
- `GET /cards/{id}` - Get card
- `PUT /cards/{id}` - Update card
- `DELETE /cards/{id}` - Delete card
- `POST /cards/{id}/preview` - Preview execution

### Dashboards (`/api/dashboards`)
- `GET /dashboards` - List dashboards
- `POST /dashboards` - Create dashboard
- `GET /dashboards/{id}` - Get dashboard
- `PUT /dashboards/{id}` - Update dashboard
- `DELETE /dashboards/{id}` - Delete dashboard
- `POST /dashboards/{id}/clone` - Clone dashboard

### Dashboard Shares (`/api/dashboards/{id}/shares`)
- `GET /shares` - List shares
- `POST /shares` - Add share
- `PUT /shares/{shareId}` - Update share
- `DELETE /shares/{shareId}` - Remove share

### Filter Views (`/api/dashboards/{id}/filter-views`)
- `GET /filter-views` - List filter views
- `POST /filter-views` - Create filter view
- `GET /filter-views/{id}` - Get filter view
- `PUT /filter-views/{id}` - Update filter view
- `DELETE /filter-views/{id}` - Delete filter view

### Transforms (`/api/transforms`)
- `GET /transforms` - List transforms
- `POST /transforms` - Create transform
- `GET /transforms/{id}` - Get transform
- `PUT /transforms/{id}` - Update transform
- `DELETE /transforms/{id}` - Delete transform
- `POST /transforms/{id}/execute` - Execute transform
- `GET /transforms/{id}/executions` - Execution history

### Chatbot (`/api/dashboards/{id}/chat`)
- `POST /chat` - Chatbot query

### Test Setup (`/api/test` - Test Only)
- `POST /setup` - Create test data (user, dataset, card, dashboard)
- **Note:** Only enabled when `ALLOW_TEST_SETUP=true`

## Service Layer

Services contain business logic and coordinate between:
- Database operations (DynamoDB)
- Storage operations (S3)
- External services (Executor, Vertex AI)

### Key Services

**user_service.py**
- User CRUD operations
- Password management

**dataset_service.py**
- CSV parsing and import
- Parquet conversion
- S3 storage management
- Schema inference

**card_service.py**
- Card CRUD
- Card execution orchestration (calls Executor)

**dashboard_service.py**
- Dashboard CRUD
- Layout management
- Filter configuration

**transform_service.py**
- Transform CRUD
- Execution orchestration (calls Executor)
- Schedule management

## Database Layer

### DynamoDB Tables
- `bi_users` - User accounts
- `bi_groups` - Groups
- `bi_datasets` - Dataset metadata
- `bi_cards` - Card definitions
- `bi_dashboards` - Dashboard definitions
- `bi_dashboard_shares` - Sharing permissions
- `bi_filter_views` - Saved filter states
- `bi_transforms` - Transform definitions

### S3 Buckets
- `bi-datasets` - Parquet files (partitioned by date)
- `bi-static` - Static assets (frontend build)

## Dependencies

**Core:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `pydantic-settings` - Configuration

**AWS:**
- `aioboto3` - Async AWS SDK

**Security:**
- `python-jose` - JWT
- `passlib[bcrypt]` - Password hashing

**Data:**
- `pandas` - Data processing
- `pyarrow` - Parquet I/O

**AI:**
- `google-cloud-aiplatform` - Vertex AI

**Logging:**
- `structlog` - Structured logging
