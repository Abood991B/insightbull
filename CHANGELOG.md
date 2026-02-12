# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2025-12-01

### Added
- AI-powered sentiment analysis using FinBERT with multi-source data collection
- Real-time dashboard with TanStack Query for live stock sentiment monitoring
- Admin panel with Google OAuth2 + TOTP two-factor authentication
- Automated data collection pipeline (Finnhub, NewsAPI, GDELT, HackerNews, Yahoo Finance)
- AI verification layer using Google Gemini for sentiment cross-validation
- Interactive correlation analysis between sentiment scores and stock prices
- APScheduler-based automated collection with configurable schedules
- AES-256 encryption for API key storage
- 5-layer clean architecture (Presentation → Business → Service → Infrastructure → Data Access)
- Comprehensive admin tools: system logs, database explorer, collector health monitoring
- Market cap-based stock categorisation
- Responsive UI with shadcn/ui and Tailwind CSS

### Security
- Removed frontend-exposed secrets (OAuth client_secret, session keys, TOTP)
- Enforced backend-only OAuth token exchange
- Required environment variables for encryption (no fallback keys)
- Dynamic PBKDF2 salt from environment configuration
- Escaped SQL LIKE wildcards to prevent injection
- Replaced verbose error messages with generic responses
- Added CI/CD pipeline with TruffleHog secret scanning
- Added `.gitattributes` for consistent line endings
