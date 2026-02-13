---
name: typescript
description: TypeScript coding standards and best practices
---

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
