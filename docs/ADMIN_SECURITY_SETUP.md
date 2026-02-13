# Admin Security Setup Guide

## Overview
This guide provides instructions for setting up the secure OAuth2 + TOTP authentication system for admin access to the Stock Market Sentiment Dashboard.

## Security Architecture

### Multi-Factor Authentication (MFA)
The admin panel implements a three-layer security model:
1. **OAuth2 Authentication** - Google account verification
2. **Email Whitelist** - Authorization check against approved admin emails
3. **TOTP Verification** - Time-based One-Time Password using authenticator apps

### Session Management
- Configurable session timeout (`VITE_SESSION_TIMEOUT`) with activity-based renewal
- Automatic logout on inactivity
- Server-issued JWT tokens (no secrets in browser storage)
- Real-time session monitoring

## Setup Instructions

### 1. Install Dependencies

**Frontend:**
```bash
npm install
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

> Cryptographic operations (JWT signing, TOTP secret generation, API key encryption) are handled entirely on the backend. The frontend only needs `@react-oauth/google`, `qrcode`, and `js-cookie`.

### 2. Google OAuth2 Configuration

#### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google Identity Services API

#### Configure OAuth2 Credentials
1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Web application**
4. Configure:
   - **Name**: Stock Market Dashboard Admin
   - **Authorized JavaScript origins**:
     - Development: `http://localhost:8080`
     - Production: `https://yourdomain.com`
   - **Authorized redirect URIs**:
     - Development: `http://localhost:8080/admin`
     - Production: `https://yourdomain.com/admin`
5. Save the Client ID and Client Secret

### 3. Environment Configuration

#### Development Setup

**Frontend** (`.env` in project root — public values only):
```env
VITE_GOOGLE_CLIENT_ID=your_client_id_here
VITE_OAUTH_REDIRECT_URI=http://localhost:8080/admin
VITE_API_BASE_URL=http://localhost:8000
VITE_SESSION_TIMEOUT=1800000
VITE_TOTP_ISSUER=InsightBull
```

**Backend** (`backend/.env` — all secrets):
```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
ADMIN_EMAILS=admin@example.com,admin2@example.com
SECRET_KEY=generate_64_char_random_string
JWT_SECRET_KEY=generate_64_char_random_string
API_ENCRYPTION_KEY=generate_32_byte_hex_string
API_ENCRYPTION_SALT=generate_16_byte_hex_string
```

> **Security policy:** Secrets (`GOOGLE_CLIENT_SECRET`, `ADMIN_EMAILS`, `JWT_SECRET_KEY`, encryption keys) **never** appear in the frontend `.env`. They exist only in `backend/.env`.

#### Production Setup
1. Set all URLs to use HTTPS
2. Generate cryptographically secure secrets for backend:

```bash
# Generate secure random strings
openssl rand -hex 32

# Or use Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 4. Admin Email Management

Add authorized admin emails to the **backend** `ADMIN_EMAILS` env var:
- Use comma-separated list
- Emails are case-insensitive
- Only these emails can authenticate through OAuth2

Example (in `backend/.env`):
```env
ADMIN_EMAILS=john.doe@company.com,jane.smith@company.com,admin@company.com
```

### 5. TOTP Setup for Admins

#### First-Time Admin Setup
1. Navigate to `/admin` (manually enter URL)
2. Sign in with Google account
3. System will display QR code for TOTP setup
4. Scan with authenticator app:
   - Google Authenticator
   - Microsoft Authenticator
   - Authy
5. Enter 6-digit code to verify
6. Save backup codes securely

#### Subsequent Logins
1. Navigate to `/admin`
2. Sign in with Google
3. Enter current TOTP code
4. Access granted (JWT token issued with configured expiry)

## Security Features

### Rate Limiting
- 5 authentication attempts per 15-minute window
- Automatic blocking of suspicious activity
- IP-based tracking (when deployed with backend)

### Session Security
- Server-issued JWT tokens with expiry
- Configurable frontend timeout (`VITE_SESSION_TIMEOUT`)
- Activity-based session renewal
- Secure logout with complete cleanup

### Audit Logging
- All authentication attempts logged
- Failed login tracking
- Session activity monitoring
- Security event recording

### Protection Mechanisms
- XSS protection headers
- CSRF token validation
- Input sanitization
- Secure cookie handling

## Deployment Checklist

### Pre-Deployment
- [ ] Google OAuth2 credentials configured
- [ ] Admin email whitelist populated
- [ ] Secure secrets generated (min 32 chars)
- [ ] HTTPS certificates installed
- [ ] Environment variables set

### Security Validation
- [ ] Test OAuth2 flow with authorized email
- [ ] Test rejection of unauthorized email
- [ ] Verify TOTP code validation
- [ ] Confirm session timeout works
- [ ] Test rate limiting

### Production Configuration
- [ ] Remove all development/demo code
- [ ] Enable HTTPS enforcement
- [ ] Configure secure cookies
- [ ] Set up monitoring/alerting
- [ ] Implement backup procedures

## Troubleshooting

### Common Issues

#### OAuth2 Redirect Error
- Verify redirect URI matches exactly in Google Console
- Check for trailing slashes
- Ensure protocol (http/https) matches

#### TOTP Code Invalid
- Check device time synchronization
- Verify TOTP secret is correctly stored
- Try codes from adjacent time windows

#### Session Expires Too Quickly
- Increase `VITE_SESSION_TIMEOUT` value
- Check for network issues
- Verify activity tracking is working

#### Unauthorized Access Error
- Confirm email is in backend `ADMIN_EMAILS` env var
- Check for typos in email address
- Verify backend environment variables are loaded correctly

## Security Best Practices

1. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories
   - Apply patches promptly

2. **Access Management**
   - Review admin list quarterly
   - Remove inactive admins
   - Use principle of least privilege

3. **Monitoring**
   - Review audit logs regularly
   - Set up alerts for failed logins
   - Monitor for unusual patterns

4. **Backup & Recovery**
   - Backup TOTP secrets securely
   - Document recovery procedures
   - Test recovery process regularly

## Support

For security issues or questions:
1. Check this documentation
2. Review audit logs for errors
3. Verify configuration settings
4. Contact system administrator

## Security Disclosure

If you discover a security vulnerability:
1. Do NOT create a public issue
2. Email security concerns privately
3. Allow time for patch development
4. Coordinate disclosure timeline
