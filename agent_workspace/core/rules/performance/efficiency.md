---
name: efficiency
description: Performance optimization and efficiency guidelines
---

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
