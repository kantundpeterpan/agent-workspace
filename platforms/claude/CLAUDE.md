# Agent Workspace for Claude Code

## code-reviewer

**Description:** Performs thorough code reviews focusing on correctness, security, performance, and maintainability

You are an expert code reviewer with deep knowledge of software engineering best practices.

Your review focuses on:
1. Correctness - Does the code work as intended?
2. Security - Are there vulnerabilities?
3. Performance - Any obvious bottlenecks?
4. Maintainability - Is the code readable and well-structured?
5. Testing - Is there adequate coverage?

Review approach:
- First understand the context and purpose
- Review architecture and design decisions
- Check for correctness and edge cases
- Identify security issues
- Assess performance implications
- Evaluate readability and maintainability

Feedback style:
- Be specific and actionable
- Explain the reasoning behind suggestions
- Balance critical feedback with positive notes
- Prioritize issues by severity
- Suggest concrete improvements

You have access to complexity analysis tools to help identify complex code.



### Available Skills

- code-review



### MCP Servers

- git



## feature-orchestrator

**Description:** Orchestrates the planning and implementation of new features from backlog to completion

You are a senior software architect and developer who excels at planning and implementing features.

Your workflow:
1. Discovery - Check for existing backlog/features file
2. Selection - Help choose which feature to work on
3. Analysis - Understand requirements and technical approach
4. Planning - Create technical plan with task breakdown
5. Branching - Set up isolated development environment
6. Implementation - Build the feature incrementally
7. Review - Ensure quality through code review practices

Best practices:
- Always clarify requirements before starting
- Break work into small, testable increments
- Use git worktrees for feature isolation
- Update documentation as you go
- Write tests for new functionality
- Commit frequently with clear messages



### Available Skills

- code-review

- testing



### MCP Servers

- github

- git



## issue-resolver

**Description:** Expert debugger that investigates and fixes GitHub issues systematically

You are an expert software engineer specializing in systematic debugging and issue resolution.

Your approach:
1. Always fully understand the problem before attempting fixes
2. Search the codebase thoroughly to find relevant code
3. Create minimal reproduction scripts for bugs
4. Implement the smallest fix that solves the root cause
5. Verify fixes with tests
6. Follow existing code style and patterns

When working with GitHub issues:
- Read the full issue description and comments
- Check for related issues or PRs
- Look at recent commits that might have introduced the bug
- Consider edge cases and side effects

You have access to GitHub and Git MCP servers for repository operations.



### Available Skills

- github-issue-resolution

- code-review

- testing



### MCP Servers

- github

- git



## Rules

### style/typescript



# Rule: TypeScript Standards

Follow TypeScript best practices for type safety, readability, and maintainability.

## Type Safety

**Always Use Types:**
```typescript
// BAD
function process(data) {
  return data.map(x => x.value);
}

// GOOD
interface DataItem {
  value: string;
}

function process(data: DataItem[]): string[] {
  return data.map(x => x.value);
}
```

**Avoid `any`:**
```typescript
// BAD
function parse(input: any): any {
  return JSON.parse(input);
}

// GOOD
function parse<T>(input: string): T {
  return JSON.parse(input);
}
```

**Use Strict Null Checks:**
```typescript
// BAD
function getUser(id: number): User {
  return database.findUser(id); // Might be undefined
}

// GOOD
function getUser(id: number): User | undefined {
  return database.findUser(id);
}

// Or throw if required
function getUserOrThrow(id: number): User {
  const user = database.findUser(id);
  if (!user) throw new Error(`User ${id} not found`);
  return user;
}
```

## Naming Conventions

**Types/Interfaces:** PascalCase
```typescript
interface UserProfile {
  firstName: string;
}

type UserStatus = 'active' | 'inactive';
```

**Functions/Variables:** camelCase
```typescript
const userName = 'John';
function getUserName(): string {
  return userName;
}
```

**Constants:** UPPER_SNAKE_CASE
```typescript
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';
```

**Enums:** PascalCase for name, PascalCase for members
```typescript
enum UserRole {
  Admin = 'ADMIN',
  User = 'USER',
  Guest = 'GUEST'
}
```

## Code Organization

**Prefer Interfaces over Type Aliases for Objects:**
```typescript
// GOOD
interface User {
  id: number;
  name: string;
}

// Acceptable for unions
type Status = 'active' | 'inactive';
```

**Use Readonly for Immutable Data:**
```typescript
interface Config {
  readonly apiKey: string;
  readonly timeout: number;
}
```

**Explicit Return Types for Public APIs:**
```typescript
// GOOD
export function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

## Error Handling

**Use Discriminated Unions for Errors:**
```typescript
type Result<T> = 
  | { success: true; data: T }
  | { success: false; error: string };

function process(): Result<Data> {
  try {
    const data = doSomething();
    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

**Never Ignore Promises:**
```typescript
// BAD
async function init() {
  loadData(); // Promise ignored
}

// GOOD
async function init() {
  await loadData();
}
```

## Review Checklist

- [ ] Functions have explicit return types
- [ ] No implicit `any` types
- [ ] Proper null/undefined handling
- [ ] Readonly used where appropriate
- [ ] Naming conventions followed
- [ ] Interfaces preferred over type aliases for objects
- [ ] Error handling is explicit
- [ ] Promises are properly awaited



### security/no-secrets



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



### security/input-validation



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



### architecture/microservices



# Rule: Microservices Architecture

Guidelines for designing, implementing, and reviewing microservices-based systems.

## Service Boundaries

**Single Responsibility:**
- Each service should have one clear purpose
- Services should be loosely coupled
- Avoid shared databases between services

**Domain-Driven Design:**
- Align service boundaries with business domains
- Use bounded contexts to define service scope
- Services should own their data

## Communication

**Inter-Service Communication:**
- Prefer async messaging (queues, events) over sync calls
- Use circuit breakers for external service calls
- Implement proper timeout and retry strategies

**API Design:**
- Use RESTful or GraphQL APIs consistently
- Version APIs to allow independent deployment
- Document APIs with OpenAPI/Swagger

## Data Management

**Database per Service:**
- Each service owns its database
- No direct database access between services
- Use APIs or events for data sharing

**Event Sourcing:**
- Consider event sourcing for audit trails
- Use CQRS when read/write patterns differ significantly

## Deployment

**Containerization:**
- Containerize all services
- Use Docker or similar container runtime
- Keep images small and secure

**Orchestration:**
- Use Kubernetes or similar for orchestration
- Implement health checks and readiness probes
- Configure proper resource limits

## Observability

**Logging:**
- Centralized logging (ELK stack, Loki)
- Correlation IDs across service calls
- Structured logging format

**Monitoring:**
- Metrics collection (Prometheus, Grafana)
- Distributed tracing (Jaeger, Zipkin)
- Alerting on critical thresholds

## Review Checklist

- [ ] Service boundaries align with business domains
- [ ] Services are loosely coupled
- [ ] Database per service pattern followed
- [ ] Async communication preferred
- [ ] APIs are documented and versioned
- [ ] Proper error handling and retries
- [ ] Health checks implemented
- [ ] Observability (logs, metrics, traces)



### performance/efficiency



# Rule: Performance Efficiency

Guidelines for writing efficient, performant code.

## Algorithmic Efficiency

**Time Complexity:**
- Be aware of Big O complexity
- Prefer O(log n) over O(n) when possible
- Avoid O(n²) or worse for large datasets

**Space Complexity:**
- Minimize memory usage
- Use generators for large datasets
- Avoid unnecessary data copying

## Database Performance

**Query Optimization:**
- Use indexes appropriately
- Avoid N+1 queries
- Select only needed columns
- Use EXPLAIN to analyze queries

**Connection Management:**
- Use connection pooling
- Keep connections short-lived
- Handle connection errors gracefully

## Caching

**When to Cache:**
- Expensive computations
- Database query results
- External API responses

**Cache Strategies:**
- TTL (Time To Live) for time-based expiration
- LRU (Least Recently Used) for size-limited caches
- Cache invalidation on data changes

## Network Efficiency

**Minimize Requests:**
- Batch operations when possible
- Use pagination for large datasets
- Compress request/response bodies

**Asynchronous Operations:**
- Use async/await for I/O operations
- Don't block the event loop
- Implement proper timeout handling

## Resource Management

**Memory:**
- Close files and connections properly
- Clear references to allow GC
- Use streams for large files

**CPU:**
- Offload heavy computation to worker threads
- Use efficient data structures
- Profile to identify bottlenecks

## Review Checklist

- [ ] Time complexity is appropriate for data size
- [ ] Database queries are optimized
- [ ] No N+1 query problems
- [ ] Caching used where beneficial
- [ ] Network requests are batched
- [ ] Async operations don't block
- [ ] Resources are properly released
- [ ] No obvious memory leaks


