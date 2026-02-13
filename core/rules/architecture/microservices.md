---
name: microservices
description: Guidelines for building and reviewing microservices architecture
---

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
