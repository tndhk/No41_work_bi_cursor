# Contributing

## Overview
This project contains a FastAPI backend, a React frontend, and a Python executor.

## Development Setup
1. Copy environment file.
   - `cp .env.example .env.local`
2. Start services.
   - `docker compose up -d`
3. Check health.
   - `curl http://localhost:8000/health`

## Frontend Scripts

| Script | Command | Purpose |
| --- | --- | --- |
| dev | `vite` | Run Vite dev server |
| build | `tsc && vite build` | Type-check and build |
| lint | `eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0` | Lint frontend |
| preview | `vite preview` | Preview production build |
| test | `vitest` | Run frontend tests |
| test:coverage | `vitest --coverage` | Run tests with coverage |

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENV` | `local` | Runtime environment |
| `API_HOST` | `0.0.0.0` | API bind host |
| `API_PORT` | `8000` | API bind port |
| `API_WORKERS` | `4` | API worker count |
| `API_DEBUG` | `false` | API debug mode |
| `JWT_SECRET_KEY` | (required) | JWT signing key (min 32 chars) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | `1440` | JWT expiry in minutes |
| `PASSWORD_MIN_LENGTH` | `8` | Password minimum length |
| `DYNAMODB_ENDPOINT` | `http://dynamodb-local:8000` | DynamoDB endpoint |
| `DYNAMODB_REGION` | `ap-northeast-1` | DynamoDB region |
| `DYNAMODB_TABLE_PREFIX` | `bi_` | DynamoDB table prefix |
| `S3_ENDPOINT` | `http://minio:9000` | S3 endpoint |
| `S3_REGION` | `ap-northeast-1` | S3 region |
| `S3_BUCKET_DATASETS` | `bi-datasets` | Datasets bucket |
| `S3_BUCKET_STATIC` | `bi-static` | Static bucket |
| `S3_ACCESS_KEY` | `minioadmin` | S3 access key |
| `S3_SECRET_KEY` | `minioadmin` | S3 secret key |
| `VERTEX_AI_PROJECT_ID` | (required) | GCP project id |
| `VERTEX_AI_LOCATION` | `asia-northeast1` | Vertex AI location |
| `VERTEX_AI_MODEL` | `gemini-1.5-pro` | Vertex AI model |
| `EXECUTOR_ENDPOINT` | `http://executor:8080` | Executor endpoint |
| `EXECUTOR_TIMEOUT_CARD` | `10` | Card execution timeout (sec) |
| `EXECUTOR_TIMEOUT_TRANSFORM` | `300` | Transform execution timeout (sec) |
| `EXECUTOR_MAX_CONCURRENT_CARDS` | `10` | Card concurrency limit |
| `EXECUTOR_MAX_CONCURRENT_TRANSFORMS` | `5` | Transform concurrency limit |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_FORMAT` | `json` | Log format |

## Testing
Backend:
- `docker compose run --rm api pytest tests/ -v`

Frontend:
- `npm run test`
- `npm run test:coverage`

