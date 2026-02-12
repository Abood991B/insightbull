/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  // VITE_GOOGLE_CLIENT_SECRET removed - secret lives on backend only
  readonly VITE_OAUTH_REDIRECT_URI: string;
  // VITE_ADMIN_EMAILS removed - enforced server-side
  // VITE_SESSION_SECRET removed - secret lives on backend only
  readonly VITE_SESSION_TIMEOUT: string;
  readonly VITE_TOTP_ISSUER: string;
  // VITE_TOTP_SECRET_KEY removed - secret lives on backend only
  readonly VITE_RATE_LIMIT_WINDOW: string;
  readonly VITE_RATE_LIMIT_MAX_ATTEMPTS: string;
  readonly VITE_ENABLE_HTTPS: string;
  readonly VITE_SECURE_COOKIES: string;
  readonly VITE_API_BASE_URL: string;

  // Timezone configuration (optional - auto-detects browser timezone if not set)
  readonly VITE_USER_TIMEZONE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}