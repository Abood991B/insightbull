# Insight Stock Dashboard

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?style=flat&logo=react&logoColor=white)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5.3-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **AI-Powered Stock Market Sentiment Analysis Platform for Retail Investors**

## Overview

**Insight Stock Dashboard** is a production-ready, full-stack web application that combines real-time sentiment analysis with stock market data to provide actionable insights. Built as a Final Year Project (FYP), it bridges the gap between qualitative market psychology and quantitative financial data.

The platform aggregates financial news from multiple sources, applies hybrid AI sentiment analysis (FinBERT + Google Gemma 3 27B), and correlates sentiment trends with stock price movements to help retail investors, financial analysts, and researchers make informed decisions.

### Key Highlights

| Feature | Description |
|---------|-------------|
| **91%+ Sentiment Accuracy** | Hybrid FinBERT ML + Gemma AI verification achieving industry-leading confidence |
| **5 Data Sources** | HackerNews, FinHub, NewsAPI, GDELT, Yahoo Finance |
| **Real-Time Analysis** | 45-minute automated pipeline during market hours |
| **20 Tech Stocks** | Magnificent Seven + IXT Leaders |
| **Enterprise Security** | OAuth2 + TOTP multi-factor authentication |
| **Production Optimized** | 77% token reduction, 5-8 min pipeline execution |

### Target Stocks
```
AAPL  MSFT  NVDA  GOOGL  AMZN  META  TSLA  INTC  CSCO  AMD
AVGO  ORCL  PLTR  IBM   CRM   INTU  QCOM  TXN   AMAT  MU
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INSIGHT STOCK DASHBOARD                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND (React/TypeScript)                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │   │
│  │  │  Dashboard   │  │   Analysis   │  │    Admin Panel     │    │   │
│  │  │  - Summary   │  │  - Trends    │  │  - Scheduler       │    │   │
│  │  │  - Charts    │  │  - Sentiment │  │  - API Keys        │    │   │
│  │  │  - Stocks    │  │  - Correlation│ │  - Watchlist       │    │   │
│  │  └──────────────┘  └──────────────┘  └────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    BACKEND (FastAPI/Python)                      │   │
│  │                                                                  │   │
│  │  Presentation → Business → Service → Infrastructure → Data      │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────────┐  ┌────────────────────┐  │   │
│  │  │   Pipeline  │  │  Hybrid Sentiment│  │     Collectors     │  │   │
│  │  │   Facade    │──│   FinBERT +     │──│  HN/FH/News/GDELT  │  │   │
│  │  │             │  │   Gemma 3 27B   │  │  Yahoo Finance     │  │   │
│  │  └─────────────┘  └─────────────────┘  └────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      DATABASE (SQLite/PostgreSQL)                │   │
│  │     Stocks │ SentimentData │ StockPrices │ NewsArticles         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Backend: 5-Layer Clean Architecture
```
Presentation Layer → Business Layer → Service Layer → Infrastructure Layer → Data Access Layer
```
- **Presentation**: FastAPI controllers, routes, request/response schemas
- **Business**: Pipeline (Facade pattern), Scheduler, Processor
- **Service**: Sentiment analysis, Dashboard, Admin, Watchlist
- **Infrastructure**: Collectors, Security, Rate limiting, Logging
- **Data Access**: SQLAlchemy models, Repositories

### Frontend: Feature-Based Architecture
```
src/
├── features/           # Self-contained feature modules
│   ├── dashboard/      # Main dashboard with market overview
│   ├── analysis/       # Sentiment analysis, trends, correlation
│   └── admin/          # Protected admin panel
├── shared/             # Shared components, hooks, utilities
├── api/services/       # Backend API integration layer
└── config/             # Application configuration
```

---

## Features

### User Dashboard
- **Market Overview**: Real-time sentiment distribution (positive/neutral/negative)
- **Top Stocks**: Ranked by sentiment score with price data
- **Price Movers**: Stocks with significant price changes
- **System Health**: Data collection status and pipeline metrics

### Analysis Tools
- **Sentiment vs Price**: Dual-axis charts comparing sentiment trends with stock prices
- **Correlation Analysis**: Pearson coefficient calculations (1, 7, 14-day windows)
- **Sentiment Trends**: Historical sentiment tracking with 45-minute granularity
- **Stock Deep Dive**: Individual stock analysis with news sources

### Admin Panel (Protected)
- **Scheduler Manager**: Control automated pipeline with smart presets
- **API Configuration**: Encrypted API key management (AES-256)
- **Watchlist Manager**: Add/remove tracked stocks dynamically
- **Model Accuracy**: Benchmark sentiment models against datasets
- **System Logs**: Real-time log streaming with filtering
- **Storage Settings**: Database maintenance and backups

### Security Features
- **Multi-Factor Authentication**: Google OAuth2 + TOTP (Google Authenticator)
- **Email Whitelist**: Only authorized emails can access admin
- **Session Management**: 30-minute timeout with activity tracking
- **Rate Limiting**: Exponential backoff for API protection
- **Encrypted Storage**: AES-256 for API keys, secure cookies

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI framework |
| TypeScript | 5.5.3 | Type safety |
| Vite | 5.4.1 | Build tool |
| TanStack Query | 5.56.2 | Server state management |
| React Router | 6.26.2 | Client-side routing |
| Recharts | 2.12.7 | Data visualization |
| shadcn/ui | Latest | UI components (Radix-based) |
| Tailwind CSS | 3.4.11 | Styling |
| Axios | 1.12.1 | HTTP client |
| Zod | 3.23.8 | Schema validation |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115.0 | Web framework |
| Python | 3.10+ | Runtime |
| SQLAlchemy | 2.0.36 | Async ORM |
| Transformers | 4.45.2 | FinBERT model |
| PyTorch | 2.4.1 | ML framework |
| Google Gemini | Gemma 3 27B | AI verification |
| APScheduler | 3.10.4 | Job scheduling |
| Alembic | 1.13.3 | Database migrations |
| Pydantic | 2.8.2 | Data validation |
| structlog | 24.4.0 | Structured logging |

### External APIs
| Service | Purpose |
|---------|---------|
| FinHub | Professional financial news |
| NewsAPI | Aggregated news (80,000+ sources) |
| Yahoo Finance | Stock prices and market data |
| GDELT | Global news event database |
| HackerNews | Tech community discussions |
| Google AI Studio | Gemini API for AI verification |

---

## Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.10+
- **Git**
- **4GB+ RAM** (for ML models)

### 1. Clone Repository
```bash
git clone https://github.com/Abood991B/insight-stock-dash.git
cd insight-stock-dash
```

### 2. Backend Setup
```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (GEMINI_API_KEY, FINNHUB_API_KEY, etc.)

# Initialize database
alembic upgrade head

# Start server
python main.py
```
Backend runs at: `http://localhost:8000`  
API Docs: `http://localhost:8000/api/docs`

### 3. Frontend Setup
```powershell
# From project root
cd ..

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with VITE_API_URL, VITE_GOOGLE_CLIENT_ID, etc.

# Start development server
npm run dev
```
Frontend runs at: `http://localhost:8080`

### 4. First-Time Setup
1. Access admin panel: `http://localhost:8080/admin`
2. Login with authorized Google account
3. Set up TOTP (scan QR code with authenticator app)
4. Navigate to **API Configuration** → Add your API keys
5. Go to **Watchlist Manager** → Verify tracked stocks
6. Start the **Scheduler** → Begin data collection

---

## Project Structure

```
insight-stock-dashboard/
├── backend/                          # Python/FastAPI Backend
│   ├── app/
│   │   ├── presentation/             # API routes and schemas
│   │   │   ├── routes/               # FastAPI routers
│   │   │   └── schemas/              # Pydantic models
│   │   ├── business/                 # Core business logic
│   │   │   ├── pipeline.py           # Data collection facade
│   │   │   └── scheduler.py          # APScheduler management
│   │   ├── service/                  # Application services
│   │   │   ├── sentiment_processing/ # FinBERT + Gemma AI
│   │   │   └── *.py                  # Dashboard, Admin, etc.
│   │   ├── infrastructure/           # External integrations
│   │   │   ├── collectors/           # Data source adapters
│   │   │   ├── security/             # Auth, encryption
│   │   │   └── log_system.py         # Structured logging
│   │   └── data_access/              # Database layer
│   │       ├── models/               # SQLAlchemy models
│   │       └── repositories/         # Repository pattern
│   ├── alembic/                      # Database migrations
│   ├── scripts/                      # Utility scripts
│   ├── tests/                        # 9-phase test suite
│   ├── data/                         # Runtime data
│   └── logs/                         # Application logs
│
├── src/                              # React/TypeScript Frontend
│   ├── features/                     # Feature modules
│   │   ├── dashboard/                # Main dashboard
│   │   │   └── pages/                # Index, About, NotFound
│   │   ├── analysis/                 # Analysis pages
│   │   │   └── pages/                # Trends, Correlation, etc.
│   │   └── admin/                    # Admin panel
│   │       ├── pages/                # Dashboard, Config, etc.
│   │       ├── components/           # OAuth, TOTP, etc.
│   │       └── services/             # Admin API service
│   ├── shared/                       # Shared resources
│   │   ├── components/               # UI components
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   ├── layouts/              # Page layouts
│   │   │   └── states/               # Empty states
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── utils/                    # Utility functions
│   │   └── types/                    # TypeScript types
│   ├── api/                          # API integration
│   │   └── services/                 # Service classes
│   ├── config/                       # Configuration
│   ├── styles/                       # Global styles
│   ├── App.tsx                       # Root component
│   └── main.tsx                      # Entry point
│
├── docs/                             # Documentation
│   ├── BACKEND_REFERENCE.md          # Backend specification
│   ├── SECURITY_IMPLEMENTATION.md    # OAuth2 + TOTP setup
│   ├── ADMIN_SECURITY_SETUP.md       # Admin panel setup guide
│   ├── SCHEDULER_V2_GUIDE.md         # Smart scheduler documentation
│   ├── DATABASE_MIGRATIONS.md        # Alembic migration guide
│   ├── PROJECT_STRUCTURE.md          # Frontend architecture
│   ├── EMPTY_STATE_GUIDE.md          # Empty database handling
│   └── SETUP.md                      # Installation instructions
│
├── package.json                      # Frontend dependencies
├── vite.config.ts                    # Vite configuration
├── tailwind.config.ts                # Tailwind configuration
└── README.md                         # This file
```

---

## API Documentation

### Base URL
```
http://localhost:8000/api
```

### Public Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/summary` | GET | Market overview with top stocks |
| `/api/stocks/` | GET | List all tracked stocks |
| `/api/stocks/{symbol}` | GET | Stock details with price history |
| `/api/stocks/{symbol}/analysis` | GET | Comprehensive stock analysis |
| `/api/analysis/stocks/{symbol}/sentiment` | GET | Sentiment history for stock |
| `/api/analysis/stocks/{symbol}/correlation` | GET | Price-sentiment correlation |

### Protected Endpoints (OAuth2 + TOTP)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/system/status` | GET | Comprehensive system metrics |
| `/api/admin/data-collection/trigger` | POST | Manually trigger pipeline |
| `/api/admin/scheduler/jobs` | GET | Scheduler state and job listing |
| `/api/admin/config/apis` | GET/PUT | Manage encrypted API keys |
| `/api/admin/watchlist` | GET/PUT | Manage stock watchlist |
| `/api/admin/logs` | GET | System logs with filtering |
| `/api/admin/collectors/health` | GET | Collector health status |
| `/api/admin/database/schema` | GET | Database schema explorer |
| `/api/admin/market/status` | GET | Real-time market status |

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

---

## Configuration

### Backend Environment Variables

```bash
# .env in backend/

# Application
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./data/insight_stock.db

# AI/ML (optional — for AI verification of sentiment)
GEMINI_API_KEY=your_gemini_api_key

# Data Sources
FINNHUB_API_KEY=your_finnhub_key
NEWS_API_KEY=your_newsapi_key

# Google OAuth2 (required for admin panel)
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Admin Access
ADMIN_EMAILS=admin@example.com

# Security (generate unique values!)
SECRET_KEY=your_32_char_secret
JWT_SECRET_KEY=your_jwt_secret
API_ENCRYPTION_KEY=your_encryption_key
API_ENCRYPTION_SALT=your_encryption_salt
```

### Frontend Environment Variables

```bash
# .env in project root
# SECURITY: Only NON-SECRET values belong here.
# All secrets are configured in backend/.env ONLY.

# Google OAuth2 (public client ID — safe for frontend)
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_OAUTH_REDIRECT_URI=http://localhost:8080/admin/auth/callback

# Session Configuration
VITE_SESSION_TIMEOUT=1800000
VITE_TOTP_ISSUER=Stock Market Sentiment Dashboard

# API Connection
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Development

### Running Both Servers

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```powershell
npm run dev
```

### Testing

**Backend Tests (9 phases):**
```bash
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

**Frontend Build:**
```bash
npm run build
npm run preview
```

### Code Quality

**Backend:**
```bash
black app/ tests/ --line-length 100
isort app/ tests/
flake8 app/ tests/
```

**Frontend:**
```bash
npm run lint
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Performance Metrics

### Sentiment Analysis Pipeline

| Metric | Value | Notes |
|--------|-------|-------|
| Pipeline Duration | 5-8 min | Full data collection + analysis |
| Sentiment Confidence | 91%+ | FinBERT + AI verification |
| Token Usage | 77K/run | 77% reduction via batching |
| Peak TPM | 6.5K/15K | 43% of Google Gemini limit |
| API Calls | 37/run | Down from 370 (90% reduction) |
| 429 Errors | 0 | Eliminated via TPM optimization |

### System Capacity

| Resource | Current | Maximum | Safety Margin |
|----------|---------|---------|---------------|
| Stocks Tracked | 15-20 | 40 | 2x headroom |
| Pipeline Frequency | 45 min | 15 min | 3x faster possible |
| Daily API Calls | ~500 | 14,400 | 96% available |

---

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Use PostgreSQL database
- [ ] Configure HTTPS with SSL
- [ ] Set secure `SECRET_KEY`
- [ ] Update CORS origins
- [ ] Enable log rotation
- [ ] Setup database backups
- [ ] Configure monitoring

### Production URLs

```
Frontend: https://your-domain.com
Backend API: https://api.your-domain.com
API Docs: https://api.your-domain.com/api/docs
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Backend README](backend/README.md) | Backend-specific documentation |
| [Backend Reference](docs/BACKEND_REFERENCE.md) | API and architecture details |
| [Security Setup](docs/SECURITY_IMPLEMENTATION.md) | OAuth2 + TOTP configuration |
| [Admin Security Guide](docs/ADMIN_SECURITY_SETUP.md) | Admin panel setup guide |
| [Empty State Guide](docs/EMPTY_STATE_GUIDE.md) | Handling empty database |
| [Project Structure](docs/PROJECT_STRUCTURE.md) | Frontend architecture |
| [Database Migrations](docs/DATABASE_MIGRATIONS.md) | Alembic migration guide |
| [Scheduler Guide](docs/SCHEDULER_V2_GUIDE.md) | Smart scheduler documentation |

---

## Roadmap

### v1.0.0 (Current)
- [x] Hybrid FinBERT + Gemma AI sentiment analysis
- [x] TPM optimization (77% token reduction)
- [x] Multi-factor authentication (OAuth2 + TOTP)
- [x] 45-minute automated scheduling
- [x] 5 production-ready data collectors
- [x] Comprehensive admin panel
- [x] Full frontend-backend integration
- [x] 91%+ sentiment analysis accuracy

### Future Enhancements
- [ ] WebSocket real-time updates
- [ ] GraphQL API
- [ ] Historical data backfilling
- [ ] Advanced correlation analysis
- [ ] Prometheus metrics
- [ ] Cryptocurrency sentiment
- [ ] Multi-language support
- [ ] Trading platform integration
- [ ] Mobile application

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start
1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Follow architecture patterns (5-layer backend, feature-based frontend)
4. Write tests for new features
5. Run linters before committing
6. Submit pull request with description

### Code Style
- **Python**: PEP 8, black formatting, type hints
- **TypeScript**: Strict mode, no `any`, interfaces over types
- **Commits**: Imperative mood ("Add feature" not "Added feature")

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **Hugging Face**: ProsusAI/FinBERT model
- **Google**: Gemini API for AI verification
- **shadcn**: Beautiful UI components
- **FastAPI**: Modern Python web framework
- **FYP Advisors**: Guidance and support

---

**Version**: 1.0.0  
**Last Updated**: February 12, 2026
