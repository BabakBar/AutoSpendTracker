# Security Policy

## Supported Versions

Currently, we are supporting the following versions of AutoSpendTracker with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of AutoSpendTracker seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do not disclose the vulnerability publicly**
2. **Email us** at babak.barghi@gmail.com with details about the vulnerability
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggestions for mitigation

We will acknowledge your report within 48 hours and provide an estimated timeline for a fix.

## Security Features

AutoSpendTracker implements the following security measures:

### Secure Credential Storage

- OAuth2 tokens are stored in a secure location (`~/.autospendtracker/secrets/`) with appropriate file permissions
- Service account credentials should be kept secure and never committed to source control

### Environment Variables

- Sensitive configuration is loaded from environment variables or `.env` files
- The `.env` file should never be committed to version control (added to `.gitignore`)

### API Access

- Minimal OAuth2 scopes are requested for Gmail API access
- All API calls use HTTPS encryption

## Best Practices for Users

1. **Keep credentials secure**: 
   - Store your `credentials.json` and service account files securely
   - Never commit these files to public repositories

2. **Use environment variables**: 
   - Set sensitive configuration through environment variables rather than hardcoding

3. **Regularly rotate tokens**:
   - Delete the token.pickle file periodically to force re-authentication

4. **Review API access**:
   - Periodically review and revoke unused OAuth2 tokens in your Google account

5. **Update regularly**:
   - Keep the application and its dependencies updated to benefit from security fixes
