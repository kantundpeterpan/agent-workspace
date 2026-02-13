---
name: no-secrets
description: Ensures no secrets, API keys, or credentials are hardcoded in the codebase
---

# Rule: No Secrets in Code

Never hardcode secrets, API keys, passwords, or credentials in source code.

## Prohibited Patterns

**Hardcoded Secrets:**
```javascript
// BAD
const apiKey = "sk-1234567890abcdef";
const password = "supersecret123";
const token = "ghp_xxxxxxxxxxxx";
```

**Configuration with Secrets:**
```yaml
# BAD
database:
  password: "mydbpassword123"
```

## Allowed Patterns

**Environment Variables:**
```javascript
// GOOD
const apiKey = process.env.API_KEY;
```

**Configuration Files (not committed):**
```javascript
// GOOD - from .env file (gitignored)
const config = require('./.env');
```

**Secret Management Services:**
```javascript
// GOOD
const secret = await secretManager.getSecret('api-key');
```

## Detection Patterns

Watch for:
- `password`, `secret`, `token`, `key` followed by `=` and a quoted string
- `API_KEY`, `SECRET_KEY`, `AUTH_TOKEN` assignments
- Base64 encoded strings that look like credentials
- Private keys (BEGIN PRIVATE KEY, BEGIN RSA PRIVATE KEY)
- Hardcoded database connection strings with passwords

## Review Checklist

- [ ] No hardcoded passwords
- [ ] No hardcoded API keys
- [ ] No hardcoded tokens
- [ ] No private keys in code
- [ ] No database passwords in connection strings
- [ ] Secrets loaded from environment or secure storage
- [ ] `.env` files are in `.gitignore`
