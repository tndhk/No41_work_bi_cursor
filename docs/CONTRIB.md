# Contributing

## Overview

This project contains a FastAPI backend, a React frontend, and a Python executor service.

## Development Setup

### Prerequisites

- Docker 24.x and docker-compose 2.x
- Node.js 20.x (for frontend development)
- Python 3.11 (for backend development)

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
   docker compose run --rm api python scripts/init_dynamodb.py
   ```

6. **Initialize S3 buckets** (first time only)
   ```bash
   docker compose run --rm api python scripts/init_s3.py
   ```

## Frontend Scripts

All scripts are run from the `frontend/` directory:

| Script | Command | Purpose |
| --- | --- | --- |
| `dev` | `vite` | Run Vite development server with hot reload |
| `build` | `tsc && vite build` | Type-check TypeScript and build for production |
| `lint` | `eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0` | Lint frontend code with ESLint |
| `preview` | `vite preview` | Preview production build locally |
| `test` | `vitest` | Run frontend unit tests |
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

Backend uses Python with Poetry for dependency management. Common commands:

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

### Backend Development

```bash
cd backend
poetry install       # Install dependencies
poetry run pytest tests/ -v  # Run tests
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

## Testing

### Backend Tests

Run backend tests using Docker Compose:

```bash
# Run all tests
docker compose run --rm api pytest tests/ -v

# Run specific test file
docker compose run --rm api pytest tests/test_users.py -v

# Run with coverage
docker compose run --rm api pytest tests/ --cov=app --cov-report=term-missing

# Run tests matching a pattern
docker compose run --rm api pytest tests/ -k "test_user" -v
```

Or run locally with Poetry:

```bash
cd backend
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
   # Backend
   docker compose run --rm api pytest tests/ -v
   
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
│   │   ├── core/         # Core utilities (config, security)
│   │   ├── db/           # Database clients (DynamoDB, S3)
│   │   ├── models/       # Pydantic models
│   │   └── services/     # Business logic
│   └── tests/            # Backend tests
├── executor/             # Python execution service
│   ├── app/
│   └── tests/
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/        # Page components
│   │   └── stores/       # Zustand stores
│   └── tests/
└── docs/                 # Documentation
```

## Common Development Tasks

### Adding a New API Endpoint

1. Create model in `backend/app/models/`
2. Add service function in `backend/app/services/`
3. Add route in `backend/app/api/routes/`
4. Write tests in `backend/tests/`
5. Update API documentation in `docs/api-spec.md`

### Adding a New Frontend Component

1. Create component in `frontend/src/components/`
2. Add tests in `frontend/src/components/__tests__/`
3. Update storybook (if applicable)
4. Add to appropriate page

### Database Schema Changes

1. Update model definitions in `backend/app/models/`
2. Create migration script (if needed)
3. Update tests
4. Update documentation

## Getting Help

- Check existing documentation in `docs/`
- Review test files for usage examples
- Check API specification in `docs/api-spec.md`
- Review design documents in `docs/design.md`
