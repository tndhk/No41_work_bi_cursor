# Contributing

## Overview

This project contains a FastAPI backend, a React frontend, and a Python executor service.

## Development Setup

### Prerequisites

- Docker 24.x and docker-compose 2.x
- Node.js 20.x (for frontend local development only)
- Python 3.11 (for backend local development only)

**推奨開発環境**: このプロジェクトでは**Docker Composeを使用した開発・テストを標準**としています。ローカルでのPython/Node.js実行も可能ですが、環境構築が必要です。Docker Composeを使用することで依存サービス（DynamoDB Local、MinIO等）が自動的に起動し、環境差異によるトラブルを回避できます。

### Initial Setup

1. **Copy environment file**
   ```bash
   cp .env.example .env.local
   ```

2. **Edit `.env.local`**
   - Set `JWT_SECRET_KEY` to a secure random string (minimum 32 characters)
   - Set `VERTEX_AI_PROJECT_ID` to your GCP project ID (if using Chatbot feature)

3. **Start services**
   ```bash
   docker compose up -d
   ```

4. **Verify services are running**
   ```bash
   curl http://localhost:8000/health
   ```

5. **Initialize DynamoDB tables** (first time only)
   ```bash
   docker compose run --rm api python scripts/init_tables.py
   ```

6. **Initialize S3 buckets** (first time only)
   ```bash
   docker compose run --rm api python scripts/init_s3.py
   ```

## Frontend Scripts

All scripts are run from the `frontend/` directory:

| Script | Command | Purpose |
| --- | --- | --- |
| `dev` | `vite` | Run Vite development server with hot reload (http://localhost:5173) |
| `build` | `tsc && vite build` | Type-check TypeScript and build for production |
| `lint` | `eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0` | Lint frontend code with ESLint |
| `preview` | `vite preview` | Preview production build locally |
| `test` | `vitest` | Run frontend unit tests with Vitest |
| `test:coverage` | `vitest --coverage` | Run tests with coverage report |
| `test:e2e` | `playwright test` | Run end-to-end tests with Playwright |

### Frontend Development

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (http://localhost:5173)
npm run lint         # Check code quality
npm run test         # Run tests
```

## Backend Scripts

Backend uses Python with Poetry for dependency management.

### Recommended: Docker Compose Development

```bash
# サービス起動
docker compose up -d

# テスト実行
docker compose run --rm api pytest tests/ -v

# コンテナ内でシェルを開く
docker compose run --rm api bash
```

### Local Development (Optional)

ローカル環境で直接実行する場合（環境構築が必要）:

```bash
cd backend

# Install dependencies
poetry install

# Run development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest tests/ -v

# Run tests with coverage
poetry run pytest tests/ --cov=app --cov-report=html
```

## Environment Variables

All environment variables are defined in `.env.example`. Copy to `.env.local` and customize:

| Variable | Default | Purpose | Required |
| --- | --- | --- | --- |
| `ENV` | `local` | Runtime environment (`local`, `staging`, `production`) | Yes |
| `API_HOST` | `0.0.0.0` | API bind host | No |
| `API_PORT` | `8000` | API bind port | No |
| `API_WORKERS` | `4` | Number of API worker processes | No |
| `API_DEBUG` | `false` | Enable debug mode | No |
| `JWT_SECRET_KEY` | (none) | JWT signing key (minimum 32 characters) | Yes |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm | No |
| `JWT_EXPIRE_MINUTES` | `1440` | JWT token expiry in minutes (24 hours) | No |
| `PASSWORD_MIN_LENGTH` | `8` | Minimum password length | No |
| `DYNAMODB_ENDPOINT` | `http://dynamodb-local:8000` | DynamoDB endpoint (local only) | No |
| `DYNAMODB_REGION` | `ap-northeast-1` | AWS region for DynamoDB | No |
| `DYNAMODB_TABLE_PREFIX` | `bi_` | Prefix for DynamoDB table names | No |
| `S3_ENDPOINT` | `http://minio:9000` | S3 endpoint (local only) | No |
| `S3_REGION` | `ap-northeast-1` | AWS region for S3 | No |
| `S3_BUCKET_DATASETS` | `bi-datasets` | S3 bucket name for datasets | No |
| `S3_BUCKET_STATIC` | `bi-static` | S3 bucket name for static assets | No |
| `S3_ACCESS_KEY` | `minioadmin` | S3 access key (local only) | No |
| `S3_SECRET_KEY` | `minioadmin` | S3 secret key (local only) | No |
| `VERTEX_AI_PROJECT_ID` | (none) | GCP project ID for Vertex AI | Yes (if using Chatbot) |
| `VERTEX_AI_LOCATION` | `asia-northeast1` | Vertex AI region | No |
| `VERTEX_AI_MODEL` | `gemini-1.5-pro` | Vertex AI model name | No |
| `EXECUTOR_ENDPOINT` | `http://executor:8080` | Executor service endpoint | No |
| `EXECUTOR_TIMEOUT_CARD` | `10` | Card execution timeout in seconds | No |
| `EXECUTOR_TIMEOUT_TRANSFORM` | `300` | Transform execution timeout in seconds | No |
| `EXECUTOR_MAX_CONCURRENT_CARDS` | `10` | Maximum concurrent card executions | No |
| `EXECUTOR_MAX_CONCURRENT_TRANSFORMS` | `5` | Maximum concurrent transform executions | No |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARN`, `ERROR`) | No |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`) | No |
| `REDIS_URL` | (none) | Redis URL for caching (e.g., `redis://localhost:6379/0`). If not set, in-memory cache is used | No |
| `CACHE_TTL_SECONDS` | `3600` | Cache TTL in seconds (default: 1 hour) | No |
| `ALLOW_TEST_SETUP` | `false` | Enable test setup endpoint (for E2E tests only) | No |

## Testing

### Backend Tests

**重要: このプロジェクトはDocker Composeでのテスト実行が必須です**

このプロジェクトは**Dockerベースのプロジェクト**です。テストは必ず**Docker Composeを使用して実行**してください。

**理由:**
- DynamoDB LocalとMinIOが必須の依存サービス
- ローカル環境では依存サービスが起動していないためエラーになる
- PEP 668によりシステムPythonへの直接インストールが制限されている
- Docker Composeを使用すれば全ての依存サービスが自動的に起動し、環境の一貫性が保たれる

**⚠️ ローカルで`pytest`を直接実行しないでください。必ずDocker Composeを使用してください。**

```bash
# 全テスト実行
docker compose run --rm api pytest tests/ -v

# 特定のテストファイルを実行
docker compose run --rm api pytest tests/test_users.py -v

# カバレッジ付きで実行
docker compose run --rm api pytest tests/ --cov=app --cov-report=term-missing

# パターンマッチでテスト実行
docker compose run --rm api pytest tests/ -k "test_user" -v
```

**ローカルでの実行（非推奨）**

⚠️ **ローカル環境での直接実行は推奨しません。** 依存サービス（DynamoDB Local、MinIO）を別途起動し、環境変数を正しく設定する必要があるため、Docker Composeの使用を強く推奨します。

どうしてもローカルで実行する場合:

```bash
# 依存サービスを起動（別ターミナルで）
docker compose up -d dynamodb-local minio

cd backend
poetry install
# 環境変数を設定してから実行
poetry run pytest tests/ -v
```

### Frontend Tests

Run frontend unit tests:

```bash
cd frontend

# Run tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test -- --watch
```

### E2E Tests

Run end-to-end tests with Playwright:

```bash
cd frontend

# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run in UI mode for debugging
npx playwright test --ui

# Run specific test file
npx playwright test e2e/critical-path.spec.ts
```

**Prerequisites for E2E tests:**
- Backend and frontend services must be running
- Test setup endpoint must be enabled (set `ALLOW_TEST_SETUP=true` in backend)
- Playwright browsers installed (`npx playwright install`)

**Local E2E test setup:**

```bash
# Start all services
docker compose up -d

# Wait for services to be ready
curl http://localhost:8000/health

# Run E2E tests
cd frontend && npm run test:e2e
```

### Test Coverage Requirements

- Backend: Target 80% code coverage
- Frontend: Target 80% code coverage
- Critical paths (authentication, data access) should have 100% coverage
- E2E tests should cover critical user flows (login, dashboard viewing, filtering)

## Code Quality

### Linting

**Frontend:**
```bash
cd frontend
npm run lint
```

**Backend:**
```bash
cd backend
poetry run ruff check app/
poetry run mypy app/
```

### Type Checking

**Frontend:**
```bash
cd frontend
npm run build  # Includes TypeScript type checking
```

**Backend:**
```bash
cd backend
poetry run mypy app/
```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Write code following project conventions
   - Add tests for new functionality
   - Update documentation if needed

3. **Run tests and linting**
   
   ```bash
   # Backend（必ずDocker Composeを使用）
   docker compose run --rm api pytest tests/ -v
   
   # テスト後はDockerを停止
   docker compose down
   
   # Frontend
   cd frontend && npm run lint && npm run test
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Project Structure

```
work_BI/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   │   └── routes/   # Route handlers (auth, cards, dashboards, datasets, chatbot, etc.)
│   │   ├── core/         # Core utilities (config, security, logging, middleware)
│   │   ├── db/           # Database clients (DynamoDB, S3)
│   │   ├── models/       # Pydantic models
│   │   └── services/     # Business logic
│   └── tests/            # Backend tests (pytest)
├── executor/             # Python execution service
│   ├── app/              # Sandboxed code execution
│   └── tests/            # Executor tests
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   │   ├── card/     # Card components
│   │   │   ├── chatbot/  # Chatbot UI (NEW)
│   │   │   ├── common/   # Shared components
│   │   │   ├── dashboard/ # Dashboard viewer and editor
│   │   │   ├── dataset/  # Dataset management
│   │   │   └── transform/ # Transform components
│   │   ├── pages/        # Page components
│   │   └── stores/       # Zustand stores (auth state)
│   ├── e2e/              # Playwright E2E tests
│   └── tests/            # Unit tests
├── docs/                 # Documentation
│   ├── plans/            # Implementation plans and decisions
│   └── codemaps/         # Architecture documentation
└── scripts/              # Initialization scripts (DynamoDB, S3)
```

## Features

### Chatbot (NEW)

The Chatbot feature allows users to ask questions about dashboard data using natural language. It leverages Google Cloud Vertex AI (Gemini) to generate insights based on dataset summaries.

**Architecture:**
- Backend: `backend/app/services/chatbot_service.py` - Vertex AI integration, dataset summarization, rate limiting
- Frontend: `frontend/src/components/chatbot/ChatbotPanel.tsx` - Chat UI with conversation history
- Rate limiting: 10 requests per minute per user (DynamoDB-based sliding window)

**Configuration:**
- Requires `VERTEX_AI_PROJECT_ID` in `.env.local` (see Environment Variables section)
- Optional: `VERTEX_AI_LOCATION` (default: `asia-northeast1`)
- Optional: `VERTEX_AI_MODEL` (default: `gemini-1.5-pro`)

**How it works:**
1. User opens chat panel from dashboard view
2. User asks a question about the data
3. Backend generates summaries of referenced datasets (schema, samples, statistics)
4. Prompt is sent to Vertex AI with dataset context
5. AI response is returned and displayed in chat UI

**Rate limiting:**
- Implemented with DynamoDB TTL-based sliding window
- Default: 10 requests per 60 seconds per user
- Returns HTTP 429 when limit exceeded

### Card Execution Caching

Card preview results are cached to improve performance and reduce executor load. Cache keys are based on card ID and filter values.

**Architecture:**
- Backend: `backend/app/services/cache_service.py` - Cache abstraction with Redis and in-memory backends
- Cache key format: `card_preview:{card_id}:{filters_hash}`
- TTL: Configurable (default: 1 hour)

**Configuration:**
- `REDIS_URL`: Redis connection URL (optional). If not set, in-memory cache is used (development mode)
- `CACHE_TTL_SECONDS`: Cache TTL in seconds (default: 3600)

**How it works:**
1. When a card preview is requested, cache is checked first
2. If cache hit, cached HTML is returned immediately
3. If cache miss, executor runs the card code and result is cached
4. Cache is invalidated when card is updated or deleted

**Cache backends:**
- **Redis**: Production-ready, shared across instances
- **In-memory**: Development mode, per-instance cache

## Common Development Tasks

### Adding a New API Endpoint

1. Create model in `backend/app/models/`
2. Add service function in `backend/app/services/`
3. Add route in `backend/app/api/routes/`
4. Write tests in `backend/tests/` (use moto for AWS mocking)
5. Update API documentation in `docs/api-spec.md`

### Adding a New Frontend Component

1. Create component in `frontend/src/components/`
2. Add tests in `frontend/src/components/__tests__/` (use Vitest + Testing Library)
3. Add TypeScript interfaces for props
4. Add to appropriate page
5. Update E2E tests if critical user path

### Database Schema Changes

1. Update model definitions in `backend/app/models/`
2. Update initialization scripts in `scripts/` if adding new tables or GSIs
   - `scripts/init_tables.py` - Local development tables
   - `backend/tests/conftest.py` - Test table definitions
3. Update tests with new schema
4. Update service code to use new GSIs (replace scans with queries)
5. Update documentation in `docs/design.md`

**Adding Global Secondary Indexes (GSIs):**

When adding GSIs for query optimization:

1. Add GSI definition to `scripts/init_tables.py`:
   ```python
   "GlobalSecondaryIndexes": [
       {
           "IndexName": "YourIndexName",
           "KeySchema": [
               {"AttributeName": "hashKey", "KeyType": "HASH"},
               {"AttributeName": "rangeKey", "KeyType": "RANGE"},  # Optional
           ],
           "Projection": {"ProjectionType": "ALL"},
       }
   ]
   ```

2. Add same GSI to `backend/tests/conftest.py` table definitions

3. Update service code to use query instead of scan:
   ```python
   response = await client.query(
       TableName=TABLE_NAME,
       IndexName="YourIndexName",
       KeyConditionExpression="hashKey = :hashKey",
       ExpressionAttributeValues={":hashKey": {"S": value}},
   )
   ```

4. Update production infrastructure (Terraform/CloudFormation) separately

## Getting Help

- Check existing documentation in `docs/`
- Review test files for usage examples
- Check API specification in `docs/api-spec.md`
- Review design documents in `docs/design.md`
