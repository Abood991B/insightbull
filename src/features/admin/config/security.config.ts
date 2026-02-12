/**
 * Security configuration for admin authentication.
 *
 * SECURITY NOTE: Only public, non-sensitive values belong here.
 * All secrets (client_secret, session keys, TOTP secrets) are
 * handled exclusively on the backend. Never expose secrets in
 * frontend code - they are visible to anyone via browser DevTools.
 */
export const securityConfig = {
  oauth2: {
    clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    // clientSecret is intentionally omitted - token exchange happens server-side only
    redirectUri: import.meta.env.VITE_OAUTH_REDIRECT_URI || 'http://localhost:8080/admin/auth/callback',
    scope: 'openid email profile',
    discoveryDocs: ['https://accounts.google.com/.well-known/openid-configuration'],
  },

  admin: {
    // Admin email authorization is enforced server-side only
    sessionTimeout: parseInt(import.meta.env.VITE_SESSION_TIMEOUT || '1800000'), // 30 minutes default
  },

  totp: {
    issuer: import.meta.env.VITE_TOTP_ISSUER || 'Stock Market Sentiment Dashboard',
    algorithm: 'SHA1',
    digits: 6,
    period: 30,
    window: 2, // Allow 2 time windows for clock skew
  },

  rateLimit: {
    windowMs: parseInt(import.meta.env.VITE_RATE_LIMIT_WINDOW || '900000'), // 15 minutes
    maxAttempts: parseInt(import.meta.env.VITE_RATE_LIMIT_MAX_ATTEMPTS || '5'),
  },

  security: {
    enableHttps: import.meta.env.VITE_ENABLE_HTTPS === 'true',
    secureCookies: import.meta.env.VITE_SECURE_COOKIES === 'true',
    sameSite: 'strict' as const,
    httpOnly: true,
  },

  // Security headers
  headers: {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://accounts.google.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; media-src 'self' data:; connect-src 'self' http://127.0.0.1:8000 http://localhost:8000 https://accounts.google.com https://www.googleapis.com https://oauth2.googleapis.com",
  },
};

// Validate configuration on load
export const validateSecurityConfig = (): boolean => {
  const errors: string[] = [];

  if (!securityConfig.oauth2.clientId) {
    errors.push('Google OAuth2 Client ID is not configured');
  }

  if (errors.length > 0) {
    console.error('Security configuration errors:', errors);
    return false;
  }

  return true;
};