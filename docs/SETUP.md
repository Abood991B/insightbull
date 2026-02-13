# Setup Instructions

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Git**
- **4GB+ RAM** (required for ML models)

---

## 1. Clone Repository

```bash
git clone https://github.com/Abood991B/insightbull.git
cd insightbull
```

---

## 2. Backend Setup

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
# Edit .env with your API keys (FINNHUB_API_KEY, NEWS_API_KEY, GEMINI_API_KEY, etc.)

# Initialize database
alembic upgrade head

# Start server
python main.py
```

**Backend runs at:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/api/docs`

### Backend Environment Variables

Create `backend/.env` from `backend/.env.example`. Key variables:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/insight_stock.db

# Data Sources (required for data collection)
FINNHUB_API_KEY=your_finnhub_api_key
NEWS_API_KEY=your_newsapi_key

# AI Verification (optional)
GEMINI_API_KEY=your_gemini_api_key

# Google OAuth2 (required for admin panel)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Admin Access
ADMIN_EMAILS=admin@example.com

# Security (generate unique values!)
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
API_ENCRYPTION_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">
API_ENCRYPTION_SALT=<generate: python -c "import secrets; print(secrets.token_hex(16))">
```

> See `backend/.env.example` for the full list of configuration options.

---

## 3. Frontend Setup

```powershell
# From project root (not backend/)
cd ..

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your VITE_GOOGLE_CLIENT_ID

# Start development server
npm run dev
```

**Frontend runs at:** `http://localhost:8080`

### Frontend Environment Variables

Create `.env` in the project root from `.env.example`:

```bash
# Google OAuth2 (public client ID — safe for frontend)
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_OAUTH_REDIRECT_URI=http://localhost:8080/admin/auth/callback

# Session timeout (milliseconds)
VITE_SESSION_TIMEOUT=1800000

# API Connection
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> **Security note:** All secrets (OAuth client_secret, session keys, admin emails) are configured in `backend/.env` only. The frontend `.env` contains only non-secret values.

---

## 4. First-Time Setup

1. Access admin panel: `http://localhost:8080/admin`
2. Login with an authorized Google account (email must be in `ADMIN_EMAILS`)
3. Set up TOTP (scan QR code with Google Authenticator or similar app)
4. Navigate to **API Configuration** → Add your data source API keys
5. Go to **Watchlist Manager** → Verify tracked stocks
6. Start the **Scheduler** → Begin automated data collection

---

## 5. Running Both Servers

**Terminal 1 — Backend:**
```powershell
cd backend
.\venv\Scripts\activate
python main.py
```

**Terminal 2 — Frontend:**
```powershell
npm run dev
```

---

## Project Scripts

### Frontend
| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run build:dev` | Build for development |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npx vitest run` | Run tests |
| `npx vitest run --coverage` | Run tests with coverage |

### Backend
| Command | Description |
|---------|-------------|
| `python main.py` | Start backend server |
| `pytest tests/ -v` | Run all tests |
| `pytest tests/ --cov=app --cov-report=html` | Tests with coverage |
| `black app/ tests/ --line-length 100` | Format code |
| `isort app/ tests/` | Sort imports |
| `flake8 app/ tests/` | Lint code |
| `python manage_db.py status` | Check migration status |
| `alembic upgrade head` | Apply migrations |

---

## Troubleshooting

### Port Already in Use
If port 8080 is already in use, change it in `vite.config.ts`:
```typescript
server: {
  port: 3001, // Change to your preferred port
}
```

### Module Resolution Issues
If you encounter frontend import errors:
1. Clear node_modules: `rm -rf node_modules` or `Remove-Item -Recurse node_modules`
2. Clear package lock: `rm package-lock.json`
3. Reinstall: `npm install`

### Backend Module Errors
If you see `ModuleNotFoundError: No module named 'app'`:
- Ensure you are in the `backend/` directory
- Ensure the virtual environment is activated

### Database Issues
```bash
# Reset and rebuild database
cd backend
alembic downgrade base
alembic upgrade head
```

### TypeScript Errors
Run `npm run lint` to check for TypeScript errors and fix them accordingly.
