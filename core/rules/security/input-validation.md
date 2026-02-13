---
name: input-validation
description: Ensures all user inputs are properly validated to prevent injection and other attacks
---

# Rule: Input Validation

All user inputs must be validated before processing to prevent security vulnerabilities.

## Requirements

**Validate Input Type:**
```python
# GOOD
user_id = request.args.get('id')
if not user_id or not user_id.isdigit():
    return error("Invalid user ID")
user_id = int(user_id)
```

**Validate Input Length:**
```python
# GOOD
username = request.json.get('username', '')
if len(username) < 3 or len(username) > 50:
    return error("Username must be 3-50 characters")
```

**Validate Input Format:**
```python
# GOOD
import re
email = request.json.get('email', '')
if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
    return error("Invalid email format")
```

**Sanitize Input:**
```python
# GOOD
from markupsafe import escape
user_input = request.form.get('comment', '')
safe_input = escape(user_input)  # Prevents XSS
```

## Common Vulnerabilities

**SQL Injection:**
```python
# BAD
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**Command Injection:**
```python
# BAD
os.system(f"ping {hostname}")

# GOOD
subprocess.run(["ping", "-c", "4", hostname], check=True)
```

**Path Traversal:**
```python
# BAD
with open(f"/data/{filename}") as f:
    content = f.read()

# GOOD
from pathlib import Path
base_path = Path("/data")
file_path = (base_path / filename).resolve()
if not str(file_path).startswith(str(base_path)):
    return error("Invalid path")
```

## Review Checklist

- [ ] All user inputs are validated
- [ ] Input type is checked
- [ ] Input length is limited
- [ ] Input format is validated
- [ ] SQL queries use parameterized statements
- [ ] No shell commands with user input
- [ ] File paths are validated and sanitized
- [ ] Special characters are escaped when needed
