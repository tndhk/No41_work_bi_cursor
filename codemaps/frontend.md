# Frontend Architecture

**Last Updated:** 2026-02-02

## Directory Structure

```
frontend/src/
├── main.tsx              # Entry point
├── App.tsx               # Root component + routing
├── index.css             # Global styles
├── setupTests.ts         # Test configuration
├── components/
│   ├── common/           # Shared components
│   │   ├── Layout.tsx
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── ProtectedRoute.tsx
│   ├── dashboard/        # Dashboard components
│   │   ├── DashboardViewer.tsx
│   │   ├── DashboardEditor.tsx
│   │   ├── CardContainer.tsx
│   │   ├── FilterBar.tsx
│   │   └── layout.ts     # Layout utilities
│   ├── dataset/          # Dataset components
│   │   ├── DatasetList.tsx
│   │   ├── DatasetImport.tsx
│   │   └── DatasetPreview.tsx
│   ├── card/             # Card components
│   │   ├── CardList.tsx
│   │   ├── CardEditor.tsx
│   │   └── CardPreview.tsx
│   └── transform/        # Transform components
│       ├── TransformList.tsx
│       └── TransformEditor.tsx
├── pages/                # Page components
│   ├── LoginPage.tsx
│   ├── DashboardListPage.tsx
│   ├── DashboardViewPage.tsx
│   ├── DashboardEditPage.tsx
│   ├── DatasetListPage.tsx
│   ├── DatasetDetailPage.tsx
│   ├── CardListPage.tsx
│   └── TransformListPage.tsx
└── stores/               # Zustand stores
    └── auth.ts           # Authentication state
```

## Component Hierarchy

```
App
├── QueryClientProvider
└── BrowserRouter
    ├── Route: /login → LoginPage
    └── Route: / → ProtectedRoute
        └── Layout
            ├── Header
            ├── Sidebar
            └── Outlet
                ├── DashboardListPage
                ├── DashboardViewPage
                │   └── DashboardViewer
                │       ├── FilterBar
                │       └── CardContainer[]
                ├── DashboardEditPage
                │   └── DashboardEditor
                ├── DatasetListPage
                │   └── DatasetList
                ├── DatasetDetailPage
                │   └── DatasetPreview
                ├── CardListPage
                │   ├── CardList
                │   └── CardEditor
                └── TransformListPage
                    ├── TransformList
                    └── TransformEditor
```

## Routing

**Public Routes:**
- `/login` - Login page

**Protected Routes (require authentication):**
- `/` - Redirects to `/dashboards`
- `/dashboards` - Dashboard list
- `/dashboards/:id` - Dashboard view
- `/dashboards/:id/edit` - Dashboard edit
- `/datasets` - Dataset list
- `/datasets/:id` - Dataset detail
- `/cards` - Card list
- `/transforms` - Transform list

## State Management

### Server State (TanStack Query)
- API data caching
- Automatic refetching
- Optimistic updates
- Query invalidation

**Query Keys:**
- `['dashboards']` - Dashboard list
- `['dashboard', id]` - Dashboard detail
- `['datasets']` - Dataset list
- `['dataset', id]` - Dataset detail
- `['cards']` - Card list
- `['transforms']` - Transform list

### Client State (Zustand)
- `auth` store - Authentication state (token, user)

## API Integration

API clients are organized by domain:
- `lib/api.ts` - Base API client + auth
- `lib/dashboards.ts` - Dashboard API
- `lib/datasets.ts` - Dataset API
- `lib/cards.ts` - Card API
- `lib/transforms.ts` - Transform API

All API calls use TanStack Query hooks:
- `useQuery` - GET requests
- `useMutation` - POST/PUT/DELETE requests

## Key Components

### Layout Components
- **Layout** - Main app layout with header/sidebar
- **Header** - Top navigation bar
- **Sidebar** - Left navigation menu
- **ProtectedRoute** - Route guard for authentication

### Dashboard Components
- **DashboardViewer** - Read-only dashboard display
- **DashboardEditor** - Editable dashboard with drag-drop
- **CardContainer** - iframe wrapper for card HTML
- **FilterBar** - Filter controls (category, date range)

### Data Management Components
- **DatasetList** - Dataset table with pagination
- **DatasetImport** - CSV upload form
- **DatasetPreview** - Data preview table
- **CardList** - Card table with actions
- **CardEditor** - Monaco editor for card code
- **TransformList** - Transform table
- **TransformEditor** - Monaco editor for transform code

## Dependencies

**Core:**
- `react` - UI framework
- `react-dom` - DOM rendering
- `react-router-dom` - Routing

**State:**
- `@tanstack/react-query` - Server state
- `zustand` - Client state

**Forms:**
- `react-hook-form` - Form handling
- `zod` - Schema validation
- `@hookform/resolvers` - Zod integration

**UI:**
- `tailwindcss` - Utility-first CSS
- `react-grid-layout` - Dashboard grid
- `monaco-editor` - Code editor

**Utilities:**
- `date-fns` - Date manipulation
- `ky` - HTTP client
- `dompurify` - HTML sanitization

**Build:**
- `vite` - Build tool
- `typescript` - Type checking
- `vitest` - Testing

## Build Output

Production build outputs to `frontend/dist/`:
- `index.html` - Entry HTML
- `assets/` - JS/CSS bundles
- Static assets

Deployed to S3 and served via CloudFront.
