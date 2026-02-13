---
name: github-issue-resolution
description: Investigates and resolves GitHub issues through systematic debugging and root cause analysis
mcp_servers:
  - github
  - git
allowed_tools:
  - github_*
  - git_*
  - Bash(git:*)
  - Read
  - Grep
  - Write
  - Edit
---

# GitHub Issue Resolution

Expertly investigates, debugs, and resolves GitHub issues through systematic analysis and implementation.

## When to Use

- A user reports a bug via GitHub issue
- Need to investigate a reported problem
- Implementing a fix for an open issue
- Creating reproduction scripts for bugs

## Steps

### 1. Discovery

Read the GitHub issue to understand:
- What behavior is expected
- What behavior is actually happening
- Steps to reproduce (if provided)
- Environment details
- Any error messages or logs

### 2. Codebase Search

Search for relevant code:
- Files mentioned in the issue
- Error messages or keywords
- Related functionality
- Recent changes that might have introduced the bug

### 3. Root Cause Analysis

Analyze the issue:
- Trace through the code path
- Identify where the bug occurs
- Understand why it's happening
- Consider edge cases

### 4. Reproduction

Create a minimal reproduction:
- Write a test that fails due to the bug
- Or create a script that demonstrates the issue
- Keep it as simple as possible

### 5. Implementation

Implement the fix:
- Make the minimal necessary changes
- Ensure the fix addresses the root cause
- Consider side effects
- Follow existing code style

### 6. Verification

Verify the fix:
- Run the reproduction script - it should now pass
- Run existing tests - they should still pass
- Consider adding a regression test
- Test edge cases

### 7. Pull Request

Create a pull request:
- Reference the issue: `Fixes #123`
- Describe what was changed and why
- Include test results
- Request review if appropriate

## Best Practices

- Always start by fully understanding the issue
- Don't guess - verify your assumptions with code
- Write tests for bugs to prevent regression
- Keep fixes minimal and focused
- Document any non-obvious changes
