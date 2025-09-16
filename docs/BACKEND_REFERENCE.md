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
- **Multi-source Data Collection**: Reddit (PRAW), FinHub, Marketaux, NewsAPI
- **Dual-model Sentiment Analysis**: FinBERT for financial news, VADER for social media
- **Interactive Visualizations**: Time-series plots, correlation analysis, sentiment trends
- **Admin Panel**: TOTP-secured administrative interface
- **Real-time Updates**: Dashboard polling for new data

### Target Stocks
- **Top 20 IXT Technology Stocks** including the **Magnificent Seven**:
  - AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, INTC, CSCO, AMD, AVGO, ORCL, PLTR, IBM, CRM, INTU

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
- **Collectors**: RedditCollector, FinHubCollector, NewsAPICollector, MarketauxCollector
- **APIKeyManager**: Secure credential management
- **RateLimitHandler**: API throttling and backoff strategies
- **LogSystem**: Centralized logging (Singleton pattern)

#### 4. Service Layer (Analytical Intelligence)
- **SentimentEngine**: Sentiment analysis orchestration
- **SentimentModel Interface**: Strategy pattern for model abstraction
- **VADERModel**: Social media sentiment analysis
- **FinBERTModel**: Financial news sentiment analysis

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
| SY-FR3 | Sentiment Analysis | VADER + FinBERT classification |
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
- **Flow**: Load preprocessed data → Route to VADER/FinBERT → Generate sentiment scores

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
- source (VARCHAR(20)) // Reddit, FinHub, Marketaux, NewsAPI
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
- model_name (VARCHAR(20)) // VADER, FinBERT
- accuracy (FLOAT)
- precision (FLOAT)
- recall (FLOAT)
- f1_score (FLOAT)
- evaluated_at (DATETIME)
```

## Technology Stack

### Backend Technology Requirements

Based on the FYP Report analysis, the backend should implement:

#### Core Libraries & Frameworks
- **Python 3.8+**: Primary language
- **FastAPI/Flask**: RESTful API framework
- **SQLAlchemy**: ORM for database operations
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **scikit-learn**: Machine learning utilities

#### Data Collection
- **PRAW**: Reddit API wrapper
- **finnhub-python**: FinHub API client
- **newsapi-python**: NewsAPI client
- **requests**: HTTP client for Marketaux

#### Sentiment Analysis
- **transformers**: Hugging Face models (FinBERT)
- **torch**: PyTorch backend
- **nltk**: VADER sentiment analyzer
- **BeautifulSoup4**: HTML parsing

#### Data Storage
- **PostgreSQL/SQLite**: Primary database
- **Redis**: Caching layer (optional)
- **yfinance**: Stock price data

#### Infrastructure
- **Celery**: Task scheduling and background jobs
- **APScheduler**: Alternative job scheduler
- **python-dotenv**: Environment variable management
- **cryptography**: API key encryption

#### Development & Testing
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

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
│   ├── Index.tsx          // Main dashboard with mock data
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
│   └── QRCodeDisplay.tsx         // QR code generation
├── pages/
│   ├── AdminDashboard.tsx        // Admin overview
│   ├── AdminLogin.tsx            // Simple login
│   ├── ModelAccuracy.tsx         // Model performance
│   ├── ApiConfig.tsx            // API configuration
│   ├── WatchlistManager.tsx     // Stock management
│   ├── StorageSettings.tsx      // Data storage config
│   └── SystemLogs.tsx           // System monitoring
└── services/
    └── auth.service.ts          // Authentication logic
```

### Current Data Patterns

The frontend currently uses **mock data** with these patterns:

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
- **Basic Admin Login**: username/password (demo: admin/admin123)
- **OAuth2 Google Integration**: Implemented but not connected to backend
- **TOTP 2FA**: Full implementation with QR codes and secret generation
- **Session Management**: Local storage-based with activity monitoring

## Integration Points

### API Endpoints Required

Based on frontend analysis, the backend needs to implement:

#### User Endpoints
```
GET  /api/dashboard/summary           // Dashboard overview data
GET  /api/stocks                      // All tracked stocks
GET  /api/stocks/{symbol}             // Individual stock data
GET  /api/stocks/{symbol}/sentiment   // Stock sentiment history
GET  /api/stocks/{symbol}/correlation // Sentiment-price correlation
GET  /api/analysis/correlation        // Cross-stock correlation
GET  /api/analysis/trends/{symbol}    // Sentiment trends
```

#### Admin Endpoints
```
POST /api/admin/auth/login           // Basic authentication
POST /api/admin/auth/oauth/google    // OAuth2 authentication
POST /api/admin/auth/totp/verify     // TOTP verification
GET  /api/admin/auth/totp/setup      // TOTP setup
POST /api/admin/auth/logout          // Session termination

GET  /api/admin/models/accuracy      // Model performance metrics
PUT  /api/admin/models/retrain       // Trigger model retraining

GET  /api/admin/config/apis          // API configuration status
PUT  /api/admin/config/apis          // Update API keys

GET  /api/admin/watchlist            // Current stock watchlist
PUT  /api/admin/watchlist            // Update watchlist

GET  /api/admin/storage/status       // Storage system status
PUT  /api/admin/storage/settings     // Update storage config

GET  /api/admin/logs                 // System logs
GET  /api/admin/system/status        // System health
```

#### Data Pipeline Endpoints
```
POST /api/pipeline/trigger           // Manual pipeline execution
GET  /api/pipeline/status            // Pipeline status
GET  /api/pipeline/jobs              // Job history
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
The frontend expects API calls to:
- **Base URL**: `http://localhost:3000/api` (configurable via `VITE_API_BASE_URL`)
- **Timeout**: 30 seconds
- **Headers**: `Content-Type: application/json`
- **Authentication**: Bearer token in Authorization header

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
1. **Basic Login**: POST credentials → receive JWT token
2. **OAuth2 Flow**: Redirect to Google → callback with code → exchange for tokens
3. **TOTP Verification**: Validate TOTP code → receive full access token
4. **Session Management**: Token refresh and activity monitoring

#### API Security
- **Rate Limiting**: Implement per-IP and per-user limits
- **CORS Configuration**: Allow frontend origin
- **Input Validation**: Sanitize all inputs
- **SQL Injection Prevention**: Use parameterized queries

This reference document provides the complete foundation for implementing the backend system that will integrate seamlessly with the existing frontend while fulfilling all requirements specified in the FYP Report.