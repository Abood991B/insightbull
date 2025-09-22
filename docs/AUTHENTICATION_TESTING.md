# Authentication Flow Testing Guide

## Environment Setup

### 1. Backend Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Admin Configuration
ADMIN_EMAILS=admin@example.com,your-admin-email@gmail.com

# JWT Configuration
JWT_SECRET_KEY=your-secure-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/insight_stock.db

# API Configuration
VITE_API_URL=http://localhost:8000
```

### 2. Frontend Environment Variables

Create a `.env` file in the root directory with:

```env
# Google OAuth2 Configuration
VITE_GOOGLE_CLIENT_ID=your_google_client_id_here
VITE_GOOGLE_CLIENT_SECRET=your_google_client_secret_here
VITE_OAUTH_REDIRECT_URI=http://localhost:5173/admin/auth/callback

# Admin Configuration
VITE_ADMIN_EMAILS=admin@example.com,your-admin-email@gmail.com

# API Configuration
VITE_API_URL=http://localhost:8000

# Session Configuration
VITE_SESSION_TIMEOUT=1800000
VITE_SESSION_SECRET=your-secure-session-secret
```

## Testing the Authentication Flow

### 1. Start the Backend Server

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Frontend Development Server

```bash
npm run dev
```

### 3. Test Authentication Steps

1. **Navigate to Admin Login**: Go to `http://localhost:5173/admin`
2. **Google OAuth2 Flow**: Click "Sign in with Google" button
3. **Google Authorization**: Complete Google OAuth2 authorization
4. **Callback Handling**: System should redirect to callback URL and exchange code
5. **TOTP Verification**: Complete two-factor authentication
6. **Dashboard Access**: System should redirect to admin dashboard

### 4. Test Protected Routes

Try accessing these URLs directly without authentication:
- `/admin/dashboard`
- `/admin/model-accuracy`
- `/admin/api-config`
- `/admin/watchlist`
- `/admin/storage`
- `/admin/logs`

All should redirect to `/admin` login page.

### 5. Test Session Management

1. **Activity Updates**: Navigate between admin pages (session should update)
2. **Session Expiry**: Wait for session timeout (should redirect to login)
3. **Logout**: Use logout button (should clear session and redirect)

## Troubleshooting

### Common Issues

1. **OAuth2 Errors**: Check Google Client ID/Secret configuration
2. **CORS Issues**: Ensure backend allows frontend origin
3. **Token Issues**: Check JWT secret key configuration
4. **Admin Access**: Verify admin email is in ADMIN_EMAILS list

### API Endpoints to Test

Backend authentication endpoints:
- `POST /api/admin/auth/oauth/google` - OAuth2 token exchange
- `POST /api/admin/auth/totp/verify` - TOTP verification
- `POST /api/admin/auth/validate` - Token validation
- `GET /api/admin/auth/verify` - Session verification
- `POST /api/admin/auth/refresh` - Token refresh

### Expected Flow

1. **Initial Access**: `/admin` → OAuth2AdminAuth component
2. **Google OAuth**: Redirect to Google → Authorization → Callback
3. **Backend Token Exchange**: Frontend sends code → Backend exchanges for tokens
4. **TOTP Setup/Verification**: Complete two-factor authentication
5. **Dashboard Access**: Authenticated user can access all admin features
6. **API Calls**: All admin API calls include Bearer token authentication

## Success Criteria

✅ OAuth2 authentication flow works end-to-end
✅ Backend token exchange functions correctly
✅ TOTP verification completes successfully
✅ Protected routes redirect unauthenticated users
✅ Admin dashboard loads with real data from backend APIs
✅ All admin pages function with authenticated API calls
✅ Session management (timeouts, logout) works properly
✅ JWT tokens are properly validated by backend