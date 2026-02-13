---
name: code-review
description: Performs thorough code review focusing on correctness, security, performance, and maintainability
mcp_servers:
  - git
custom_tools:
  - complexity-analyzer
allowed_tools:
  - Read
  - Grep
  - git_*
---

# Code Review

Performs comprehensive code reviews to ensure code quality, correctness, and maintainability.

## When to Use

- Reviewing a pull request
- Auditing existing code
- Pre-commit review
- Mentoring and knowledge sharing

## Steps

### 1. Understanding

First, understand the context:
- What is the purpose of this change?
- What problem does it solve?
- Are there related issues or PRs?
- What is the scope of changes?

### 2. Architecture & Design

Review the overall approach:
- Does the solution fit the architecture?
- Are there simpler alternatives?
- Is the abstraction level appropriate?
- Are there potential side effects?

### 3. Correctness

Verify the implementation:
- Does it solve the stated problem?
- Are there edge cases not handled?
- Are there off-by-one errors?
- Is error handling adequate?

### 4. Security

Check for security issues:
- Input validation
- Injection vulnerabilities
- Authentication/authorization
- Data exposure

### 5. Performance

Consider performance implications:
- Algorithmic complexity
- Resource usage
- Database queries
- Network calls

### 6. Maintainability

Assess code quality:
- Readability and clarity
- Documentation
- Test coverage
- Code duplication

### 7. Feedback

Provide constructive feedback:
- Be specific and actionable
- Explain the 'why', not just the 'what'
- Balance critical feedback with positive notes
- Suggest improvements, don't just point out problems

## Review Checklist

**Functionality:**
- [ ] Code achieves its stated purpose
- [ ] Edge cases are handled
- [ ] Error cases are handled
- [ ] No obvious bugs

**Security:**
- [ ] Input is validated
- [ ] No secrets in code
- [ ] Proper access controls

**Performance:**
- [ ] No obvious bottlenecks
- [ ] Resource usage is reasonable

**Quality:**
- [ ] Code is readable
- [ ] Comments explain 'why', not 'what'
- [ ] Naming is clear
- [ ] Tests are included
