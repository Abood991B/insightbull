# Stock Market Sentiment Dashboard - Backend API

## Overview
FastAPI-based backend service providing real-time sentiment analysis, stock price data, and correlation analytics for technology stocks. The system collects data from multiple sources, analyzes sentiment using FinBERT and VADER, and provides RESTful APIs and WebSocket connections for the frontend dashboard.

## Technology Stack
- **Framework**: FastAPI 0.104.x with Python 3.11
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Cache**: Redis 7.x
- **Task Queue**: APScheduler (Celery ready)
- **ML Models**: 
  - FinBERT for financial news sentiment
  - VADER for social media sentiment
- **WebSocket**: Socket.IO for real-time updates
- **Authentication**: OAuth2 with JWT tokens

## Project Structure
```
backend/
├── app/
│   ├── api/
│   │   └── routes/         # API endpoint definitions
│   ├── core/              # Core functionality (database, security, etc.)
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic validation schemas
│   └── services/          # Business logic services
├── logs/                  # Application logs
├── config.py             # Configuration settings
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
└── IMPLEMENTATION_PLAN.md  # Detailed implementation guide
```

## Features
- ✅ Real-time sentiment analysis from multiple sources
- ✅ Stock price tracking and historical data
- ✅ Sentiment-price correlation analysis
- ✅ RESTful API with comprehensive endpoints
- ✅ WebSocket support for live updates
- ✅ OAuth2 authentication for admin access
- ✅ Automated data collection pipeline
- ✅ Redis caching for performance
- ✅ Comprehensive logging and monitoring

## API Endpoints

### Public Endpoints
- `GET /api/stocks` - List all tracked stocks
- `GET /api/stocks/{symbol}` - Get stock details
- `GET /api/sentiment/{symbol}` - Get sentiment data
- `GET /api/sentiment/aggregate/{symbol}` - Get aggregated sentiment
- `GET /api/prices/{symbol}` - Get historical prices
- `GET /api/correlation/{symbol}` - Get sentiment-price correlation
- `WS /ws` - WebSocket connection for real-time updates

### Admin Endpoints (Protected)
- `POST /api/auth/login` - Admin authentication
- `GET /api/admin/dashboard` - Dashboard statistics
- `GET /api/admin/model-metrics` - Model performance metrics
- `POST /api/admin/watchlist` - Manage stock watchlist
- `POST /api/admin/pipeline/trigger` - Manually trigger data collection

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Installation

#### Option 1: Using Docker Compose (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd FYP2-Dashboard

# Create .env file from example
cp .env.example .env

# Edit .env and add your API keys
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

#### Option 2: Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up PostgreSQL and Redis
# Make sure PostgreSQL is running on localhost:5432
# Make sure Redis is running on localhost:6379

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the application
uvicorn main:app --reload --port 3000
```

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/sentiment_dashboard

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# External APIs (obtain from respective providers)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
FINNHUB_API_KEY=your_finnhub_key
MARKETAUX_API_KEY=your_marketaux_key
NEWSAPI_KEY=your_newsapi_key

# OAuth2 (for admin authentication)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_secret
```

## API Documentation
Once the server is running, access the interactive API documentation at:
- Swagger UI: http://localhost:3000/api/docs
- ReDoc: http://localhost:3000/api/redoc

## Data Sources
The system collects data from:
1. **Reddit** (r/wallstreetbets, r/stocks) - Social sentiment
2. **FinnHub** - Professional financial news
3. **Marketaux** - Global financial news
4. **NewsAPI** - Mainstream media coverage
5. **Yahoo Finance** - Stock price data

## Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_sentiment.py
```

## Deployment
See `IMPLEMENTATION_PLAN.md` for detailed deployment instructions.

## Performance Targets
- API Response: < 200ms (cached), < 2s (fresh)
- Sentiment Processing: 100 texts/second
- Data Pipeline: Process 1000 articles in < 60 seconds
- Uptime: 99.9% availability

## Contributing
Please read the contribution guidelines before submitting PRs.

## License
MIT License - See LICENSE file for details
