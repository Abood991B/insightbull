# Backend Implementation Plan
## Stock Market Sentiment Dashboard: Analysis and Insights

---

## Executive Summary
This document outlines the comprehensive implementation plan for the backend system of the Stock Market Sentiment Dashboard. The backend will provide real-time sentiment analysis, stock price data, correlation analytics, and administrative management capabilities for technology stocks.

---

## 1. System Architecture Overview

### 1.1 Core Components
- **API Gateway**: RESTful API using Node.js/Express or Python/FastAPI
- **Data Pipeline**: Automated data collection and processing system
- **Sentiment Analysis Engine**: FinBERT for news, VADER for social media
- **Database Layer**: PostgreSQL for structured data, Redis for caching
- **Authentication Service**: OAuth2 with JWT tokens
- **Task Scheduler**: Celery/Bull for background jobs
- **WebSocket Server**: Real-time data updates

### 1.2 External Data Sources
- **Reddit API (PRAW)**: Social media sentiment from r/wallstreetbets, r/stocks
- **FinnHub API**: Professional financial news
- **Marketaux API**: Global financial news aggregation
- **NewsAPI**: Mainstream news coverage
- **Yahoo Finance (yfinance)**: Stock price data

---

## 2. Technology Stack

### 2.1 Backend Framework
**Option A: Python Stack (Recommended)**
- **Framework**: FastAPI 0.104.x
- **ORM**: SQLAlchemy 2.0.x
- **Task Queue**: Celery 5.3.x with Redis
- **ML/NLP**: 
  - transformers 4.35.x (FinBERT)
  - vaderSentiment 3.3.x
  - pandas 2.1.x
  - numpy 1.24.x
- **API Clients**:
  - praw 7.7.x (Reddit)
  - yfinance 0.2.x
  - requests 2.31.x
- **Authentication**: python-jose[cryptography], passlib
- **WebSocket**: python-socketio

**Option B: Node.js Stack**
- **Framework**: Express.js 4.18.x
- **ORM**: Prisma 5.x
- **Task Queue**: Bull 4.x with Redis
- **ML Integration**: Python microservice via gRPC
- **Authentication**: Passport.js
- **WebSocket**: Socket.io

### 2.2 Database
- **Primary Database**: PostgreSQL 15.x
- **Cache**: Redis 7.x
- **Time Series**: TimescaleDB extension (optional)

### 2.3 Infrastructure
- **Container**: Docker & Docker Compose
- **Process Manager**: PM2 (Node.js) or Gunicorn (Python)
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus + Grafana

---

## 3. Database Schema

### 3.1 Core Tables
```sql
-- Stocks watchlist
stocks (
  symbol VARCHAR(10) PRIMARY KEY,
  name VARCHAR(255),
  sector VARCHAR(100),
  market_cap DECIMAL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Sentiment data
sentiment_data (
  id UUID PRIMARY KEY,
  stock_symbol VARCHAR(10) REFERENCES stocks(symbol),
  source VARCHAR(50), -- 'reddit', 'finnhub', 'marketaux', 'newsapi'
  content TEXT,
  sentiment VARCHAR(20), -- 'positive', 'negative', 'neutral'
  sentiment_score FLOAT,
  confidence FLOAT,
  model_used VARCHAR(50), -- 'finbert', 'vader'
  source_url TEXT,
  published_at TIMESTAMP,
  created_at TIMESTAMP
)

-- Stock price data
price_data (
  id UUID PRIMARY KEY,
  stock_symbol VARCHAR(10) REFERENCES stocks(symbol),
  date DATE,
  open DECIMAL,
  high DECIMAL,
  low DECIMAL,
  close DECIMAL,
  volume BIGINT,
  created_at TIMESTAMP
)

-- Correlation analysis results
correlation_data (
  id UUID PRIMARY KEY,
  stock_symbol VARCHAR(10) REFERENCES stocks(symbol),
  time_window VARCHAR(10), -- '1d', '7d', '14d'
  correlation_coefficient FLOAT,
  p_value FLOAT,
  sample_size INT,
  calculated_at TIMESTAMP
)

-- Users (admin)
users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  name VARCHAR(255),
  role VARCHAR(50), -- 'admin', 'user'
  oauth_provider VARCHAR(50),
  oauth_id VARCHAR(255),
  created_at TIMESTAMP,
  last_login TIMESTAMP
)

-- API configurations
api_configs (
  id UUID PRIMARY KEY,
  name VARCHAR(100),
  endpoint VARCHAR(500),
  api_key_encrypted TEXT,
  enabled BOOLEAN DEFAULT true,
  rate_limit INT,
  last_checked TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- System logs
system_logs (
  id UUID PRIMARY KEY,
  level VARCHAR(20), -- 'info', 'warning', 'error'
  source VARCHAR(100),
  message TEXT,
  metadata JSONB,
  created_at TIMESTAMP
)

-- Model performance metrics
model_metrics (
  id UUID PRIMARY KEY,
  model_name VARCHAR(50),
  accuracy FLOAT,
  precision FLOAT,
  recall FLOAT,
  f1_score FLOAT,
  evaluation_date DATE,
  test_size INT,
  created_at TIMESTAMP
)
```

---

## 4. API Endpoints

### 4.1 Public Endpoints
```
GET /api/stocks
  - List all tracked stocks

GET /api/stocks/{symbol}
  - Get stock details with latest price

GET /api/sentiment/{symbol}
  - Get sentiment data for a stock
  - Query params: timeRange (1d, 7d, 14d), source

GET /api/sentiment/aggregate/{symbol}
  - Get aggregated sentiment scores
  - Query params: timeRange, groupBy (hour, day)

GET /api/prices/{symbol}
  - Get historical price data
  - Query params: startDate, endDate

GET /api/correlation/{symbol}
  - Get sentiment-price correlation
  - Query params: timeRange

GET /api/trends
  - Get trending stocks by sentiment

GET /api/analysis/sentiment-vs-price
  - Get combined sentiment and price data
  - Query params: symbols[], timeRange

WebSocket /ws/live-updates
  - Real-time sentiment and price updates
```

### 4.2 Admin Endpoints (Protected)
```
POST /api/auth/login
  - OAuth2 login

POST /api/auth/refresh
  - Refresh JWT token

GET /api/admin/dashboard
  - Admin dashboard statistics

GET /api/admin/model-metrics
  - Model performance metrics

POST /api/admin/api-config
  - Create/update API configuration

PUT /api/admin/api-config/{id}
  - Update specific API config

DELETE /api/admin/api-config/{id}
  - Delete API configuration

GET /api/admin/watchlist
  - Get stock watchlist

POST /api/admin/watchlist
  - Add stock to watchlist

DELETE /api/admin/watchlist/{symbol}
  - Remove stock from watchlist

GET /api/admin/storage
  - Get storage settings

PUT /api/admin/storage
  - Update storage settings

GET /api/admin/logs
  - Get system logs
  - Query params: level, startDate, endDate, limit

POST /api/admin/pipeline/trigger
  - Manually trigger data pipeline

GET /api/admin/pipeline/status
  - Get pipeline status
```

---

## 5. Data Pipeline Architecture

### 5.1 Collection Pipeline
```python
# Scheduled every 15 minutes for near-real-time updates
1. Load API configurations and watchlist
2. For each stock in watchlist:
   a. Fetch Reddit posts (PRAW)
   b. Fetch FinnHub news
   c. Fetch Marketaux articles
   d. Fetch NewsAPI articles
   e. Fetch Yahoo Finance prices
3. Handle rate limits with exponential backoff
4. Store raw data in staging tables
```

### 5.2 Processing Pipeline
```python
1. Text Preprocessing:
   - Remove URLs, emojis, special characters
   - Normalize text (lowercase, expand contractions)
   - Remove stop words (context-aware)
   
2. Sentiment Analysis:
   - FinBERT for news articles (FinnHub, Marketaux, NewsAPI)
   - VADER for Reddit posts
   - Store sentiment scores with confidence levels
   
3. Aggregation:
   - Calculate moving averages (3-day default)
   - Group by time windows (1h, 1d, 7d, 14d)
   - Calculate weighted sentiment scores
   
4. Correlation Calculation:
   - Align sentiment and price data by timestamp
   - Calculate Pearson correlation coefficient
   - Store with statistical significance (p-value)
```

### 5.3 Data Flow
```
External APIs → Raw Data Store → Preprocessing → 
Sentiment Analysis → Aggregation → API/WebSocket → Frontend
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Set up development environment
- [ ] Initialize backend project structure
- [ ] Configure Docker containers
- [ ] Set up PostgreSQL and Redis
- [ ] Implement database schema
- [ ] Create base API structure

### Phase 2: Authentication & Admin (Week 3)
- [ ] Implement OAuth2 authentication
- [ ] Set up JWT token management
- [ ] Create admin middleware
- [ ] Implement user management
- [ ] Build admin API endpoints

### Phase 3: Data Collection (Week 4-5)
- [ ] Integrate Reddit API (PRAW)
- [ ] Integrate FinnHub API
- [ ] Integrate Marketaux API
- [ ] Integrate NewsAPI
- [ ] Integrate Yahoo Finance
- [ ] Implement rate limiting
- [ ] Create data collection scheduler

### Phase 4: Sentiment Analysis (Week 6-7)
- [ ] Set up FinBERT model
- [ ] Configure VADER sentiment analyzer
- [ ] Implement text preprocessing pipeline
- [ ] Create sentiment analysis service
- [ ] Build model evaluation metrics
- [ ] Optimize for performance

### Phase 5: Data Processing & Analytics (Week 8-9)
- [ ] Implement data aggregation logic
- [ ] Create correlation calculation service
- [ ] Build trending analysis algorithms
- [ ] Implement caching strategies
- [ ] Create data validation layer

### Phase 6: API Development (Week 10-11)
- [ ] Implement all public endpoints
- [ ] Build WebSocket server
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Implement error handling
- [ ] Add request validation
- [ ] Set up CORS configuration

### Phase 7: Integration & Testing (Week 12-13)
- [ ] Connect frontend to backend
- [ ] Write unit tests (80% coverage target)
- [ ] Create integration tests
- [ ] Perform load testing
- [ ] Fix bugs and optimize performance
- [ ] Update frontend API calls

### Phase 8: Deployment & Documentation (Week 14)
- [ ] Set up production environment
- [ ] Configure CI/CD pipeline
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Write deployment documentation
- [ ] Create user guide
- [ ] Final testing and bug fixes

---

## 7. Key Implementation Details

### 7.1 Rate Limiting Strategy
```python
# Example implementation
rate_limits = {
    'reddit': {'calls': 60, 'period': 60},  # 60 calls/minute
    'finnhub': {'calls': 60, 'period': 60},
    'marketaux': {'calls': 100, 'period': 86400},  # 100/day (free tier)
    'newsapi': {'calls': 100, 'period': 86400}
}

# Implement token bucket or sliding window algorithm
# Use Redis for distributed rate limiting
```

### 7.2 Caching Strategy
- Cache sentiment scores for 15 minutes
- Cache price data for 5 minutes during market hours
- Cache correlation results for 1 hour
- Use Redis with appropriate TTL values

### 7.3 Error Handling
- Comprehensive logging at all levels
- Graceful degradation for API failures
- Retry mechanism with exponential backoff
- Dead letter queue for failed processing

### 7.4 Security Measures
- API key encryption using AES-256
- Rate limiting per IP/user
- Input validation and sanitization
- SQL injection prevention via ORM
- XSS protection headers
- HTTPS enforcement

---

## 8. Performance Targets

- **API Response Time**: < 200ms for cached data, < 2s for fresh calculations
- **Data Pipeline**: Process 1000 articles in < 60 seconds
- **Sentiment Analysis**: 100 texts/second throughput
- **Concurrent Users**: Support 100+ concurrent connections
- **Uptime**: 99.9% availability
- **Data Freshness**: 15-minute maximum lag

---

## 9. Monitoring & Maintenance

### 9.1 Metrics to Track
- API response times
- Pipeline execution times
- Sentiment analysis accuracy
- Database query performance
- Cache hit rates
- Error rates by source

### 9.2 Alerts
- API failure rate > 1%
- Pipeline failure
- Database connection issues
- High memory/CPU usage
- Rate limit approaching

---

## 10. Future Enhancements

1. **Machine Learning Improvements**
   - Fine-tune FinBERT on financial data
   - Implement ensemble models
   - Add sarcasm detection for Reddit

2. **Additional Features**
   - Portfolio tracking
   - Trading signals generation
   - News summarization
   - Multi-language support

3. **Scalability**
   - Kubernetes deployment
   - Microservices architecture
   - GraphQL API option
   - Real-time streaming with Kafka

---

## 11. Resources & Dependencies

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [FinBERT Paper](https://arxiv.org/abs/1908.10063)
- [VADER Documentation](https://github.com/cjhutto/vaderSentiment)

### API Keys Required
- Reddit API (via Reddit App)
- FinnHub API Key
- Marketaux API Key
- NewsAPI Key
- Google OAuth2 credentials (for admin)

---

## 12. Success Criteria

- [ ] All frontend pages display real data (no mock data)
- [ ] Sentiment analysis accuracy > 75%
- [ ] Correlation calculations are statistically significant
- [ ] Admin can manage all system configurations
- [ ] System handles API rate limits gracefully
- [ ] Real-time updates work via WebSocket
- [ ] Documentation is complete and accurate

---

*Last Updated: December 2024*
*Version: 1.0.0*
