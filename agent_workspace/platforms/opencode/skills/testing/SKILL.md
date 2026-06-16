---
name: testing
description: Creates comprehensive test suites following best practices for the target language and framework
mcp_servers:
  - git
allowed_tools:
  - Read
  - Grep
  - Write
  - Bash
---

# Testing

Creates thorough, maintainable test suites that ensure code correctness and prevent regression.

## When to Use

- Adding tests for new features
- Writing tests for bug fixes
- Improving test coverage
- Refactoring existing tests

## Steps

### 1. Analyze Code Under Test

Understand what needs testing:
- What is the public interface?
- What are the expected behaviors?
- What are the edge cases?
- What are the error conditions?
- Are there dependencies to mock?

### 2. Identify Test Framework

Determine the appropriate testing framework:
- JavaScript/TypeScript: Jest, Vitest, Mocha
- Python: pytest, unittest
- Go: testing package
- Rust: built-in test framework
- Java: JUnit, TestNG

### 3. Plan Test Cases

Design comprehensive test coverage:

**Happy Path:**
- Normal operation with valid inputs
- Expected outputs for typical cases

**Edge Cases:**
- Boundary values
- Empty inputs
- Maximum/minimum values
- Null/undefined handling

**Error Cases:**
- Invalid inputs
- Exception handling
- Resource unavailability
- Network failures

### 4. Write Tests

Follow test structure:
```
Arrange - Set up test data and mocks
Act     - Execute the code under test
Assert  - Verify expected outcomes
```

**Best Practices:**
- One concept per test
- Descriptive test names
- Use table-driven tests for multiple cases
- Mock external dependencies
- Keep tests independent

### 5. Verify Coverage

Check test effectiveness:
- Run the tests - they should pass
- Verify edge cases are covered
- Check error paths are tested
- Aim for meaningful coverage, not just line count

### 6. Documentation

Document the tests:
- Explain complex setup
- Document why certain cases are tested
- Note any testing trade-offs

## Test Types

**Unit Tests:**
- Test individual functions/methods
- Fast and isolated
- Mock dependencies

**Integration Tests:**
- Test component interactions
- Use real dependencies where appropriate
- Slower but more realistic

**End-to-End Tests:**
- Test complete user flows
- Most realistic but slowest
- Usually fewer in number

## Example Test Structure

```python
# Python example with pytest
def test_function_name_scenario():
    # Arrange
    input_data = ...
    expected_output = ...
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == expected_output
```

```javascript
// JavaScript example with Jest
describe('FunctionName', () => {
  test('should handle normal case', () => {
    // Arrange
    const input = ...;
    const expected = ...;
    
    // Act
    const result = functionUnderTest(input);
    
    // Assert
    expect(result).toBe(expected);
  });
  
  test('should handle edge case', () => {
    // ...
  });
});
```
