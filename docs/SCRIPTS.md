# Scripts Reference

## Frontend Scripts

All frontend scripts are defined in `frontend/package.json` and should be run from the `frontend/` directory using `npm run <script>`.

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `vite` | Start Vite development server with hot module replacement (HMR). Server runs on http://localhost:5173 by default. |
| `build` | `tsc && vite build` | Type-check TypeScript files with `tsc` and build production-optimized bundle with Vite. Output goes to `dist/` directory. |
| `lint` | `eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0` | Lint all TypeScript and TSX files using ESLint. Fails if any warnings are found. |
| `preview` | `vite preview` | Preview production build locally. Requires running `build` first. |
| `test` | `vitest` | Run unit tests with Vitest in watch mode. |
| `test:coverage` | `vitest --coverage` | Run unit tests with code coverage reporting. |
| `test:e2e` | `playwright test` | Run end-to-end tests with Playwright. Requires backend services to be running. |

## Backend Scripts

Backend uses Python with Poetry for dependency management. Scripts should be run from the `backend/` directory.

**重要: このプロジェクトはDockerベースです。バックエンドテストは必ずDocker Composeを使用してください。**

### Using Docker Compose (Required)

```bash
# Run tests
docker compose run --rm api pytest tests/ -v

# Run tests with coverage
docker compose run --rm api pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
docker compose run --rm api pytest tests/test_chatbot.py -v

# Start development server
docker compose up api

# Execute shell in container
docker compose run --rm api bash
```

### Local Development (Not Recommended)

⚠️ **ローカル環境での直接実行は非推奨です。** DynamoDB LocalとMinIOが別途必要になるため、Docker Composeの使用を強く推奨します。

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest tests/ -v

# Run tests with coverage
poetry run pytest tests/ --cov=app --cov-report=html

# Lint code
poetry run ruff check app/

# Type check
poetry run mypy app/
```

## Initialization Scripts

Located in `scripts/` directory. These should be run once during initial setup or when resetting the environment.

| Script | Purpose | Usage |
|--------|---------|-------|
| `init_dynamodb.py` | Initialize DynamoDB tables (Users, Dashboards, Cards, Datasets, etc.) | `docker compose run --rm api python scripts/init_dynamodb.py` |
| `init-dynamodb.sh` | Shell wrapper for `init_dynamodb.py` | `./scripts/init-dynamodb.sh` |
| `init-s3.sh` | Initialize S3 buckets (datasets, static) | `./scripts/init-s3.sh` |

## Docker Compose Commands

Common docker compose commands for development:

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d api

# View logs
docker compose logs -f api

# Stop all services
docker compose down

# Rebuild images
docker compose build

# Rebuild and restart specific service
docker compose up -d --build api

# Remove all containers and volumes
docker compose down -v
```

## Playwright Commands

Additional Playwright commands for E2E testing (run from `frontend/` directory):

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run tests in UI mode (for debugging)
npx playwright test --ui

# Run specific test file
npx playwright test e2e/critical-path.spec.ts

# Run tests in headed mode (see browser)
npx playwright test --headed

# Generate test code
npx playwright codegen http://localhost:5173
```

## Git Workflow

Standard git commands for development workflow:

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Stage changes
git add .

# Commit changes
git commit -m "feat: add your feature description"

# Push to remote
git push origin feature/your-feature-name

# Pull latest changes
git pull origin main

# Rebase onto main
git rebase main
```

## Quick Reference

### Start Development Environment

```bash
# 1. Copy environment file
cp .env.example .env.local

# 2. Edit .env.local (set JWT_SECRET_KEY and VERTEX_AI_PROJECT_ID)

# 3. Start services
docker compose up -d

# 4. Initialize database (first time only)
docker compose run --rm api python scripts/init_dynamodb.py

# 5. Initialize S3 (first time only)
./scripts/init-s3.sh

# 6. Verify services
curl http://localhost:8000/health

# 7. Start frontend dev server
cd frontend && npm run dev
```

### Run Tests

```bash
# Backend tests (in Docker)
docker compose run --rm api pytest tests/ -v

# Frontend unit tests
cd frontend && npm run test

# Frontend E2E tests
cd frontend && npm run test:e2e

# Frontend linting
cd frontend && npm run lint
```

### Build for Production

```bash
# Build backend image
docker build -t bi-api:latest ./backend

# Build executor image
docker build -t bi-executor:latest ./executor

# Build frontend
cd frontend && npm run build

# Build frontend image
docker build -t bi-frontend:latest ./frontend
```
