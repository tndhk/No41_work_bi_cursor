# Architecture Overview

**Last Updated:** 2026-02-02

## System Architecture

```
┌─────────────┐
│   Browser   │
│  (React)    │
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────────────────────────────┐
│         API Gateway / ALB          │
└──────┬─────────────────────────────┘
       │
       ├─────────────────┐
       ▼                 ▼
┌─────────────┐  ┌──────────────┐
│   FastAPI   │  │   Executor  │
│   Service   │  │   Service   │
└──────┬──────┘  └──────┬──────┘
       │                 │
       ├────────┬────────┤
       ▼        ▼        ▼
┌──────────┐ ┌──────┐ ┌──────┐
│DynamoDB  │ │  S3  │ │Vertex│
│          │ │      │ │  AI  │
└──────────┘ └──────┘ └──────┘
```

## Component Overview

### Frontend (React + TypeScript)
- **Framework:** React 18, TypeScript 5
- **Routing:** React Router v6
- **State Management:** 
  - TanStack Query (server state)
  - Zustand (client state)
- **Build Tool:** Vite 5
- **UI:** Tailwind CSS + shadcn/ui components

### Backend API (FastAPI)
- **Framework:** FastAPI 0.109
- **Language:** Python 3.11
- **ASGI Server:** Uvicorn
- **Validation:** Pydantic v2
- **Database:** DynamoDB (via aioboto3)
- **Storage:** S3 (via aioboto3)

### Executor Service (Python)
- **Framework:** FastAPI
- **Purpose:** Sandboxed Python code execution
- **Features:**
  - Card execution (HTML generation)
  - Transform execution (ETL)
  - Resource limiting
  - Queue management

### External Services
- **DynamoDB:** Metadata storage (Users, Datasets, Cards, Dashboards, etc.)
- **S3:** Dataset storage (Parquet format), static assets
- **Vertex AI:** Chatbot functionality (Gemini)

## Data Flow

### Dataset Import Flow
```
CSV (Local/S3) → API → Parse → Convert to Parquet → S3 → DynamoDB Metadata
```

### Card Execution Flow
```
Dashboard View → Filter Change → API → Filter Apply → Executor → HTML → iframe
```

### Transform Execution Flow
```
Transform Definition → Execute → Executor → Read Input → Process → Write Output → S3 + DynamoDB
```

## Key Dependencies

### Backend Dependencies
- `fastapi` - Web framework
- `pydantic` - Data validation
- `aioboto3` - AWS SDK (async)
- `python-jose` - JWT handling
- `passlib` - Password hashing
- `structlog` - Structured logging
- `pyarrow` - Parquet I/O
- `pandas` - Data processing

### Frontend Dependencies
- `react` - UI framework
- `react-router-dom` - Routing
- `@tanstack/react-query` - Server state
- `zustand` - Client state
- `react-hook-form` - Form handling
- `zod` - Schema validation
- `monaco-editor` - Code editor
- `react-grid-layout` - Dashboard layout

## Security Architecture

- **Authentication:** JWT tokens
- **Authorization:** Dashboard-level permissions (Owner/Editor/Viewer)
- **Code Execution:** Sandboxed containers with network isolation
- **HTML Rendering:** iframe with CSP
- **Data Access:** Owner-based + Dashboard sharing
