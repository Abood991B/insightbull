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
- 30-minute session timeout with activity-based renewal
- Automatic logout on inactivity
- Secure session storage with encryption
- Real-time session monitoring

## Setup Instructions

### 1. Install Dependencies
Run the PowerShell script to install all required packages:
```powershell
.\install-auth-dependencies.ps1
```

Or manually install:
```bash
npm install @react-oauth/google otplib qrcode js-cookie crypto-js jsonwebtoken axios
npm install --save-dev @types/qrcode @types/js-cookie @types/crypto-js @types/jsonwebtoken
```

### 2. Google OAuth2 Configuration

#### Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API

#### Configure OAuth2 Credentials
1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Web application**
4. Configure:
   - **Name**: Stock Market Dashboard Admin
   - **Authorized JavaScript origins**:
     - Development: `http://localhost:5173`
     - Production: `https://yourdomain.com`
   - **Authorized redirect URIs**:
     - Development: `http://localhost:5173/admin/auth/callback`
     - Production: `https://yourdomain.com/admin/auth/callback`
5. Save the Client ID and Client Secret

### 3. Environment Configuration

#### Development Setup
1. Copy `.env.example` to `.env`
2. Configure the following variables:

```env
# Google OAuth2
VITE_GOOGLE_CLIENT_ID=your_client_id_here
VITE_GOOGLE_CLIENT_SECRET=your_client_secret_here
VITE_OAUTH_REDIRECT_URI=http://localhost:5173/admin/auth/callback

# Admin Emails (comma-separated)
VITE_ADMIN_EMAILS=admin@example.com,admin2@example.com

# Session Security
VITE_SESSION_SECRET=generate_32_char_random_string
VITE_SESSION_TIMEOUT=1800000

# TOTP Configuration
VITE_TOTP_SECRET_KEY=generate_another_32_char_random_string
```

#### Production Setup
1. Use `.env.production` as template
2. Update all URLs to use HTTPS
3. Generate cryptographically secure secrets:

```bash
# Generate secure random strings (Linux/Mac)
openssl rand -hex 32

# Or use Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 4. Admin Email Management

Add authorized admin emails to `VITE_ADMIN_EMAILS`:
- Use comma-separated list
- Emails are case-insensitive
- Only these emails can access admin panel

Example:
```env
VITE_ADMIN_EMAILS=john.doe@company.com,jane.smith@company.com,admin@company.com
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
4. Access granted for 30 minutes

## Security Features

### Rate Limiting
- 5 authentication attempts per 15-minute window
- Automatic blocking of suspicious activity
- IP-based tracking (when deployed with backend)

### Session Security
- Encrypted session storage
- Automatic timeout after 30 minutes
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
- Confirm email is in `VITE_ADMIN_EMAILS`
- Check for typos in email address
- Verify environment variables are loaded

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
