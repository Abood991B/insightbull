# GitHub Copilot Instructions

## Project Overview

**Insight Stock Dashboard** is a sentiment analysis platform for stock market insights, combining React/TypeScript frontend with Python/FastAPI backend. The system aggregates financial news and social media data, performs dual-model sentiment analysis (FinBERT + VADER), and provides interactive visualizations with correlation analysis.

**Target Stocks**: Top 20 IXT Technology stocks (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, etc.)

### Current Implementation Status
- **Backend**: ✅ Fully implemented and operational (all 5 layers complete)
- **Frontend**: 🔄 Integration in progress - **PRIORITY: Replace all mock data with real backend API calls**
- **Main Reference**: `FYP-Report.md` (6000+ lines) - the authoritative source for all project specifications, architecture decisions, and requirements. Always consult this document for context on design patterns, data models, and system behavior.

## Architecture

### Backend: 5-Layer Architecture
The backend strictly follows a clean 5-layer pattern defined in `backend/app/`:

1. **Presentation Layer** (`presentation/`): FastAPI controllers, middleware, request/response schemas
2. **Business Layer** (`business/`): Core orchestration - `pipeline.py` (Facade pattern), `processor.py`, `scheduler.py`
3. **Infrastructure Layer** (`infrastructure/`): External APIs (collectors), security, rate limiting, logging
4. **Service Layer** (`service/`): Application services - sentiment analysis, data collection, dashboard logic
5. **Data Access Layer** (`data_access/`): SQLAlchemy models, repositories (Repository pattern), database connection

**Critical Pattern**: Always import following layer hierarchy - never skip layers or create circular dependencies.
- Example: Controllers import Services, Services import Repositories, never Controllers→Repositories directly
- Import pattern: `from app.{layer}.{module} import ClassName`

### Frontend: Feature-Based Architecture
Structure in `src/`:
- `features/`: Self-contained modules (`dashboard/`, `analysis/`, `admin/`)
- `shared/`: Common components, hooks, utilities
- `api/services/`: Backend integration (`base.service.ts`, `admin.service.ts`)
- Import alias: `@/` maps to `src/`

## Critical Workflows

### Backend Development

**Database Migrations** (Alembic):
```powershell
# Create migration
alembic revision --autogenerate -m "Description"
# Apply migrations
alembic upgrade head
# Rollback
alembic downgrade -1
```

**Running Backend**:
```powershell
cd backend
# Activate venv: .\venv\Scripts\activate.bat
python main.py
# API docs: http://localhost:8000/api/docs
```

**Testing** (Phase-based test suite in `backend/tests/`):
```powershell
pytest tests/                                    # All tests
pytest tests/test_01_security_auth.py           # Security tests
pytest tests/test_06_pipeline_orchestration.py  # Pipeline tests
```
Test phases: 01-Security, 02-API Encryption, 03-Collector Encryption, 04-Data Collection, 05-Sentiment Analysis, 06-Pipeline, 07-Admin Panel, 08-Integration, 09-Cross-Phase

### Frontend Development

**Running Frontend**:
```powershell
npm run dev          # Development server (port 8080)
npm run build        # Production build
npm run build:dev    # Development build
```

**CRITICAL: Frontend Integration Tasks**
The backend is fully operational - focus on connecting frontend to real APIs:
1. **Remove Mock Data**: Search for `mockData`, `const mock*`, hardcoded arrays in `src/features/`
   - Example: `src/features/analysis/pages/SentimentVsPrice.tsx` line 9 has `mockData` array
2. **Use Real API Services**: Replace hardcoded data with calls to `admin.service.ts` and `base.service.ts`
3. **Connect to Backend Endpoints**: All routes in `backend/app/presentation/routes/` are live
4. **Handle Empty Database State**: ⚠️ **CRITICAL** - Database is currently empty (pipeline not run). Every page MUST gracefully handle:
   - No sentiment data collected yet
   - Empty watchlist (no stocks tracked)
   - Insufficient data for analysis (< 5-10 points)
   - Show user-friendly empty states with pipeline instructions
5. **Test Integration**: Backend runs on `localhost:8000`, frontend on `localhost:8080` with CORS configured

**Admin Access**: Navigate directly to `/admin` (hidden from UI). Requires:
1. Google OAuth2 (whitelisted email in `VITE_ADMIN_EMAILS`)
2. TOTP verification (Google Authenticator/Authy)
3. Session timeout: 30 minutes

## Project-Specific Conventions

### Security Implementation
- **API Keys**: Encrypted with `SecureAPIKeyLoader` (backend), stored in `backend/data/secure_keys/`
- **Admin Auth**: Multi-factor (OAuth2 + TOTP), session-based with `authService.ts`
- **Rate Limiting**: `RateLimitHandler` with exponential backoff for external APIs
- **CORS**: Configured in `setup_security_middleware()` with allowed origins

### Data Collection Pipeline
- **Entry Point**: `business/pipeline.py` - Facade pattern orchestrating collectors
- **Collectors**: `HackerNewsCollector`, `YFinanceCollector`, `GDELTCollector`, `FinHubCollector`, `NewsAPICollector`
- **Watchlist**: Dynamic stock management via `WatchlistService` (database-driven, not static lists)
- **Scheduler**: `business/scheduler.py` using APScheduler for automated collection

### Sentiment Analysis
- **Models**: FinBERT (financial news) + Gemma 3 27B AI verification
- **Service**: `service/sentiment_processing/hybrid_sentiment_analyzer.py`
- **Storage**: `SentimentData` model with `sentiment_label` (positive/neutral/negative)

### Structured Logging
- **System**: Singleton pattern `infrastructure/log_system.py`
- **Format**: JSON structured logs with correlation IDs
- **Usage**: `logger = get_logger()` - never instantiate directly

### Database Models
- **ORM**: SQLAlchemy 2.0 async
- **Key Models**: `Stock`, `SentimentData`, `StockPrice`, `NewsArticle`, `RedditPost`, `StocksWatchlist`
- **Migrations**: See `backend/alembic/versions/` for schema history

### Frontend API Integration
- **Base Service**: `src/api/services/base.service.ts` with timeout/error handling
- **Admin API**: `src/api/services/admin.service.ts` - comprehensive admin operations
- **Pattern**: Use `BaseService` for all new API services, implement typed responses

## Code Style Guidelines

### General Principles
- Professional tone - no emojis in code/comments/commits/docs
- Technical clarity over verbosity
- Descriptive names following domain language
- Summaries in chat responses, not separate files

### Backend (Python)
- Follow FastAPI best practices with Pydantic schemas
- Use type hints consistently
- Async/await for all database and external API calls
- Docstrings: Google-style format with Args/Returns/Raises

### Frontend (TypeScript)
- Strict TypeScript - avoid `any`, prefer interfaces
- React functional components with hooks
- shadcn/ui for UI components (`src/shared/components/ui/`)
- Layouts in `src/shared/components/layouts/`

### Commit Messages
- Imperative mood: "Add feature" not "Added feature"
- Professional, no emojis
- Include context for complex changes

## Key Files Reference

### Backend Entry Points
- `backend/main.py`: FastAPI app with lifespan management
- `backend/app/presentation/routes/`: API route definitions
- `backend/app/infrastructure/config/settings.py`: Environment config (Pydantic Settings)

### Frontend Entry Points
- `src/App.tsx`: React Router setup with protected routes
- `src/main.tsx`: Application bootstrap with QueryClient
- `vite.config.ts`: Build config with `@/` alias

### Documentation
- **`FYP-Report.md`**: 📘 **PRIMARY REFERENCE** - Full project specification (6055 lines covering literature review, architecture, requirements, data models, implementation plan)
- **`docs/FRONTEND_INTEGRATION_PLAN.md`**: 🎯 **INTEGRATION ROADMAP** - Phase-by-phase plan for connecting frontend to backend, mock data inventory, API mappings
- **`docs/EMPTY_STATE_GUIDE.md`**: ⚠️ **EMPTY DATABASE HANDLING** - Critical guide for handling empty database state (pipeline not run yet)
- `docs/BACKEND_REFERENCE.md`: Full backend specification (derived from FYP Report)
- `docs/SECURITY_IMPLEMENTATION.md`: OAuth2 + TOTP setup
- `docs/PROJECT_STRUCTURE.md`: Frontend architecture
- `backend/README.md`: Quick start guide

**When to Consult FYP-Report.md**:
- Understanding system requirements (Chapter 3: Requirements Analysis)
- Architecture decisions and patterns (Chapter 4: System Design - layered architecture justification)
- Data models and schemas (Section 4.7: Entity-Relationship Diagram)
- Sentiment analysis model selection rationale (Section 2.3.3-2.3.4: FinBERT + VADER justification)
- API integration specifications (Section 2.4: Data Sources)
- Testing strategy (Chapter 7: Implementation & Testing Plan)

**When to Consult FRONTEND_INTEGRATION_PLAN.md**:
- Starting frontend integration work (see Phase-Based Implementation)
- Identifying which files have mock data (Mock Data Inventory table)
- Finding corresponding backend endpoints (Backend API Mapping section)
- Understanding service layer architecture (Service Layer Architecture section)
- Testing integration work (Testing & Validation checklist)

## Integration Points

### Frontend ↔ Backend
- **Dev Setup**: Frontend port 8080, Backend port 8000
- **CORS**: Configured in `settings.py` allowed_origins
- **Auth**: Bearer tokens via `authService.ts` for admin endpoints
- **Base URL**: `VITE_API_URL` env variable (default: `http://localhost:8000`)

### External Dependencies
- **Google OAuth2**: Requires `VITE_GOOGLE_CLIENT_ID` and callback URI setup
- **API Keys**: FinHub, NewsAPI (managed via admin panel post-encryption)
- **Database**: PostgreSQL (prod) or SQLite (dev) - configured via `DATABASE_URL`

## Common Pitfalls
- **Don't** bypass layer architecture - respect the 5-layer separation
- **Don't** create static stock lists - use `WatchlistService` dynamic management
- **Don't** instantiate `LogSystem` directly - use `get_logger()`
- **Don't** hardcode API keys - use `SecureAPIKeyLoader` or environment variables
- **Don't** forget to run Alembic migrations after model changes
- **Don't** leave mock data in frontend - backend is fully functional, always integrate real APIs
- **Don't** ignore FYP-Report.md - it contains the authoritative specifications for all features

## Frontend-Specific Integration Checklist
When working on frontend components:
1. ✅ **Consult Integration Plan**: Reference `docs/FRONTEND_INTEGRATION_PLAN.md` for phase roadmap and specific file tasks
2. ✅ **Check Mock Data Inventory**: Use the table in FRONTEND_INTEGRATION_PLAN.md to identify which files need integration
3. ✅ **Find Backend Endpoint**: Use "Backend API Mapping" section to identify correct endpoint and response schema
4. ✅ **Create/Use Service**: Extend `BaseService` following service layer patterns in integration plan
5. ✅ **Implement React Query**: Replace mock data with `useQuery` hooks (see hook patterns in plan)
6. ✅ **Add UI States**: Implement loading skeletons, error boundaries, and empty states
7. ✅ **Validate Data**: Ensure response matches FYP-Report.md Section 4.7 (Entity-Relationship Diagram)
8. ✅ **Test Integration**: Follow testing checklist in integration plan before marking phase complete
