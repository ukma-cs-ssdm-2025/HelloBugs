# API Quality Attributes

## Performance
- **Target**: 95th percentile response time < 200 ms (GET endpoints)
- **Implementation**:
  - In-memory storage (Python lists) for instant access
  - Linear search by ID (simple O(n) lookups)
  - No database overhead — all operations in RAM
  - Database optimization, indexes, and caching *(planned)*
- **Measurement**: 
  - Load testing with k6 or JMeter under 20–50 concurrent users
  - Monitor p95 latency over 1000+ requests

---

## Security
- **Target**: 100% compliance with OWASP API Security Top 10 (0 critical vulnerabilities)
- **Implementation**:
  - Input validation with Marshmallow on all POST/PUT/PATCH endpoints
  - Email/phone format, date range, and uniqueness checks
  - Booking overlap prevention for data integrity
  - Rate limiting (100 req/min) *(planned)*
  - JWT authentication and HTTPS *(planned)*
- **Measurement**: 
  - Security scanning with OWASP ZAP (target: 0 critical, < 3 medium findings)
  - Manual penetration testing with invalid payloads

---

## Reliability
- **Target**: 99.9% uptime; error rate < 1%
- **Implementation**:
  - Consistent JSON error format and proper HTTP status codes
  - Idempotent booking creation via unique booking code
  - Graceful error handling
  - Health check endpoint *(planned)*
  - Database-level transactions and retry logic *(planned)*
- **Measurement**: 
  - Integration tests (target: 100% pass rate)
  - Uptime monitoring over 30-day period
  - Error rate calculation: (5xx responses / total requests) × 100%

---

## Consistency
- **Target**: 0 duplicate rooms; 0 double-bookings per date range (100% data integrity)
- **Implementation**:
  - Room number uniqueness validation in `rooms.py`
  - Overlap check for booking creation
  - Status-based update restrictions (no edits for COMPLETED/CANCELLED bookings)
  - Database constraints and foreign keys *(planned)*
- **Measurement**: 
  - Integration tests simulating concurrent booking requests (10+ threads)
  - Automated data integrity checks (SQL queries for duplicates)
  - Monitor constraint violation logs

---

## Developer Experience (Usability)
- **Target**: 
  - API documentation coverage: 100% endpoints
  - Average onboarding time for developer integration: < 10 minutes (measured from developer feedback)
  - Swagger UI response time: < 2 seconds
- **Implementation**:
  - Auto-generated OpenAPI 3.0.3 spec (`openapi-generated.yaml`)
  - Interactive Swagger UI at `/api-docs`
  - Descriptive validation error messages
  - Prometheus/Grafana monitoring *(planned)*
- **Measurement**: 
  - Developer onboarding surveys (sample: 3 developers)
  - OpenAPI spec validation (all endpoints documented)
  - Swagger UI usability testing

---

## Trade-offs Analysis

| Quality | Trade-off | Impact | Mitigation |
|----------|-----------|---------|-------------|
| Security (validation) | +20–50 ms latency per request | Low | Optimize validators / skip heavy checks on non-critical endpoints |
| Performance (in-memory data) | Data lost on restart | Dev-only | Migrate to PostgreSQL DB |
| Consistency (conflict check) | O(n) scan through bookings | Slower with large datasets | Add DB indexes and transactions |
| Reliability (detailed errors) | Possible information disclosure | Medium | Sanitize error messages in production |
| Developer Experience (documentation) | Extra maintenance effort | Low | Auto-generate specs and use CI/CD validation |