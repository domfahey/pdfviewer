# Security Policy

[![Security](https://img.shields.io/badge/security-best%20practices-brightgreen.svg)](docs/SECURITY.md)

## Table of Contents

- [Reporting Security Vulnerabilities](#reporting-security-vulnerabilities)
- [Security Measures](#security-measures)
  - [Code Security](#code-security)
  - [Repository Security](#repository-security)
  - [Infrastructure Security](#infrastructure-security)
- [Security Checklist for Contributors](#security-checklist-for-contributors)
- [Tools](#tools)
- [Incident Response](#incident-response)

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please email the author at domfahey@gmail.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Security Measures

### Code Security

1. **No Hardcoded Secrets**
   - All configuration via environment variables
   - `.env.example` provided as template
   - Secrets never committed to repository

2. **Input Validation**
   - File size limits (50MB)
   - File type validation (PDF only)
   - Path traversal protection
   - UUID v4 validation

3. **Logging Security**
   - Automatic sanitization of sensitive data
   - Headers like `authorization`, `cookie` are redacted
   - Password/token fields automatically masked

### Repository Security

1. **Pre-commit Hooks**
   ```bash
   pre-commit install
   ```
   - `detect-secrets`: Prevents secret commits
   - `gitleaks`: Scans for sensitive patterns
   - Python/JS linting and formatting

2. **Git History**
   - Cleaned of all uploaded files (2025-01-21)
   - No user data in version control
   - Regular security scans

3. **Dependencies**
   - Regular updates via Dependabot
   - Security advisories monitored
   - Minimal dependency footprint

### Infrastructure Security

1. **File Storage**
   - Uploads stored temporarily
   - Not tracked in git
   - Cleared on restart (POC only)

2. **CORS Configuration**
   - Restricted to localhost ports
   - Production requires explicit domains

3. **Error Handling**
   - Debug info only in development
   - Generic errors in production
   - No stack traces exposed

## Security Checklist for Contributors

Before submitting code:

- [ ] No hardcoded passwords, tokens, or secrets
- [ ] No sensitive URLs or connection strings
- [ ] All user input validated
- [ ] Error messages don't leak sensitive info
- [ ] New dependencies reviewed for vulnerabilities
- [ ] Tests don't contain real credentials
- [ ] Documentation doesn't expose secrets

## Tools

```bash
# Scan current code
detect-secrets scan
gitleaks detect --no-git

# Scan git history
gitleaks detect

# Update dependencies
pip list --outdated
npm outdated
```

## Incident Response

1. Immediately remove any exposed secrets
2. Rotate affected credentials
3. Update security measures
4. Document in CHANGELOG.md
5. Notify affected users if applicable