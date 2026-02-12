# Insight Stock Dashboard - Backend

> FastAPI backend for the Insight Stock Dashboard. For full project documentation, see the [main README](../README.md).

## Quick Start

### Prerequisites
- Python 3.10+
- 4GB+ RAM (for ML models)

### Setup

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
alembic upgrade head

# Start server
python main.py
```

**Server runs at:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/api/docs`

---

## Environment Variables

Create `.env` file with these variables:

```bash
# Application
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./data/insight_stock.db

# AI/ML (Required)
GEMINI_API_KEY=your_gemini_api_key

# Data Sources
FINNHUB_API_KEY=your_finnhub_key
NEWS_API_KEY=your_newsapi_key
YFINANCE_ENABLED=true
GDELT_ENABLED=true
HACKERNEWS_ENABLED=true

# Security
SECRET_KEY=your_32_char_secret
ADMIN_EMAILS=admin@example.com

# Sentiment Analysis
VERIFICATION_MODE=low_confidence_and_neutral
ML_CONFIDENCE_THRESHOLD=0.90
MIN_CONFIDENCE_THRESHOLD=0.80

# Scheduler (cron: every 45 min, Mon-Fri 2-9 PM EST)
SCHEDULER_CRON=0,45 14-20 * * 0-4
SCHEDULER_TIMEZONE=America/New_York
```

---

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific phase
pytest tests/test_05_sentiment_analysis.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

**Test Phases:**
1. Security & Authentication
2. API Key Encryption
3. Collector Encryption
4. Data Collection
5. Sentiment Analysis
6. Pipeline Orchestration
7. Admin Panel
8. Integration Tests
9. Cross-Phase Tests

### Code Quality

```bash
black app/ tests/ --line-length 100
isort app/ tests/
flake8 app/ tests/ --max-line-length 100
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Project Structure

```
backend/
├── app/
│   ├── presentation/           # API routes, schemas, middleware
│   │   ├── routes/                # FastAPI route handlers
│   │   ├── controllers/           # Business logic controllers (OAuth2)
│   │   ├── schemas/           # Pydantic models
│   │   ├── middleware/        # Logging, security middleware
│   │   └── dependencies/      # Auth dependencies
│   │
│   ├── business/              # Core business logic
│   │   ├── pipeline.py        # Data collection facade
│   │   ├── scheduler.py       # APScheduler management
│   │   └── watchlist_observer.py
│   │
│   ├── service/               # Application services
│   │   ├── sentiment_processing/
│   │   │   ├── hybrid_sentiment_analyzer.py
│   │   │   ├── sentiment_engine.py
│   │   │   └── models/        # FinBERT, DistilBERT
│   │   ├── admin_service.py
│   │   ├── dashboard_service.py
│   │   └── watchlist_service.py
│   │
│   ├── infrastructure/        # External integrations
│   │   ├── collectors/        # HN, FinHub, NewsAPI, GDELT, YFinance
│   │   ├── security/          # Auth, API key encryption
│   │   ├── config/settings.py
│   │   ├── log_system.py
│   │   └── rate_limiter.py
│   │
│   ├── data_access/           # Database layer
│   │   ├── models/            # SQLAlchemy models
│   │   ├── repositories/      # Repository pattern
│   │   └── database/          # Connection, migrations, retry
│   │
│   └── utils/                 # Utilities
│       ├── sql.py
│       └── timezone.py
│
├── alembic/                   # Database migrations
├── scripts/                   # Utility scripts
├── tests/                     # 9-phase test suite
├── data/                      # Runtime data, secure keys
├── logs/                      # Application logs
├── main.py                    # Entry point
└── requirements.txt
```

---

## Debugging

### Test Sentiment Analysis

```python
python -c "
from app.service.sentiment_processing.hybrid_sentiment_analyzer import HybridSentimentAnalyzer
import asyncio

analyzer = HybridSentimentAnalyzer()
text = 'NVIDIA stock surges 15% on AI chip demand'
result = asyncio.run(analyzer.analyze(text))
print(f'{result.label}: {result.confidence:.2%}')
print(f'AI Verified: {result.ai_verified}')
"
```

### Test Pipeline

```python
python -c "
from app.business.pipeline import SentimentAnalysisPipeline
import asyncio

pipeline = SentimentAnalysisPipeline()
result = asyncio.run(pipeline.run_pipeline())
print(f'Processed: {result.summary.analyzed} texts')
"
```

### Check Database Health

```bash
python scripts/db_health_check.py
```

### Verify TPM Optimization

```bash
python scripts/verify_tpm_fix.py
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'app'` | Ensure you're in `backend/` with venv activated |
| Database migration failed | `alembic downgrade base && alembic upgrade head` |
| 429 errors from Gemini | Fixed in v1.0.0 - ensure TPM limits are configured |
| Low sentiment confidence | Set `VERIFICATION_MODE=all` in .env |
| Pipeline not running | Check scheduler: `curl http://localhost:8000/api/admin/scheduler/jobs` |

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
```

---

## API Endpoints

See full API documentation at `http://localhost:8000/api/docs` when running.

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/dashboard/summary` | Market overview |
| `GET /api/stocks/` | All tracked stocks |
| `GET /api/analysis/stocks/{symbol}/sentiment` | Stock sentiment |
| `POST /api/admin/pipeline/run` | Trigger pipeline (auth required) |
| `GET /api/admin/scheduler/jobs` | Scheduler jobs (auth required) |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `db_health_check.py` | Verify database state |
| `clear_tables.py` | Reset data (dev only) |
| `reprocess_sentiment_data.py` | Reprocess with updated model |
| `backfill_stock_mentions.py` | Backfill missing data |

---

## More Documentation

- **Full Project Docs**: [../README.md](../README.md)
- **Backend Reference**: [../docs/BACKEND_REFERENCE.md](../docs/BACKEND_REFERENCE.md)
- **Security Setup**: [../docs/SECURITY_IMPLEMENTATION.md](../docs/SECURITY_IMPLEMENTATION.md)

---

**Version**: 1.0.0
