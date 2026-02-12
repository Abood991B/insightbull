# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, **please do NOT open a public issue**.

Instead, report it responsibly via one of these channels:

1. **Email:** [abdulrahman16baidaq@gmail.com](mailto:abdulrahman16baidaq@gmail.com)
2. **GitHub Private Advisory:** Use [Security Advisories](../../security/advisories/new)

### What to include

- A description of the vulnerability and its impact
- Steps to reproduce the issue
- Any relevant logs, screenshots, or proof-of-concept code

### Response timeline

- **Acknowledgement:** Within 48 hours
- **Initial assessment:** Within 7 days
- **Fix & disclosure:** Coordinated with the reporter

## Security Best Practices for Contributors

- Never commit secrets (API keys, tokens, passwords) to the repository
- All sensitive configuration must go in `.env` files (gitignored)
- Frontend code must never contain secrets — use backend-only flows
- Keep dependencies up to date and review security advisories
