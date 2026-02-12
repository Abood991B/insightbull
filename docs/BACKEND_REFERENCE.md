# Stock Market Sentiment Dashboard - Backend Implementation Reference

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Framework](#architecture-framework)
3. [Functional Requirements](#functional-requirements)
4. [Use Cases](#use-cases)
5. [Data Model](#data-model)
6. [Technology Stack](#technology-stack)
7. [Current Frontend Analysis](#current-frontend-analysis)
8. [Integration Points](#integration-points)

## System Overview

The **Stock Market Sentiment Dashboard** is an open-source, web-based platform that provides accessible, sentiment-driven financial analytics for retail investors, financial analysts, and researchers. The system aggregates unstructured textual data from financial news sources and social media discussions for technology stocks, performs sentiment analysis, and provides interactive visualizations with correlation analysis.

### Key Features
- **Multi-source Data Collection**: HackerNews, Finnhub, NewsAPI, GDELT, Yahoo Finance
- **Hybrid Sentiment Analysis**: FinBERT for financial news + Google Gemini (Gemma 3 27B) for AI verification
- **Interactive Visualizations**: Time-series plots, correlation analysis, sentiment trends
- **Admin Panel**: OAuth2 + TOTP-secured administrative interface
- **Real-time Updates**: Dashboard polling for new data

### Target Stocks
- **Top 20 IXT Technology Stocks** including the **Magnificent Seven**:
  - AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, INTC, CSCO, AMD, AVGO, ORCL, PLTR, IBM, CRM, INTU, QCOM, TXN, AMAT, MU

## Architecture Framework

### Selected Architecture: Layered Architecture

The system follows a **5-layer architecture** pattern chosen for its clear separation of concerns, natural workflow mapping, and academic defensibility:

#### 1. Presentation Layer
- **Dashboard**: Main user interface
- **Visualizer**: Chart rendering and interactive visualizations
- **CorrelationCalculator**: Statistical analysis computations
- **Watchlist**: User stock selection management

#### 2. Business Layer (Core Orchestration)
- **Pipeline**: Central facade controlling system flow
- **Scheduler**: Automated job scheduling
- **DataCollector**: External data aggregation coordinator
- **Processor**: Text preprocessing and data cleaning

#### 3. Infrastructure Layer
- **Collectors**: HackerNewsCollector, FinnhubCollector, NewsAPICollector, GDELTCollector, YFinanceCollector
- **APIKeyManager**: Secure credential management (AES-256 encryption)
- **RateLimitHandler**: API throttling and backoff strategies
- **LogSystem**: Centralized structured logging (Singleton pattern)

#### 4. Service Layer (Analytical Intelligence)
- **SentimentEngine**: Sentiment analysis orchestration
- **SentimentModel Interface**: Strategy pattern for model abstraction
- **FinBERTModel**: Financial news sentiment analysis
- **DistilBERTModel**: Lightweight alternative sentiment model
- **HybridSentimentAnalyzer**: FinBERT + Google Gemini AI verification

#### 5. Data Access Layer
- **StorageManager**: Data persistence operations
- **SentimentRecord**: Core data structure
- **Domain Models**: Stock, Timestamp entities

### Design Patterns Implementation
- **Facade Pattern**: Pipeline class for complex workflow orchestration
- **Strategy Pattern**: Interchangeable sentiment models
- **Observer Pattern**: Dashboard updates on data changes
- **Singleton Pattern**: LogSystem for consistent logging
- **Adapter Pattern**: API client standardization

## Functional Requirements

### User Functional Requirements (U-FR)

| ID | Requirement | Description |
|---|---|---|
| U-FR1 | View Sentiment Dashboard | Interactive dashboard with sentiment scores and stock prices |
| U-FR2 | Select Time Range | 1-day, 7-day, 14-day analysis windows |
| U-FR3 | Filter by Stock | Stock-specific data visualization |
| U-FR4 | Compare Sentiment vs Price | Dual-axis overlay charts |
| U-FR5 | Dynamic Correlation Analysis | Real-time Pearson correlation calculation |
| U-FR6 | Evaluate Model Accuracy | Performance metrics (Admin) |
| U-FR7 | Configure API Keys | Secure credential management (Admin) |
| U-FR8 | Update Stock Watchlist | Modify tracked stocks (Admin) |
| U-FR9 | Manage Data Storage | Configure storage backends (Admin) |
| U-FR10 | View System Logs | Operational transparency (Admin) |

### System Functional Requirements (SY-FR)

| ID | Requirement | Description |
|---|---|---|
| SY-FR1 | Data Collection Pipeline | Multi-source data fetching with scheduling |
| SY-FR2 | Preprocess Raw Data | Text cleaning and normalization |
| SY-FR3 | Sentiment Analysis | FinBERT + Gemini AI hybrid classification |
| SY-FR4 | Store Sentiment Results | Structured data persistence |
| SY-FR5 | Schedule Batch Fetching | Automated data collection |
| SY-FR6 | Handle API Rate Limits | Throttling and retry mechanisms |
| SY-FR7 | Normalize Timestamps | UTC ISO format standardization |
| SY-FR8 | Trigger Visualization Updates | Automatic dashboard refresh |
| SY-FR9 | Log Pipeline Operations | Comprehensive operation logging |

### Non-Functional Requirements (NFR)

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Performance | Dashboard loads < 10 seconds |
| NFR-2 | Usability | Intuitive interface design |
| NFR-3 | Reliability | Robust error handling and logging |
| NFR-4 | Scalability | Support for additional stocks |
| NFR-5 | Maintainability | Well-documented, modular code |
| NFR-6 | Security | Encrypted API key storage |

## Use Cases

### Key User Use Cases

#### UC-1: View Sentiment Dashboard
- **Actor**: User
- **Description**: Access interactive dashboard with sentiment and price data
- **Flow**: User → Dashboard UI → Backend → Data Layer → Visualization

#### UC-2: Dynamic Correlation Analysis
- **Actor**: User
- **Description**: Calculate real-time Pearson correlation between sentiment and price
- **Flow**: User selects stock/timeframe → Backend computes correlation → Display results

#### UC-5: Admin Model Accuracy Evaluation
- **Actor**: Administrator
- **Description**: Review sentiment model performance metrics
- **Flow**: Admin → Evaluation Engine → Compute metrics → Display results

### Key System Use Cases

#### UC-11: Data Collection Pipeline
- **Actor**: System
- **Description**: Automated multi-source data fetching
- **Flow**: Scheduler → Pipeline → Collectors → API Sources → Raw data storage

#### UC-13: Sentiment Analysis Processing
- **Actor**: System
- **Description**: Apply appropriate sentiment models to preprocessed text
- **Flow**: Load preprocessed data → Route to FinBERT → Optional Gemini AI verification → Generate sentiment scores

## Data Model

### Entity Relationship Model

#### Core Entities

**Stock Entity**
```
- stock_symbol (VARCHAR(10), Primary Key)
- company_name (VARCHAR(100))
```

**SentimentRecord Entity**
```
- sentiment_id (INTEGER, Primary Key)
- stock_symbol (VARCHAR(10), Foreign Key → Stock)
- source (VARCHAR(20)) // hackernews, finnhub, newsapi, gdelt
- timestamp (DATETIME, UTC normalized)
- score (FLOAT) // Sentiment score
- label (VARCHAR(10)) // Positive, Neutral, Negative
- text (TEXT) // Original content
- job_id (INTEGER, Foreign Key → JobLog)
```

**CorrelationResult Entity**
```
- correlation_id (INTEGER, Primary Key)
- stock_symbol (VARCHAR(10), Foreign Key → Stock)
- date_range (VARCHAR(10)) // '1d', '7d', '14d'
- correlation_value (FLOAT) // Pearson coefficient
- calculated_at (DATETIME)
```

**JobLog Entity**
```
- job_id (INTEGER, Primary Key)
- status (VARCHAR(20)) // Completed, Failed, PartialSuccess
- start_time (DATETIME)
- end_time (DATETIME)
- message (TEXT) // Logs, errors, status
```

**ModelEvaluationResult Entity**
```
- evaluation_id (INTEGER, Primary Key)
- job_id (INTEGER, Foreign Key → JobLog)
- model_name (VARCHAR(20)) // FinBERT, DistilBERT
- accuracy (FLOAT)
- precision (FLOAT)
- recall (FLOAT)
- f1_score (FLOAT)
- evaluated_at (DATETIME)
```

## Technology Stack

### Backend Technology Stack

#### Core Libraries & Frameworks
- **Python 3.10+**: Primary language
- **FastAPI 0.115.0**: RESTful API framework
- **SQLAlchemy 2.0.36**: Async ORM for database operations
- **Pydantic 2.8.2**: Data validation and settings management
- **Pandas 2.2.3**: Data manipulation and analysis
- **NumPy 2.1.1**: Numerical computing

#### Data Collection
- **finnhub-python 2.4.20**: Finnhub API client
- **newsapi-python 0.2.7**: NewsAPI client
- **yfinance**: Yahoo Finance stock price data
- **httpx / aiohttp**: Async HTTP client for HackerNews and GDELT

#### Sentiment Analysis
- **transformers 4.45.2**: Hugging Face models (FinBERT, DistilBERT)
- **torch 2.4.1**: PyTorch backend
- **google-generativeai**: Google Gemini API for AI verification

#### Data Storage
- **aiosqlite 0.20.0**: Async SQLite (development)
- **asyncpg 0.29.0 / psycopg2-binary**: PostgreSQL (production)
- **Alembic 1.13.3**: Database migrations

#### Infrastructure
- **APScheduler 3.10.4**: Job scheduling
- **python-dotenv**: Environment variable management
- **cryptography 43.0.3**: API key encryption (AES-256)
- **PyJWT 2.9.0**: JSON Web Token authentication
- **structlog 24.4.0**: Structured logging

#### Development & Testing
- **pytest 8.3.3**: Testing framework
- **pytest-asyncio**: Async test support
- **black 24.10.0**: Code formatting
- **isort 5.13.2**: Import sorting
- **flake8 7.1.1**: Linting

## Current Frontend Analysis

### Technology Stack
- **React 18** with TypeScript
- **Vite** build tool
- **TanStack Query** for data fetching
- **Radix UI** component library
- **Tailwind CSS** for styling
- **Recharts** for data visualization

### Key Components Structure

#### User Dashboard Components
```
src/features/dashboard/
├── pages/
│   ├── Index.tsx          // Main dashboard view
│   ├── About.tsx          // About page
│   └── NotFound.tsx       // 404 page
```

#### Analysis Components
```
src/features/analysis/
├── pages/
│   ├── StockAnalysis.tsx      // Individual stock analysis
│   ├── SentimentVsPrice.tsx   // Sentiment-price comparison
│   ├── CorrelationAnalysis.tsx // Statistical correlation
│   └── SentimentTrends.tsx    // Trend analysis
```

#### Admin Components
```
src/features/admin/
├── components/
│   ├── AdminProtectedRoute.tsx    // Route protection
│   ├── OAuth2AdminAuth.tsx       // OAuth2 authentication
│   ├── TOTPVerification.tsx      // TOTP 2FA
│   ├── QRCodeDisplay.tsx         // QR code generation
│   └── SystemHealthAlerts.tsx    // Health alert banners
├── pages/
│   ├── AdminDashboard.tsx        // Admin overview
│   ├── AdminLogin.tsx            // OAuth2 login entry
│   ├── ModelAccuracy.tsx         // Model performance
│   ├── ApiConfig.tsx            // API configuration
│   ├── SchedulerManagerV2.tsx   // Pipeline scheduler
│   ├── WatchlistManager.tsx     // Stock management
│   ├── StorageSettings.tsx      // Data storage config
│   └── SystemLogs.tsx           // System monitoring
└── services/
    └── auth.service.ts          // Authentication logic
```

### Data Patterns

The frontend consumes the FastAPI backend with these data structures:

#### Stock Data Structure
```typescript
interface Stock {
  symbol: string;
  name: string;
  sentiment: number;  // 0.0 to 1.0
  price: number;
  change: number;     // percentage
}
```

#### Sentiment Data Structure
```typescript
interface SentimentData {
  name: 'Positive' | 'Neutral' | 'Negative';
  value: number;
  color: string;
}
```

### Authentication System
- **OAuth2 Google Login**: Server-side Google OAuth2 via `/api/admin/auth/oauth/google`
- **TOTP 2FA**: QR code setup via `/api/admin/auth/totp/setup`, verification via `/api/admin/auth/totp/verify`
- **JWT Tokens**: Server-issued JWT access tokens stored in memory, refresh via activity monitoring
- **Admin Allow-list**: Backend `ADMIN_EMAILS` env var controls who can authenticate

## Integration Points

### API Endpoints (Implemented)

#### Public Endpoints
```
GET  /api/dashboard/summary                        // Dashboard overview data
GET  /api/stocks/                                   // All tracked stocks
GET  /api/stocks/{symbol}                           // Individual stock detail
GET  /api/stocks/{symbol}/analysis                  // Stock analysis data
GET  /api/analysis/stocks/{symbol}/sentiment        // Sentiment history
GET  /api/analysis/stocks/{symbol}/correlation      // Sentiment-price correlation
```

#### Admin Authentication Endpoints (prefix: `/api/admin`)
```
POST /api/admin/auth/oauth/google    // Google OAuth2 login
POST /api/admin/auth/totp/verify     // TOTP 2FA verification
GET  /api/admin/auth/totp/setup      // TOTP QR code setup
```

#### Admin Management Endpoints (prefix: `/api/admin`, JWT required)
```
GET  /api/admin/health                              // Admin health check
POST /api/admin/data-collection/manual              // Manual data collection
POST /api/admin/data-collection/trigger             // Trigger collection

GET  /api/admin/models/accuracy                     // Model accuracy metrics
GET  /api/admin/models/benchmark                    // Benchmark results
POST /api/admin/models/benchmark/run                // Run benchmark
GET  /api/admin/models/sentiment-engine-metrics     // Sentiment engine metrics

GET  /api/admin/config/apis                         // API key status
PUT  /api/admin/config/apis                         // Update API keys
GET  /api/admin/config/collectors                   // Collector configs
PUT  /api/admin/config/collectors/{name}            // Update collector config
GET  /api/admin/config/ai-services                  // AI service configs
PUT  /api/admin/config/ai-services/{name}/toggle    // Toggle AI service
PUT  /api/admin/config/ai-services/{name}/settings  // Update AI settings

GET  /api/admin/watchlist                           // Current watchlist
PUT  /api/admin/watchlist                           // Update watchlist
GET  /api/admin/stocks/search                       // Search stocks

GET  /api/admin/storage                             // Storage statistics
POST /api/admin/storage/optimize                    // Optimize database
POST /api/admin/storage/backup                      // Create backup

GET  /api/admin/logs                                // System logs
GET  /api/admin/logs/download                       // Download logs
DEL  /api/admin/logs/clear                          // Clear old logs

GET  /api/admin/system/status                       // System health
GET  /api/admin/market/status                       // Market hours status
GET  /api/admin/collectors/health                   // Collector health

GET  /api/admin/scheduler/jobs                      // Scheduled jobs
GET  /api/admin/scheduler/jobs/{job_id}             // Job detail
PUT  /api/admin/scheduler/jobs/{job_id}             // Update job
GET  /api/admin/scheduler/events                    // Scheduler events
GET  /api/admin/scheduler/history                   // Job history
POST /api/admin/scheduler/refresh                   // Refresh scheduler

POST /api/admin/realtime-price-service/start        // Start price service
GET  /api/admin/realtime-price-service/status       // Price service status
POST /api/admin/realtime-price-service/stop         // Stop price service
PUT  /api/admin/realtime-price-service/config       // Update config
POST /api/admin/realtime-price-service/test-fetch   // Test price fetch
POST /api/admin/realtime-price-service/update-market-caps // Update caps
GET  /api/admin/realtime-price-service/debug        // Debug info

GET  /api/admin/database/schema                     // Database schema
GET  /api/admin/database/tables/{name}/data         // Table data
GET  /api/admin/database/tables/{name}/export       // Export table
GET  /api/admin/database/stats                      // Database stats
```

#### Data Pipeline Endpoints (prefix: `/api/admin/pipeline`, JWT required)
```
POST /api/admin/pipeline/configure   // Configure pipeline
POST /api/admin/pipeline/run         // Run pipeline
GET  /api/admin/pipeline/status      // Pipeline status
GET  /api/admin/pipeline/result      // Latest result
POST /api/admin/pipeline/cancel      // Cancel running pipeline
GET  /api/admin/pipeline/health      // Pipeline health
GET  /api/admin/pipeline/collectors  // Collector status
GET  /api/admin/pipeline/rate-limits // Rate limit status
```

### Data Format Specifications

#### Stock Response Format
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "current_price": 192.53,
  "change_24h": 1.2,
  "sentiment_score": 0.78,
  "sentiment_label": "Positive",
  "last_updated": "2025-09-16T10:30:00Z"
}
```

#### Sentiment History Format
```json
{
  "symbol": "AAPL",
  "timeframe": "7d",
  "data": [
    {
      "timestamp": "2025-09-16T10:00:00Z",
      "sentiment_score": 0.78,
      "price": 192.53,
      "volume": 50000
    }
  ],
  "correlation": 0.65,
  "total_records": 100
}
```

### Frontend-Backend Communication

#### API Client Configuration
The frontend sends API calls to:
- **Base URL**: `http://localhost:8000/api` (configurable via `VITE_API_BASE_URL`)
- **Timeout**: 30 seconds
- **Headers**: `Content-Type: application/json`
- **Authentication**: Bearer JWT token in `Authorization` header

#### Error Handling
Frontend expects standardized error responses:
```json
{
  "error": "Error message",
  "status": 400,
  "details": "Optional detailed information"
}
```

#### Real-time Updates
The frontend implements polling for real-time updates:
- **Dashboard**: Polls every 30 seconds
- **Analysis Pages**: Polls every 60 seconds
- **Admin Logs**: Polls every 10 seconds

### Security Integration Points

#### Authentication Flow
1. **OAuth2 Login**: Frontend sends Google `id_token` → Backend verifies with Google → checks `ADMIN_EMAILS` allow-list → returns JWT + TOTP requirement flag
2. **TOTP Setup** (first login): Backend generates TOTP secret → returns QR code URI → admin scans with authenticator app
3. **TOTP Verification**: Admin submits TOTP code → backend verifies → returns full-access JWT
4. **Session Management**: JWT expiry + frontend activity monitoring with configurable timeout

#### API Security
- **Rate Limiting**: Implement per-IP and per-user limits
- **CORS Configuration**: Allow frontend origin
- **Input Validation**: Sanitize all inputs
- **SQL Injection Prevention**: Use parameterized queries

This reference document describes the fully implemented backend system and its integration with the React frontend, aligned with the project specification requirements.