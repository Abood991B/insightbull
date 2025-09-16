# Insight Stock Dashboard Backend

## Overview

Backend API for the Insight Stock Dashboard - a sentiment analysis and stock market insights platform. Built with FastAPI following a 5-layer architecture pattern as specified in the FYP report.

## Architecture

The backend implements a clean 5-layer architecture:

- **Presentation Layer**: FastAPI controllers, middleware, and request/response schemas
- **Business Layer**: Use cases and domain entities containing business logic
- **Infrastructure Layer**: External APIs, sentiment analysis models, and configuration
- **Service Layer**: Application services for data collection and sentiment processing  
- **Data Access Layer**: Database models, repositories, and data persistence

## Features

- Real-time sentiment analysis using FinBERT and VADER models
- Multi-source data collection (Reddit, FinHub, NewsAPI, Marketaux)
- RESTful API with automatic OpenAPI documentation
- Async/await support for high performance
- Structured logging with correlation IDs
- Database migrations with Alembic
- Comprehensive error handling and validation

## Technology Stack

- **Framework**: FastAPI 0.115.0
- **Database**: PostgreSQL with SQLAlchemy 2.0.36 (async)
- **Sentiment Analysis**: Transformers (FinBERT), VADER
- **Task Queue**: Celery with Redis
- **Migration**: Alembic 1.13.3
- **Testing**: Pytest with async support
- **Code Quality**: Black, isort, flake8

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis (for background tasks)

### Setup

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   setup_env.bat
   
   # Linux/Mac
   chmod +x setup_env.sh
   ./setup_env.sh
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Setup database**
   ```bash
   # Activate virtual environment first
   # Windows: venv\Scripts\activate.bat
   # Linux/Mac: source venv/bin/activate
   
   alembic upgrade head
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/api/docs`.

## API Endpoints

### Dashboard
- `GET /api/v1/dashboard/overview` - Get dashboard overview data
- `GET /api/v1/dashboard/health` - Dashboard service health check

### Sentiment Analysis  
- `GET /api/v1/sentiment/trends` - Get sentiment trends for stocks
- `GET /api/v1/sentiment/analysis/{stock_symbol}` - Get detailed sentiment analysis

### Admin
- `GET /api/v1/admin/system-status` - Get system status
- `GET /api/v1/admin/logs` - Get system logs
- `POST /api/v1/admin/data-collection/trigger` - Trigger data collection

### Health
- `GET /health` - Application health check

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black app/
isort app/
flake8 app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `FINNHUB_API_KEY`: FinHub API key for stock data
- `MARKETAUX_API_KEY`: Marketaux API key for news
- `NEWS_API_KEY`: NewsAPI key for news articles
- `REDDIT_CLIENT_ID`: Reddit API client ID
- `REDDIT_CLIENT_SECRET`: Reddit API client secret
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key

## Project Structure

```
backend/
├── app/
│   ├── presentation/          # FastAPI controllers, middleware, schemas
│   ├── business/              # Use cases and domain entities  
│   ├── infrastructure/        # External APIs, config, sentiment models
│   ├── service/              # Application services
│   └── data_access/          # Database models and repositories
├── migrations/               # Database migrations
├── tests/                   # Unit and integration tests
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── alembic.ini            # Alembic configuration
```

## Design Patterns

The backend implements several design patterns from the FYP specification:

- **Facade Pattern**: `SentimentAnalysisPipeline` provides unified interface
- **Strategy Pattern**: `SentimentModel` with FinBERT/VADER implementations  
- **Singleton Pattern**: `LogSystem` for centralized logging
- **Observer Pattern**: Real-time dashboard updates
- **Adapter Pattern**: External API data source adapters

## Contributing

1. Follow the 5-layer architecture
2. Write tests for new features
3. Use structured logging
4. Update documentation
5. Follow code style guidelines

## License

This project is part of an FYP (Final Year Project) submission.