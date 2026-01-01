import { securityConfig } from '../config/security.config';

// Types
export interface AdminUser {
  email: string;
  name: string;
  picture?: string;
  totpEnabled: boolean;
  totpSecret?: string;
}

export interface AuthSession {
  user: AdminUser;
  accessToken: string;
  refreshToken?: string;
  expiresAt: number;
  lastActivity: number;
  totpVerified: boolean;
}

export interface RateLimitEntry {
  attempts: number;
  windowStart: number;
}

// Rate limiting storage
const rateLimitStore = new Map<string, RateLimitEntry>();

// Session storage (in production, use secure server-side storage)
const SESSION_KEY = 'admin_auth_session';
const TOTP_SECRETS_KEY = 'admin_totp_secrets';

export class AuthService {
  private static instance: AuthService;
  private session: AuthSession | null = null;
  private activityTimer: NodeJS.Timeout | null = null;

  private constructor() {
    this.loadSession();
    this.startActivityMonitoring();
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  private getApiBaseUrl(): string {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  // OAuth2 Authentication
  async authenticateWithGoogle(code: string): Promise<{ success: boolean; user?: AdminUser; error?: string }> {
    try {
      // Send the OAuth code to the backend for token exchange and validation
      const response = await fetch(`${this.getApiBaseUrl()}/api/admin/auth/oauth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          code,
          redirect_uri: securityConfig.oauth2.redirectUri 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        this.logSecurityEvent('BACKEND_AUTH_ERROR', { error: errorData.detail || 'Authentication failed' });
        return { success: false, error: errorData.detail || 'Authentication failed' };
      }

      const authResult = await response.json();
      
      if (!authResult.access_token || !authResult.user) {
        return { success: false, error: 'Invalid authentication response from server' };
      }

      const adminUser: AdminUser = {
        email: authResult.user.email,
        name: authResult.user.name || authResult.user.email,
        picture: authResult.user.picture,
        totpEnabled: this.hasTotpSecret(authResult.user.email),
      };

      this.createSession(adminUser, authResult.access_token, authResult.refresh_token);
      
      this.logSecurityEvent('OAUTH_SUCCESS', { email: adminUser.email });
      return { success: true, user: adminUser };
    } catch (error) {
      console.error('OAuth authentication error:', error);
      return { success: false, error: 'Authentication failed. Please try again.' };
    }
  }

  private async exchangeCodeForTokens(code: string): Promise<{ success: boolean; tokens?: any; error?: string }> {
    try {
      const response = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          code,
          client_id: securityConfig.oauth2.clientId,
          client_secret: securityConfig.oauth2.clientSecret,
          redirect_uri: securityConfig.oauth2.redirectUri,
          grant_type: 'authorization_code',
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: error.error_description || 'Token exchange failed' };
      }

      const tokens = await response.json();
      return { success: true, tokens };
    } catch (error) {
      console.error('Token exchange error:', error);
      return { success: false, error: 'Failed to exchange authorization code' };
    }
  }

  private async getUserInfo(accessToken: string): Promise<any> {
    const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user info');
    }

    return response.json();
  }

  // TOTP Management
  generateTotpSecret(email: string): { secret: string; qrCode: string } {
    // Generate a random secret (in production, use a cryptographically secure method)
    const secret = this.generateRandomSecret(32);
    
    // Store the secret securely (in production, encrypt and store server-side)
    this.storeTotpSecret(email, secret);
    
    // Generate QR code URL for authenticator apps
    const otpauth = `otpauth://totp/${encodeURIComponent(securityConfig.totp.issuer)}:${encodeURIComponent(email)}?secret=${secret}&issuer=${encodeURIComponent(securityConfig.totp.issuer)}&algorithm=${securityConfig.totp.algorithm}&digits=${securityConfig.totp.digits}&period=${securityConfig.totp.period}`;
    
    return { secret, qrCode: otpauth };
  }

  async verifyTotp(email: string, token: string): Promise<boolean> {
    try {
      // First verify locally to avoid unnecessary API calls
      const secret = this.getTotpSecret(email);
      if (secret) {
        const localValid = await this.verifyTotpToken(secret, token);
        if (!localValid) {
          this.logSecurityEvent('TOTP_FAILED', { email });
          return false;
        }
      }

      // Verify with backend if we have a session
      if (this.session && this.session.user.email === email) {
        try {
          const response = await fetch(`${this.getApiBaseUrl()}/api/admin/auth/totp/verify`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${this.session.accessToken}`,
            },
            body: JSON.stringify({ 
              email,
              totp_code: token 
            }),
          });

          if (response.ok) {
            const result = await response.json();
            if (result.verified) {
              // Mark TOTP as verified in session
              this.session.totpVerified = true;
              this.saveSession();
              this.logSecurityEvent('TOTP_VERIFIED', { email });
              return true;
            }
          }
        } catch (error) {
          console.error('Backend TOTP verification failed, using local verification:', error);
        }
      }

      // Fallback to local verification if backend is unavailable
      if (secret) {
        const valid = await this.verifyTotpToken(secret, token);
        if (valid && this.session && this.session.user.email === email) {
          this.session.totpVerified = true;
          this.saveSession();
          this.logSecurityEvent('TOTP_VERIFIED', { email });
        }
        return valid;
      }

      return false;
    } catch (error) {
      console.error('TOTP verification error:', error);
      this.logSecurityEvent('TOTP_ERROR', { email, error: error });
      return false;
    }
  }

  private async verifyTotpToken(secret: string, token: string): Promise<boolean> {
    try {
      // Use Web Crypto API for proper TOTP verification
      const timeStep = 30; // 30 seconds
      const window = 2; // Allow 2 time windows for clock skew
      const currentTime = Math.floor(Date.now() / 1000);
      
      // Check current time window and adjacent windows
      for (let i = -window; i <= window; i++) {
        const timeWindow = Math.floor((currentTime + (i * timeStep)) / timeStep);
        const expectedToken = await this.generateTOTP(secret, timeWindow);
        if (token === expectedToken) {
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.error('TOTP verification error:', error);
      return false;
    }
  }

  private async generateTOTP(secret: string, timeWindow: number): Promise<string> {
    try {
      // Convert secret from base32 to bytes
      const key = this.base32ToBytes(secret);
      
      // Convert time window to 8-byte array (big endian)
      const timeBytes = new ArrayBuffer(8);
      const timeView = new DataView(timeBytes);
      timeView.setUint32(4, timeWindow, false); // Big endian, high 32 bits are 0
      
      // Import key for HMAC-SHA1
      const keyBuffer = new Uint8Array(key).buffer;
      const cryptoKey = await crypto.subtle.importKey(
        'raw',
        keyBuffer,
        { name: 'HMAC', hash: 'SHA-1' },
        false,
        ['sign']
      );
      
      // Generate HMAC-SHA1
      const signature = await crypto.subtle.sign('HMAC', cryptoKey, timeBytes);
      const hmac = new Uint8Array(signature);
      
      // Dynamic truncation
      const offset = hmac[hmac.length - 1] & 0x0f;
      const code = ((hmac[offset] & 0x7f) << 24) |
                   ((hmac[offset + 1] & 0xff) << 16) |
                   ((hmac[offset + 2] & 0xff) << 8) |
                   (hmac[offset + 3] & 0xff);
      
      // Return 6-digit code
      return (code % 1000000).toString().padStart(6, '0');
    } catch (error) {
      console.error('TOTP generation error:', error);
      return '000000'; // Fallback
    }
  }

  private base32ToBytes(base32: string): Uint8Array {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    let bits = '';
    
    // Remove padding and convert to uppercase
    const cleanBase32 = base32.toUpperCase().replace(/=/g, '');
    
    for (const char of cleanBase32) {
      const index = alphabet.indexOf(char);
      if (index === -1) continue;
      bits += index.toString(2).padStart(5, '0');
    }
    
    // Convert bits to bytes
    const bytes = new Uint8Array(Math.floor(bits.length / 8));
    for (let i = 0; i < bytes.length; i++) {
      const bitStart = i * 8;
      const bitEnd = bitStart + 8;
      if (bitEnd <= bits.length) {
        bytes[i] = parseInt(bits.substring(bitStart, bitEnd), 2);
      }
    }
    
    return bytes;
  }

  // Session Management
  private createSession(user: AdminUser, accessToken: string, refreshToken?: string): void {
    const now = Date.now();
    
    // Store the backend JWT token for API calls
    localStorage.setItem('admin_token', accessToken);
    
    this.session = {
      user,
      accessToken,
      refreshToken,
      expiresAt: now + securityConfig.admin.sessionTimeout,
      lastActivity: now,
      totpVerified: false,
    };
    this.saveSession();
  }

  updateSessionActivity(): void {
    if (this.session) {
      const now = Date.now();
      this.session.lastActivity = now;
      this.session.expiresAt = now + securityConfig.admin.sessionTimeout;
      this.saveSession();
    }
  }

  isAuthenticated(): boolean {
    if (!this.session) {
      return false;
    }

    const now = Date.now();
    
    // Check if session has expired
    if (now > this.session.expiresAt) {
      this.logout();
      return false;
    }

    // Check if inactive for too long
    if (now - this.session.lastActivity > securityConfig.admin.sessionTimeout) {
      this.logout();
      return false;
    }

    return true;
  }

  isFullyAuthenticated(): boolean {
    return this.isAuthenticated() && (this.session?.totpVerified || !this.session?.user.totpEnabled);
  }

  getSession(): AuthSession | null {
    if (this.isAuthenticated()) {
      return this.session;
    }
    return null;
  }

  logout(): void {
    if (this.session) {
      this.logSecurityEvent('LOGOUT', { email: this.session.user.email });
    }
    
    // Clear admin token from localStorage
    localStorage.removeItem('admin_token');
    
    this.session = null;
    this.clearSession();
    
    if (this.activityTimer) {
      clearInterval(this.activityTimer);
      this.activityTimer = null;
    }
  }

  // Authorization
  private isAuthorizedAdmin(email: string): boolean {
    const authorizedEmails = securityConfig.admin.authorizedEmails;
    return authorizedEmails.includes(email.toLowerCase());
  }

  // Rate Limiting
  private checkRateLimit(identifier: string): boolean {
    const now = Date.now();
    const entry = rateLimitStore.get(identifier);
    
    if (!entry || now - entry.windowStart > securityConfig.rateLimit.windowMs) {
      // New window
      rateLimitStore.set(identifier, { attempts: 1, windowStart: now });
      return true;
    }
    
    if (entry.attempts >= securityConfig.rateLimit.maxAttempts) {
      return false;
    }
    
    entry.attempts++;
    return true;
  }

  // Storage helpers
  private saveSession(): void {
    if (this.session) {
      try {
        const encrypted = this.encrypt(JSON.stringify(this.session));
        sessionStorage.setItem(SESSION_KEY, encrypted);
      } catch (error) {
        console.error('Failed to save session:', error);
      }
    }
  }

  private loadSession(): void {
    try {
      const encrypted = sessionStorage.getItem(SESSION_KEY);
      if (encrypted) {
        const decrypted = this.decrypt(encrypted);
        this.session = JSON.parse(decrypted);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
      this.clearSession();
    }
  }

  private clearSession(): void {
    sessionStorage.removeItem(SESSION_KEY);
  }

  private storeTotpSecret(email: string, secret: string): void {
    try {
      const secrets = this.getTotpSecrets();
      secrets[email] = this.encrypt(secret);
      localStorage.setItem(TOTP_SECRETS_KEY, JSON.stringify(secrets));
    } catch (error) {
      console.error('Failed to store TOTP secret:', error);
    }
  }

  private getTotpSecret(email: string): string | null {
    try {
      const secrets = this.getTotpSecrets();
      const encrypted = secrets[email];
      return encrypted ? this.decrypt(encrypted) : null;
    } catch (error) {
      console.error('Failed to retrieve TOTP secret:', error);
      return null;
    }
  }

  private hasTotpSecret(email: string): boolean {
    return this.getTotpSecret(email) !== null;
  }

  private getTotpSecrets(): Record<string, string> {
    try {
      const stored = localStorage.getItem(TOTP_SECRETS_KEY);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  }

  // Encryption helpers (simplified - use crypto-js in production)
  private encrypt(data: string): string {
    // In production, use proper encryption with crypto-js
    return btoa(data);
  }

  private decrypt(data: string): string {
    // In production, use proper decryption with crypto-js
    return atob(data);
  }

  private generateRandomSecret(length: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    let secret = '';
    for (let i = 0; i < length; i++) {
      secret += chars[Math.floor(Math.random() * chars.length)];
    }
    return secret;
  }

  // Activity monitoring
  private startActivityMonitoring(): void {
    // Check session expiry every minute
    this.activityTimer = setInterval(() => {
      if (this.session && !this.isAuthenticated()) {
        this.logout();
      }
    }, 60000);

    // Listen for user activity
    if (typeof window !== 'undefined') {
      ['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
        window.addEventListener(event, () => this.updateSessionActivity(), { passive: true });
      });
    }
  }

  // Security logging
  private logSecurityEvent(event: string, details: any): void {
    const logEntry = {
      timestamp: new Date().toISOString(),
      event,
      details,
      userAgent: navigator.userAgent,
      ip: 'client-side', // In production, get from server
    };
    
    console.log('[SECURITY]', logEntry);
    
    // In production, send to server for persistent logging
    // this.sendToSecurityLog(logEntry);
  }
}

export const authService = AuthService.getInstance();
