# Backend Implementation Plan
## Stock Market Sentiment Dashboard

### Overview
This document outlines the comprehensive implementation plan for the backend system of the Stock Market Sentiment Dashboard. The plan is structured in phases to ensure systematic development, testing, and integration with the existing frontend.

---

## Phase 1: Foundation Setup (Week 1)

### 1.1 Project Structure Creation (Following 5-Layer Architecture)

**Architecture Mapping**: This structure implements the **Layered Architecture** from the FYP report with clear separation of concerns across 5 distinct layers.

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Configuration management
│   │   └── database.py         # Database connection setup
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Security utilities
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── logging.py          # Logging configuration (Singleton pattern)
│   ├── business/               # LAYER 2: BUSINESS LAYER (Core Orchestration)
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Pipeline class (Facade pattern) - Main orchestrator
│   │   ├── scheduler.py        # Scheduler for automated jobs
│   │   ├── data_collector.py   # DataCollector coordinator
│   │   └── processor.py        # Text preprocessing and data cleaning
│   ├── presentation/           # LAYER 1: PRESENTATION LAYER
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py    # Dashboard endpoints (like Dashboard class)
│   │   │   ├── stocks.py       # Stock endpoints (like Visualizer)
│   │   │   ├── analysis.py     # Analysis endpoints (like CorrelationCalculator)
│   │   │   ├── admin.py        # Admin endpoints (like Watchlist)
│   │   │   └── pipeline.py     # Pipeline management endpoints
│   │   ├── schemas/            # Pydantic response models
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py    # Dashboard response schemas
│   │   │   ├── stock.py        # Stock response schemas
│   │   │   ├── analysis.py     # Analysis response schemas
│   │   │   └── admin.py        # Admin response schemas
│   │   └── deps.py             # Route dependencies
│   ├── infrastructure/         # LAYER 3: INFRASTRUCTURE LAYER
│   │   ├── __init__.py
│   │   ├── collectors/         # External data collectors
│   │   │   ├── __init__.py
│   │   │   ├── base_collector.py
│   │   │   ├── reddit_collector.py    # RedditCollector
│   │   │   ├── finnhub_collector.py   # FinHubCollector  
│   │   │   ├── newsapi_collector.py   # NewsAPICollector
│   │   │   └── marketaux_collector.py # MarketauxCollector
│   │   ├── api_key_manager.py  # APIKeyManager for secure credentials
│   │   ├── rate_limiter.py     # RateLimitHandler for API throttling
│   │   └── log_system.py       # LogSystem (Singleton pattern)
│   ├── service/                # LAYER 4: SERVICE LAYER (Analytical Intelligence)
│   │   ├── __init__.py
│   │   ├── sentiment_engine.py     # SentimentEngine orchestration
│   │   ├── sentiment_model.py      # SentimentModel interface (Strategy pattern)
│   │   ├── vader_model.py          # VADERModel implementation
│   │   ├── finbert_model.py        # FinBERTModel implementation
│   │   ├── correlation_service.py  # Correlation calculations
│   │   └── analysis_service.py     # General analysis services
│   ├── data_access/            # LAYER 5: DATA ACCESS LAYER
│   │   ├── __init__.py
│   │   ├── models/             # SQLAlchemy models (domain entities)
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Base model class
│   │   │   ├── stock.py        # Stock entity
│   │   │   ├── sentiment.py    # SentimentRecord entity
│   │   │   └── stock_price.py  # StockPrice entity
│   │   ├── repositories/       # Data access repositories
│   │   │   ├── __init__.py
│   │   │   ├── stock_repository.py
│   │   │   ├── sentiment_repository.py
│   │   │   └── price_repository.py
│   │   └── storage_manager.py  # StorageManager for data operations
│   │
│   ├── utils/                  # Cross-cutting utilities
│   │   ├── __init__.py
│   │   ├── crypto.py           # Encryption utilities
│   │   ├── validators.py       # Input validation
│   │   └── helpers.py          # General utilities
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py         # Test fixtures
│       ├── test_api/
│       ├── test_services/
│       ├── test_pipeline/
│       └── test_models/
├── requirements/
│   ├── base.txt               # Core dependencies
│   ├── dev.txt                # Development dependencies
│   └── prod.txt               # Production dependencies
├── scripts/
│   ├── init_db.py             # Database initialization
│   ├── seed_data.py           # Sample data seeding
│   └── run_pipeline.py        # Manual pipeline execution
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── alembic/                   # Database migrations
├── .env.example
├── .gitignore
├── README.md
└── pyproject.toml
```

### 1.2 Architecture Layer Mapping

This implementation strictly follows the **5-Layer Architecture** from your FYP Report:

#### Layer 1: Presentation Layer (`app/presentation/`)
- **Routes**: FastAPI endpoints for dashboard, stocks, analysis, admin
- **Schemas**: Pydantic response models for API serialization
- **Dependencies**: Route-level dependencies and validation
- **Maps to**: Dashboard, Visualizer, CorrelationCalculator, Watchlist components

#### Layer 2: Business Layer (`app/business/`)
- **Pipeline**: Central Facade pattern orchestrator (main controller)
- **Scheduler**: Automated job scheduling and triggers
- **DataCollector**: Coordinates data collection from multiple sources
- **Processor**: Text preprocessing and data cleaning operations
- **Maps to**: Core orchestration logic from FYP design

#### Layer 3: Infrastructure Layer (`app/infrastructure/`)
- **Collectors**: RedditCollector, FinHubCollector, NewsAPICollector, MarketauxCollector
- **APIKeyManager**: Secure external API credential management
- **RateLimitHandler**: API throttling and backoff strategies
- **LogSystem**: Centralized logging using Singleton pattern
- **Maps to**: External system integration from FYP design

#### Layer 4: Service Layer (`app/service/`)
- **SentimentEngine**: Sentiment analysis orchestration
- **SentimentModel**: Strategy pattern interface for model abstraction
- **VADERModel & FinBERTModel**: Concrete sentiment analysis implementations
- **CorrelationService**: Statistical analysis services
- **Maps to**: Analytical intelligence layer from FYP design

#### Layer 5: Data Access Layer (`app/data_access/`)
- **Models**: SQLAlchemy entities (Stock, SentimentRecord, StockPrice)
- **Repositories**: Data access patterns for each entity
- **StorageManager**: Database operations and persistence
- **Maps to**: Data persistence and domain models from FYP design

### 1.3 Design Patterns Implementation

Following the FYP Report specifications:

- **Facade Pattern**: `Pipeline` class orchestrates complex workflows
- **Strategy Pattern**: `SentimentModel` interface with VADER/FinBERT implementations
- **Singleton Pattern**: `LogSystem` for consistent system-wide logging  
- **Observer Pattern**: Dashboard updates on data changes (via polling)
- **Adapter Pattern**: Standardized collector interfaces for different APIs

### 1.4 Core Dependencies Setup
```bash
# Base requirements (requirements/base.txt)
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
sqlalchemy==2.0.35
alembic==1.13.3
psycopg2-binary==2.9.9
redis==5.1.1
celery==5.4.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
httpx==0.27.2

# Data processing
pandas==2.2.3
numpy==2.1.1
scikit-learn==1.5.2

# Sentiment Analysis
transformers==4.45.2
torch==2.4.1
nltk==3.9.1
beautifulsoup4==4.12.3

# Data collection
praw==7.8.1
finnhub-python==2.4.20
newsapi-python==0.2.7
requests==2.32.3
yfinance==0.2.43

# Utilities
python-dotenv==1.0.1
cryptography==43.0.1
apscheduler==3.10.4
loguru==0.7.2

# Development requirements (requirements/dev.txt)
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
black==24.8.0
ruff==0.6.8
mypy==1.11.2
pre-commit==3.8.0
```

### 1.5 Configuration Management
Create environment-based configuration system with proper secret management.

### 1.6 Database Setup
- PostgreSQL database schema creation
- Alembic migration setup
- Connection pooling configuration

### 1.7 Logging and Monitoring
- Structured logging with Loguru (implements LogSystem Singleton from FYP)
- Error tracking setup
- Performance monitoring foundations

---

## Phase 2: Security & Middleware (Week 2)

### 2.1 Admin Authentication Integration
- **Backend Integration**: Connect with existing frontend TOTP system
- **JWT Token Validation**: Validate tokens from frontend auth
- **Session Management**: Support existing session handling

#### Key Components:
```python
# app/services/auth_service.py
class AuthService:
    async def validate_admin_token(token: str) -> bool
    async def get_admin_from_token(token: str) -> AdminUser
    async def verify_admin_permissions(admin_id: str) -> bool
```

### 2.2 Security Middleware
- **Rate Limiting**: Per-IP limits for API endpoints
- **CORS Configuration**: Frontend origin whitelisting
- **Input Validation**: Comprehensive request sanitization
- **API Key Encryption**: Secure storage of external API keys (Reddit, FinHub, etc.)

### 2.3 Admin Route Protection
- **Route Guards**: Protect admin endpoints only (user endpoints are public)
- **Token Validation**: Validate admin JWT tokens
- **Activity Logging**: Admin action tracking

---

## Phase 3: Data Models & Database (Week 3)

**FYP Alignment**: This phase implements the data model to support all functional requirements (U-FR1 through U-FR10 and SY-FR1 through SY-FR9) from the FYP Report.

**Note**: The database schema will be designed for optimal performance and simplicity, prioritizing practical implementation over strict adherence to the original ERD. The models below represent a streamlined approach focused on core functionality.

### 3.1 SQLAlchemy Models Implementation

#### Stock Model
```python
class Stock(Base):
    __tablename__ = "stocks"
    
    symbol = Column(String(10), primary_key=True)
    company_name = Column(String(100), nullable=False)
    sector = Column(String(50))  # Technology, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sentiment_records = relationship("SentimentRecord", back_populates="stock")
    price_data = relationship("StockPrice", back_populates="stock")
```

#### SentimentRecord Model  
```python
class SentimentRecord(Base):
    __tablename__ = "sentiment_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_symbol = Column(String(10), ForeignKey("stocks.symbol"), nullable=False)
    source = Column(String(20), nullable=False)  # Reddit, FinHub, etc.
    content_type = Column(String(20))  # post, comment, article, headline
    timestamp = Column(DateTime, nullable=False)
    score = Column(Float, nullable=False)  # Normalized -1.0 to 1.0
    label = Column(String(10), nullable=False)  # Positive, Neutral, Negative
    confidence = Column(Float)  # Model confidence score
    text_snippet = Column(Text)  # First 500 chars for reference
    source_url = Column(String(500))  # Original source URL if available
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="sentiment_records")
```

#### StockPrice Model (Simplified - no complex job tracking)
```python
class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_symbol = Column(String(10), ForeignKey("stocks.symbol"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float)
    close_price = Column(Float, nullable=False)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(BigInteger)
    source = Column(String(20), default="yfinance")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="price_data")
```

### 3.2 Database Migrations
- Initial schema creation with flexible design
- Performance indexes on frequently queried fields
- Simple relationships focused on core functionality

### 3.3 Data Access Layer
- Simple repository pattern for data operations
- Query optimization for dashboard performance
- Connection pooling for scalability
- Flexible schema that can evolve with requirements

---

## Phase 4: Core API Endpoints (Week 4)

**FYP Functional Requirements Implementation**: This phase implements all User Functional Requirements (U-FR1 to U-FR5) for public access.

### 4.1 User Dashboard Endpoints

#### GET /api/dashboard/summary (Implements U-FR1: View Sentiment Dashboard)
```python
@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard overview with key metrics - Implements U-FR1"""
    # Top performing stocks by sentiment
    # Recent price changes  
    # Overall market sentiment
    # System status
```

#### GET /api/stocks (Implements U-FR3: Filter by Stock)
```python
@router.get("/", response_model=List[StockSummary])
async def get_all_stocks(
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Get all tracked stocks with latest data - Implements U-FR3"""
```

#### GET /api/stocks/{symbol} (Implements U-FR2: Select Time Range + U-FR3: Filter by Stock)
```python
@router.get("/{symbol}", response_model=StockDetail)
async def get_stock_detail(
    symbol: str,
    timeframe: str = Query("7d", regex="^(1d|7d|14d)$"),  # U-FR2: 1d, 7d, 14d
    db: Session = Depends(get_db)
):
    """Get detailed stock information - Implements U-FR2 & U-FR3"""
```

### 4.2 Analysis Endpoints

#### GET /api/stocks/{symbol}/sentiment (Implements U-FR4: Compare Sentiment vs Price)
```python
@router.get("/{symbol}/sentiment", response_model=SentimentHistory)
async def get_sentiment_history(
    symbol: str,
    timeframe: str = Query("7d"),
    limit: int = Query(100),
    db: Session = Depends(get_db)
):
    """Get sentiment history for dual-axis visualization - Implements U-FR4"""
```

#### GET /api/stocks/{symbol}/correlation (Implements U-FR5: Dynamic Correlation Analysis)
```python
@router.get("/{symbol}/correlation", response_model=CorrelationAnalysis)
async def get_correlation_analysis(
    symbol: str,
    timeframe: str = Query("7d"),
    db: Session = Depends(get_db)
):
    """Get real-time Pearson correlation calculation - Implements U-FR5"""
```

### 4.3 Response Schemas
Define comprehensive Pydantic schemas for all endpoints with proper validation and documentation.

---

## Phase 5: Data Collection Pipeline (Week 5-6)

**FYP System Requirements Implementation**: This phase implements SY-FR1 (Data Collection Pipeline), SY-FR2 (Preprocess Raw Data), and SY-FR6 (Handle API Rate Limits) from the FYP Report.

**FYP Data Sources**: Implements multi-source collection from Reddit (PRAW), FinHub, Marketaux, and NewsAPI as specified in the theoretical framework.

### 5.1 Base Collector Interface
```python
from abc import ABC, abstractmethod

class BaseCollector(ABC):
    def __init__(self, api_key: str, rate_limiter: RateLimiter):
        self.api_key = api_key
        self.rate_limiter = rate_limiter
    
    @abstractmethod
    async def collect_data(self, symbols: List[str], date_range: DateRange) -> List[RawData]:
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        pass
```

### 5.2 Specific Collectors Implementation

#### Reddit Collector (PRAW)
```python
class RedditCollector(BaseCollector):
    async def collect_data(self, symbols: List[str], date_range: DateRange):
        # Search finance subreddits
        # Filter by stock symbols
        # Extract post titles and text
        # Return structured data
```

#### Financial News Collectors
- **FinHub Collector**: Company-specific news
- **NewsAPI Collector**: General financial news
- **Marketaux Collector**: Market news aggregation

### 5.3 Data Processing Pipeline
```python
class DataPipeline:
    def __init__(self):
        self.collectors = [
            RedditCollector(), FinHubCollector(), 
            NewsAPICollector(), MarketauxCollector()
        ]
        self.processors = [TextProcessor(), TimestampNormalizer()]
        self.sentiment_engine = SentimentEngine()
        self.storage_manager = StorageManager()
    
    async def run_pipeline(self, job_config: JobConfig) -> JobResult:
        # 1. Data Collection
        # 2. Data Preprocessing  
        # 3. Sentiment Analysis
        # 4. Data Storage
        # 5. Logging and monitoring
```

### 5.4 Text Preprocessing
- **HTML/Markdown cleanup**: BeautifulSoup processing
- **URL removal**: Regex-based cleaning
- **Noise removal**: Special characters, excessive whitespace
- **Timestamp normalization**: UTC ISO format standardization

---

## Phase 6: Sentiment Analysis Engine (Week 7)

**FYP Dual-Model Implementation**: This phase implements SY-FR3 (Perform Sentiment Analysis) using the dual-model approach specified in the FYP Report: **FinBERT for financial news** and **VADER for social media**.

**Strategy Pattern**: Implements the Strategy design pattern for interchangeable sentiment models as specified in the FYP architecture.

### 6.1 Sentiment Model Interface
```python
class SentimentModel(ABC):
    @abstractmethod
    async def analyze(self, texts: List[str]) -> List[SentimentResult]:
        pass
    
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        pass
```

### 6.2 VADER Implementation
```python
class VADERModel(SentimentModel):
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
    
    async def analyze(self, texts: List[str]) -> List[SentimentResult]:
        # Process social media text
        # Return sentiment scores and labels
        # Handle batch processing
```

### 6.3 FinBERT Implementation
```python
class FinBERTModel(SentimentModel):
    def __init__(self):
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "ProsusAI/finbert"
        )
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    
    async def analyze(self, texts: List[str]) -> List[SentimentResult]:
        # Process financial news text
        # GPU acceleration support
        # Batch inference optimization
```

### 6.4 Sentiment Engine Orchestration
```python
class SentimentEngine:
    def __init__(self):
        self.models = {
            "reddit": VADERModel(),
            "news": FinBERTModel()
        }
    
    async def process_batch(self, data_batch: List[RawData]) -> List[SentimentRecord]:
        # Route data to appropriate model
        # Process in batches for efficiency
        # Handle errors and retries
```

---

## Phase 7: Job Scheduling & Background Tasks (Week 8)

### 7.1 Celery Task Setup
```python
# Celery configuration
from celery import Celery

celery_app = Celery(
    "sentiment_dashboard",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
async def run_data_collection_pipeline():
    """Background task for data collection"""
    # Execute full pipeline
    # Handle errors and retries
    # Update job status
```

### 7.2 APScheduler Integration
```python
class PipelineScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    async def start(self):
        # Schedule hourly data collection
        # Schedule daily correlation analysis
        # Schedule weekly model evaluation
```

### 7.3 Job Management
- **Job Status Tracking**: Running, completed, failed states
- **Error Handling**: Retry mechanisms with exponential backoff
- **Resource Management**: Memory and CPU monitoring
- **Queue Management**: Priority-based task execution

---

## Phase 8: Admin Panel Backend (Week 9)

**FYP Admin Requirements Implementation**: This phase implements U-FR6 through U-FR10 (Admin-only functional requirements) for system management and configuration.

### 8.1 Admin Authentication Integration (Backend validation for existing frontend auth)
```python
@router.post("/admin/auth/validate")
async def validate_admin_token(token: AdminToken)

@router.get("/admin/auth/verify")
async def verify_admin_session(current_admin: Admin = Depends(get_current_admin))

@router.post("/admin/auth/refresh") 
async def refresh_admin_token(refresh_data: RefreshToken)
```

### 8.2 System Management Endpoints (FYP Admin Requirements)
```python
@router.get("/admin/models/accuracy")  # Implements U-FR6: Evaluate Model Accuracy
async def get_model_accuracy(current_admin: Admin = Depends(get_current_admin))

@router.put("/admin/config/apis")      # Implements U-FR7: Configure API Keys  
async def update_api_config(
    config: APIConfig,
    current_admin: Admin = Depends(get_current_admin)
)

@router.put("/admin/watchlist")        # Implements U-FR8: Update Stock Watchlist
async def update_stock_watchlist(
    watchlist: WatchlistConfig,
    current_admin: Admin = Depends(get_current_admin)
)

@router.put("/admin/storage")          # Implements U-FR9: Manage Data Storage
async def update_storage_settings(
    settings: StorageConfig,
    current_admin: Admin = Depends(get_current_admin)
)

@router.get("/admin/logs")             # Implements U-FR10: View System Logs
async def get_system_logs(
    filters: LogFilters,
    current_admin: Admin = Depends(get_current_admin)
)
```

### 8.3 Data Management
- **Watchlist Management**: Add/remove stocks
- **Storage Configuration**: Database settings
- **Backup Management**: Data export/import
- **Performance Monitoring**: System metrics

---

## Phase 9: Integration & Testing (Week 10-11)

### 9.1 API Integration Testing
- **Endpoint Testing**: All API routes with various scenarios
- **Authentication Flow**: Complete OAuth2 + TOTP testing
- **Error Handling**: Edge cases and failure scenarios
- **Performance Testing**: Load testing and optimization

### 9.2 Pipeline Testing
```python
# test_pipeline.py
@pytest.mark.asyncio
async def test_full_pipeline_execution():
    # Test complete data flow
    # Verify data quality
    # Check error handling
    
@pytest.mark.asyncio
async def test_sentiment_analysis_accuracy():
    # Test model predictions
    # Validate against ground truth
    # Performance benchmarking
```

### 9.3 Frontend Integration
- **API Client Testing**: Verify all frontend calls work
- **Data Format Validation**: Ensure response schemas match frontend expectations
- **Real-time Updates**: Test polling and data refresh
- **Error Handling**: Frontend error display integration
- **Public Endpoints**: Ensure user dashboard works without authentication

### 9.4 Security Testing
- **Admin Authentication**: Test admin token validation and session management
- **Public Access**: Verify user endpoints work without authentication
- **Input Validation**: SQL injection and XSS prevention
- **Rate Limiting**: API abuse prevention for both public and admin endpoints

---

## Phase 10: Performance Optimization (Week 12)

### 10.1 Database Optimization
- **Query Optimization**: Analyze slow queries
- **Index Strategy**: Create optimal indexes
- **Connection Pooling**: Optimize database connections
- **Caching Layer**: Redis implementation for frequent queries

### 10.2 API Performance
- **Response Caching**: Cache expensive computations
- **Async Optimization**: Improve concurrent processing
- **Rate Limiting**: Implement intelligent throttling
- **Compression**: Gzip response compression

### 10.3 Pipeline Optimization
- **Batch Processing**: Optimize batch sizes
- **Parallel Processing**: Multi-threading implementation
- **Memory Management**: Optimize memory usage
- **API Rate Limit Handling**: Efficient retry strategies

---

## Phase 11: Deployment Preparation (Week 13)

### 11.1 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements/ requirements/
RUN pip install -r requirements/prod.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 11.2 Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sentiment_db
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: sentiment_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    
  celery:
    build: .
    command: celery -A app.main.celery_app worker --loglevel=info
    depends_on:
      - db
      - redis
```

### 11.3 Environment Configuration
- **Production Settings**: Database connections, security keys
- **Environment Variables**: All sensitive data externalized
- **Health Checks**: Application health monitoring
- **Logging Configuration**: Production logging setup

### 11.4 Migration Scripts
- **Database Migration**: Automated schema updates
- **Data Migration**: Existing data transformation
- **Rollback Procedures**: Safe deployment rollbacks

---

## Phase 12: Documentation & Final Testing (Week 14)

### 12.1 API Documentation
- **OpenAPI/Swagger**: Complete API documentation
- **Usage Examples**: Code samples for all endpoints
- **Error Codes**: Comprehensive error documentation
- **Rate Limits**: API usage guidelines

### 12.2 Deployment Documentation
- **Setup Guide**: Step-by-step deployment instructions
- **Configuration Guide**: Environment setup and tuning
- **Monitoring Guide**: System monitoring and alerting
- **Troubleshooting Guide**: Common issues and solutions

### 12.3 Code Documentation
- **Inline Documentation**: Comprehensive code comments
- **Architecture Documentation**: System design explanation
- **Database Schema**: Complete schema documentation
- **API Reference**: Detailed endpoint documentation

### 12.4 Final Integration Testing
- **End-to-End Testing**: Complete user journey testing
- **Load Testing**: Production-level load simulation
- **Security Audit**: Final security assessment
- **Performance Benchmarking**: Production readiness validation

---

## Technology Stack Summary

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool

### Database & Caching
- **PostgreSQL**: Primary database for data persistence
- **Redis**: Caching layer and message broker
- **Connection Pooling**: Optimized database connections

### Authentication & Security
- **Python-JOSE**: JWT token handling
- **Passlib**: Password hashing
- **Cryptography**: Encryption utilities
- **OAuth2**: Google authentication integration

### Data Processing & ML
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Scikit-learn**: Machine learning utilities
- **Transformers**: Hugging Face NLP models
- **PyTorch**: Deep learning framework
- **NLTK**: Natural language toolkit

### Data Collection
- **PRAW**: Reddit API wrapper
- **Financial APIs**: FinHub, NewsAPI, Marketaux clients
- **YFinance**: Stock price data
- **Requests**: HTTP client library

### Background Processing
- **Celery**: Distributed task queue
- **APScheduler**: Job scheduling
- **Redis**: Message broker

### Development & Testing
- **Pytest**: Testing framework
- **Black**: Code formatting
- **Flake8**: Code linting
- **MyPy**: Static type checking
- **Pre-commit**: Git hooks

### Deployment
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Uvicorn**: ASGI server
- **Gunicorn**: Production WSGI server

---

## Success Metrics

### Performance Targets
- **API Response Time**: < 500ms for 95% of requests
- **Database Query Time**: < 100ms for simple queries
- **Pipeline Execution**: Complete daily update in < 30 minutes
- **Concurrent Users**: Support 100+ simultaneous users

### Quality Targets
- **Test Coverage**: > 90% code coverage
- **API Uptime**: > 99.5% availability
- **Data Accuracy**: > 95% sentiment classification accuracy
- **Error Rate**: < 1% API error rate

### Security Targets
- **Authentication**: Multi-factor authentication for admin
- **Data Encryption**: All sensitive data encrypted at rest
- **API Security**: Rate limiting and input validation
- **Audit Trail**: Complete activity logging

---

## Risk Mitigation

### Technical Risks
- **API Rate Limits**: Implement intelligent retry mechanisms
- **Model Performance**: Continuous model evaluation and retraining
- **Data Quality**: Comprehensive validation and cleaning
- **Scalability**: Horizontal scaling architecture

### Operational Risks
- **Dependency Management**: Pin all dependency versions
- **Database Backup**: Automated daily backups
- **Monitoring**: Comprehensive application monitoring
- **Documentation**: Maintain up-to-date documentation

### Security Risks
- **Access Control**: Role-based permissions
- **Data Protection**: Encryption and secure storage
- **Input Validation**: Prevent injection attacks
- **Audit Logging**: Track all system activities

This comprehensive implementation plan provides a structured approach to building a robust, scalable, and secure backend system that fully integrates with the existing frontend while meeting all requirements outlined in the FYP Report.