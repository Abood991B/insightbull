# Project Structure Documentation

## Overview

This is a full-stack application for stock market sentiment analysis and insights, consisting of a **React + TypeScript** frontend and a **FastAPI + Python** backend. Both the frontend and backend follow a feature-based / layered architecture for scalability and maintainability.

## Top-Level Directory Structure

```
FYP2 Dashboard/
├── src/                      # Frontend source code (React + TypeScript)
├── backend/                  # Backend source code (FastAPI + Python)
├── docs/                     # Project documentation
├── public/                   # Static assets served by Vite
├── logs/                     # Frontend build logs (gitignored)
├── index.html                # Vite HTML entry point
├── vite.config.ts            # Vite configuration (port 8080, API proxy)
├── tailwind.config.ts        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript config (base)
├── tsconfig.app.json         # TypeScript config (app source)
├── tsconfig.node.json        # TypeScript config (Node/Vite tooling)
├── vitest.config.ts          # Vitest test configuration
├── eslint.config.js          # ESLint configuration
├── postcss.config.js         # PostCSS configuration
├── components.json           # shadcn/ui component config
├── package.json              # Frontend dependencies & scripts
└── .env                      # Frontend environment variables
```

## Frontend Structure (`src/`)

```
src/
├── features/                  # Feature-based modules
│   ├── dashboard/             # Main dashboard feature
│   │   ├── components/        # Dashboard-specific components
│   │   │   └── DashboardSkeleton.tsx
│   │   ├── pages/             # Dashboard pages
│   │   │   ├── Index.tsx          // Main dashboard view
│   │   │   ├── About.tsx          // About page
│   │   │   └── NotFound.tsx       // 404 page
│   │   └── index.ts           # Feature barrel exports
│   ├── analysis/              # Stock analysis features
│   │   ├── pages/             # Analysis pages
│   │   │   ├── StockAnalysis.tsx       // Individual stock analysis
│   │   │   ├── SentimentVsPrice.tsx    // Sentiment-price comparison
│   │   │   ├── CorrelationAnalysis.tsx // Statistical correlation
│   │   │   └── SentimentTrends.tsx     // Trend analysis
│   │   └── index.ts           # Feature barrel exports
│   └── admin/                 # Admin panel features
│       ├── components/        # Admin-specific components
│       │   ├── AdminProtectedRoute.tsx  // JWT route guard
│       │   ├── OAuth2AdminAuth.tsx      // Google OAuth2 login
│       │   ├── TOTPVerification.tsx     // TOTP 2FA verification
│       │   ├── QRCodeDisplay.tsx        // QR code for TOTP setup
│       │   └── SystemHealthAlerts.tsx   // Health alert banners
│       ├── pages/             # Admin pages
│       │   ├── AdminDashboard.tsx       // Admin overview
│       │   ├── AdminLogin.tsx           // OAuth2 login entry
│       │   ├── ModelAccuracy.tsx        // Sentiment model metrics
│       │   ├── ApiConfig.tsx            // API key management
│       │   ├── SchedulerManagerV2.tsx   // Pipeline scheduler control
│       │   ├── WatchlistManager.tsx     // Stock watchlist CRUD
│       │   ├── StorageSettings.tsx      // Database & storage config
│       │   └── SystemLogs.tsx           // Log viewer & download
│       ├── services/          # Admin service layer
│       │   └── auth.service.ts          // JWT auth, token management
│       ├── config/            # Admin configuration
│       │   └── security.config.ts       // Security constants
│       ├── middleware/        # Admin middleware
│       │   └── security.middleware.ts   // Request security checks
│       └── index.ts           # Feature barrel exports
├── shared/                    # Shared resources across features
│   ├── components/
│   │   ├── ui/                // shadcn/ui base components
│   │   ├── layouts/           // Layout components
│   │   │   ├── AdminLayout.tsx      // Admin panel layout
│   │   │   └── UserLayout.tsx       // Public user layout
│   │   ├── states/            // Empty/loading state components
│   │   │   ├── EmptyState.tsx
│   │   │   ├── EmptyPipelineState.tsx
│   │   │   ├── EmptyWatchlistState.tsx
│   │   │   ├── InsufficientCorrelationData.tsx
│   │   │   └── PartialDataWarning.tsx
│   │   └── MarketCountdown.tsx  // Market hours countdown
│   ├── hooks/                 # Custom React hooks
│   │   ├── use-mobile.tsx         // Mobile responsive hook
│   │   ├── use-toast.ts          // Toast notification hook
│   │   └── usePipelineNotifications.ts  // Pipeline event notifications
│   └── utils/                 # Utility functions
│       ├── dataValidation.ts      // Data validation helpers
│       ├── sentimentUtils.ts      // Sentiment score formatting
│       ├── timezone.ts            // Timezone utilities
│       └── utils.ts               // General utilities
├── api/                       # API integration layer
│   ├── services/              # API service classes
│   │   ├── base.service.ts        // Axios base client (auth, interceptors)
│   │   ├── dashboard.service.ts   // Dashboard API calls
│   │   ├── stock.service.ts       // Stock data API calls
│   │   ├── analysis.service.ts    // Analysis API calls
│   │   └── admin.service.ts       // Admin API calls
│   └── types/                 # API type definitions
│       └── backend-schemas.ts     // Backend response schemas
├── config/                    # Application configuration
│   └── constants.ts           // App-wide constants
├── styles/                    # Global styles
│   └── index.css              // Main Tailwind styles
├── test/                      # Test utilities
├── App.tsx                    # Main app component (React Router)
├── main.tsx                   # Application entry point
└── vite-env.d.ts              # Vite type definitions
```

## Backend Structure (`backend/`)

```
backend/
├── main.py                    # FastAPI application entry point
├── manage_db.py               # Database management CLI
├── requirements.txt           # Python dependencies
├── alembic.ini                # Alembic migration config
├── pytest.ini                 # Pytest configuration
├── .env                       # Backend environment variables (secrets)
├── alembic/                   # Database migrations
│   ├── env.py                     // Migration environment
│   ├── script.py.mako             // Migration template
│   └── versions/                  // Migration version files
├── app/                       # Application package
│   ├── presentation/          # Layer 1: API & HTTP handling
│   │   ├── routes/                // FastAPI route handlers
│   │   │   ├── admin.py               // Admin management endpoints
│   │   │   ├── analysis.py            // Sentiment analysis endpoints
│   │   │   ├── dashboard.py           // Dashboard summary endpoint
│   │   │   ├── pipeline.py            // Pipeline control endpoints
│   │   │   └── stocks.py             // Stock data endpoints
│   │   ├── controllers/          // Business logic controllers
│   │   │   └── oauth_controller.py    // OAuth2 & TOTP auth
│   │   ├── schemas/              // Pydantic request/response schemas
│   │   │   ├── admin_schemas.py
│   │   │   ├── analysis.py
│   │   │   ├── dashboard.py
│   │   │   └── stock.py
│   │   ├── dependencies/         // FastAPI dependency injection
│   │   │   └── auth_dependencies.py   // JWT auth dependencies
│   │   ├── middleware/           // HTTP middleware
│   │   │   ├── logging_middleware.py   // Request logging
│   │   │   └── security_middleware.py  // CORS, headers, rate limiting
│   │   └── deps.py              // Shared dependencies
│   ├── service/               # Layer 2: Business services
│   │   ├── admin_service.py           // Admin operations
│   │   ├── benchmark_service.py       // Model benchmarking
│   │   ├── collector_config_service.py // Collector configuration
│   │   ├── dashboard_service.py       // Dashboard aggregation
│   │   ├── price_service.py           // Real-time price fetching
│   │   ├── quota_tracking_service.py  // API quota tracking
│   │   ├── sentiment_service.py       // Sentiment orchestration
│   │   ├── storage_service.py         // Storage management
│   │   ├── system_service.py          // System health monitoring
│   │   ├── watchlist_service.py       // Watchlist management
│   │   ├── sentiment_processing/      // Sentiment analysis subsystem
│   │   │   ├── sentiment_engine.py        // Multi-model engine
│   │   │   ├── hybrid_sentiment_analyzer.py // Gemini AI analyzer
│   │   │   └── models/
│   │   │       ├── sentiment_model.py     // Base model interface
│   │   │       ├── finbert_model.py       // FinBERT model
│   │   │       └── distilbert_model.py    // DistilBERT model
│   │   ├── content_validation/        // Content filtering
│   │   │   └── relevance_validator.py     // Relevance scoring
│   │   └── data_collection/           // Data collection orchestration
│   │       ├── base.py                    // Base collection logic
│   │       └── service.py                // Collection service
│   ├── business/              # Layer 3: Business logic & orchestration
│   │   ├── data_collector.py          // Data collection orchestrator
│   │   ├── pipeline.py                // Analysis pipeline
│   │   ├── processor.py              // Data processing
│   │   ├── scheduler.py              // APScheduler job management
│   │   └── watchlist_observer.py      // Watchlist change observer
│   ├── data_access/           # Layer 4: Database & persistence
│   │   ├── database/                  // Database infrastructure
│   │   │   ├── base.py                    // SQLAlchemy base model
│   │   │   ├── connection.py              // Async DB connection
│   │   │   ├── migration_manager.py       // Auto-migration
│   │   │   └── retry_utils.py             // Connection retry logic
│   │   ├── models/                    // SQLAlchemy ORM models
│   │   └── repositories/             // Data access repositories
│   │       ├── base_repository.py         // Base CRUD repository
│   │       ├── sentiment_repository.py    // Sentiment data access
│   │       ├── stock_repository.py        // Stock data access
│   │       └── stock_price_repository.py  // Price data access
│   ├── infrastructure/        # Layer 5: External integrations
│   │   ├── collectors/                // Data source collectors
│   │   │   ├── base_collector.py          // Abstract base collector
│   │   │   ├── collector_settings.py      // Collector config
│   │   │   ├── finnhub_collector.py       // Finnhub news
│   │   │   ├── gdelt_collector.py         // GDELT news
│   │   │   ├── hackernews_collector.py    // HackerNews posts
│   │   │   ├── newsapi_collector.py       // NewsAPI articles
│   │   │   └── yfinance_collector.py      // Yahoo Finance data
│   │   ├── security/                  // Security infrastructure
│   │   │   ├── api_key_manager.py         // AES-256 key encryption
│   │   │   ├── auth_service.py            // Google OAuth2 verification
│   │   │   ├── jwt_handler.py             // JWT creation & validation
│   │   │   └── security_utils.py          // TOTP, hashing, etc.
│   │   ├── config/                    // Application settings
│   │   │   └── settings.py               // Pydantic settings from .env
│   │   ├── log_system.py             // Structured logging (structlog)
│   │   └── rate_limiter.py           // Per-collector rate limiting
│   └── utils/                 # Shared utilities
│       ├── sql.py                     // SQL helpers
│       └── timezone.py               // Timezone utilities
├── data/                      # Runtime data (gitignored)
│   ├── backups/                   // Database backups
│   ├── secure_keys/               // Encrypted API keys
│   └── training/                  // Model training data
├── logs/                      # Application logs (gitignored)
├── scripts/                   # Utility scripts
└── tests/                     # Backend test suite
```

## Architecture Principles

### 1. Feature-Based Frontend Organization
- Each major feature has its own directory under `src/features/`
- Features are self-contained with their own components, pages, and services
- The `admin/` feature includes its own middleware and security config

### 2. Layered Backend Architecture
The backend follows a strict 5-layer architecture:
1. **Presentation** — HTTP routes, schemas, middleware, auth dependencies
2. **Service** — Business services, sentiment processing, data collection
3. **Business** — Pipeline orchestration, scheduling, data collection logic
4. **Data Access** — Database models, repositories, connection management
5. **Infrastructure** — External API collectors, security, configuration, logging

### 3. Shared Frontend Resources
- Common components, hooks, and utilities are in `src/shared/`
- UI components from shadcn/ui are centralized in `src/shared/components/ui/`
- Layout components handle the two distinct UIs (user vs admin)

### 4. API Integration Layer
- All backend API calls go through `src/api/services/`
- `base.service.ts` provides an Axios client with JWT auth interceptors
- Type-safe response schemas defined in `src/api/types/backend-schemas.ts`

### 5. Configuration Management
- Frontend: environment variables via `VITE_*` prefix, centralized in `src/config/constants.ts`
- Backend: Pydantic `Settings` class in `app/infrastructure/config/settings.py` loaded from `.env`

### 6. Type Safety
- Frontend: TypeScript with strict mode, Zod for runtime validation
- Backend: Pydantic schemas for request/response validation, SQLAlchemy typed models

## Import Aliases

The frontend uses the `@/` alias for imports, which maps to the `src/` directory:
- `@/features/...` — Feature modules
- `@/shared/...` — Shared resources
- `@/api/...` — API services and types
- `@/config/...` — Configuration

## Adding New Features

### Frontend Feature
1. Create a new directory under `src/features/[feature-name]/`
2. Add subdirectories for `components/` and `pages/`
3. Create an `index.ts` barrel file to export the feature's public API
4. Add routes in `App.tsx`

### Backend Feature
1. Add route handler in `app/presentation/routes/`
2. Define Pydantic schemas in `app/presentation/schemas/`
3. Implement service logic in `app/service/`
4. Add repository if new database access is needed in `app/data_access/repositories/`
5. Register the router in `main.py`

## Best Practices

1. **Keep features isolated** — Avoid cross-feature dependencies in the frontend
2. **Use barrel exports** — Export through `index.ts` files for clean imports
3. **Respect layer boundaries** — Backend routes should never access repositories directly
4. **Type everything** — Leverage TypeScript and Pydantic for full type safety
5. **Follow naming conventions** — PascalCase for components/classes, camelCase/snake_case for utilities
