/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  readonly VITE_GOOGLE_CLIENT_SECRET: string;
  readonly VITE_OAUTH_REDIRECT_URI: string;
  readonly VITE_ADMIN_EMAILS: string;
  readonly VITE_SESSION_SECRET: string;
  readonly VITE_SESSION_TIMEOUT: string;
  readonly VITE_TOTP_ISSUER: string;
  readonly VITE_TOTP_SECRET_KEY: string;
  readonly VITE_RATE_LIMIT_WINDOW: string;
  readonly VITE_RATE_LIMIT_MAX_ATTEMPTS: string;
  readonly VITE_ENABLE_HTTPS: string;
  readonly VITE_SECURE_COOKIES: string;
  
  // Timezone configuration (optional - auto-detects browser timezone if not set)
  readonly VITE_USER_TIMEZONE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
