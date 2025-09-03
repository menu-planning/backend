# Meal Menu Planner (WIP)

> **Status:** Experimental — AWS infrastructure (API Gateway, database, etc.) lives in a separate repository.  
> **Local HTTP server:** not available yet. A FastAPI shim is planned to enable local runs.  
> **Focus:** backend design and tests.

This service helps create, organize, and distribute meal menus with an emphasis on nutrition (macros, constraints, substitutions). It began as a study project inspired by *Architecture Patterns for Python* and evolved through multiple deployments and runtimes.

---

## What this repository demonstrates

- **Ports & Adapters (service-first):** domain and services remain free of I/O.
- **AnyIO async** with deterministic testing.
- **SQLAlchemy Declarative ORM** with **explicit mappers** between domain and ORM models.
- **Pydantic** models at the edges for validation and serialization (kept out of the domain).
- **End-to-end Lambda tests** using an in-process **API Gateway v2** event and a **Cognito Stubber** (no production code changes).

---

## Architecture (at a glance)

```
[ Entry (Lambda Handler) ]
           │
           ▼
[ Middleware (auth, logging, error handling) ]
           │
           ▼
[ API Schema Validation ]
           │
           ▼
[ Services / Use-Cases (AnyIO) ]
           │ via Ports (UnitOfWork, Repositories, Bus)
           ▼
[ Adapters: SQLAlchemy repos, Mappers, etc. ]
           │
           ▼
[ Database / External Services ]

Pydantic lives at I/O boundaries (validation/serialization).
Explicit mappers (domain ↔ ORM) keep the domain persistence-agnostic.
```

---

## Tech stack

- Python 3.12+
- AnyIO (async)
- SQLAlchemy (Declarative ORM)
- Alembic (database migrations)
- Pydantic v2
- pytest, pytest-anyio, ruff, black
- Dependency management: **uv**
- Cloud runtime: **AWS Lambda** (Cognito stubbed in tests)

---

## Repository layout

```
src/
  contexts/
    <bounded_context>/
      aws_lambda/            # Lambda entrypoints (HTTP/API GW shape)
      core/                  
        domain/              # entities, value objects, commands, events (pure Python)
        services/            # uow, message bus, use cases (command/event handlers)
        adapters/            # ORM models, repositories, mappers, api schemas
        bootstrap/           # dependency injection container and bootstrap function
tests/                       # Mirror src/ structure but with tests
  conftest.py                # shared fixtures (DB, fakes, stubbed Cognito)
```

---

## Quickstart (tests only, for now)

> Local server run is not available yet; use tests to exercise behavior and Lambda entrypoints.

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker (for local PostgreSQL database)

### Using uv
```bash
# install dependencies
uv sync

# call commands (python, ruff, alembic, etc.)
uv run <command>
```

### Database Setup
```bash
# Start PostgreSQL container
docker run -d --name postgres-dev --env-file .env -p 5432:5432 postgres

# Run database migrations
uv run alembic upgrade head
```

### Configuration
```bash
cp .env.development .env
```

---

## E2E tests: Lambda (in-process)

- Tests call the **real Lambda handler** with an **API Gateway v2**-style event.
- Cognito calls are intercepted with **botocore Stubber**; production code remains unchanged.
- Handy filter:
```bash
uv run pytest -m e2e -k lambda -q
```

---

## Evolution & Key Learnings (short case study)

> Goal: nutrition-aware menu planning. This project doubled as a study of architecture and deployment. Each milestone includes what I learned and the trade-offs I saw.

### v0 — Flask prototype with hand-rolled JWT
- **Why:** follow the book’s structure and build a thin vertical slice.
- **Learning:** custom JWT verification works but is fragile and high-maintenance.
- **Trade-off:** app-managed auth increases attack surface and cognitive load.
- **Today:** prefer **API Gateway authorizers** for managed verification.

### v1 — PostgreSQL
- **Why:** relationships and complex queries; a **restricted schema** helps early modeling and learning.
- **Learning:** relational constraints surface mistakes early; SQL shines for aggregations and joins.
- **Trade-off:** migrations and schema evolution add ceremony; long-term payoff in data quality.

### v2 — Docker (DB first, then app)
- **Why:** reproducible environments and local parity.
- **Learning:** image size, caching, and base image choice matter for iteration speed.
- **Trade-off:** build time and cache invalidation friction.

### v3 — Async + FastAPI (AnyIO)
- **Why:** concurrency, IO efficiency, and modern Python server support.
- **Learning:** “async in Python is all or nothing”; every third-party call and boundary must be async-aware. This pushed me deeper into the interpreter, event loop, and cancellation semantics.
- **Trade-off:** higher complexity in adapters and tests; better throughput/latency when done right.

### v4 — DigitalOcean (managed Postgres + droplet)
- **Why:** get something hosted quickly.
- **Learning:** basic ops (SSH, systemd, logs) and operational hygiene; managed DB reduces toil.
- **Trade-off:** I still owned patching and monitoring on the droplet.

### v5 — Kubernetes (Helm, RabbitMQ, Prometheus, Grafana, Loki, Vault operator, Nginx Ingress, cert-manager)
- **Why:** explore production-grade orchestration and observability.
- **Learning:** difficult to debug orchestration issues; understanding why a resource/artifact wouldn’t start or would crash was non-trivial. I learned about brokers, metrics/logging, ingress, TLS—and how complexity and cost can grow quickly. Running Postgres **inside** the cluster looked risky without deep expertise.
- **Trade-off:** big power, big complexity. Great learning, but not the simplest way to ship a small solo app.

### v6 — AWS Lambda (serverless)
- **Why:** scale-to-zero, pay-for-use, reduced ops burden.
- **Learning:** architecture paid off—moving from FastAPI to Lambda required minimal changes because the **services and ports remained stable**. I also learned that cold starts (especially in Python) can affect perceived latency on the frontend.
- **Trade-off:** packaging size and dependency graph matter; cold starts can sting.
- **Mitigations:** provisioned concurrency on hot paths; smaller packages and fewer heavy imports; warm-up pings; caching across invocations; offload token verification to an API Gateway authorizer where possible.

### Other architecture learnings
- **Bounded contexts:** defining the right boundaries is hard. It’s easy to split into microservices slices instead of true contexts. Real constraints matter: large aggregates (e.g., clients → menus → meals → recipes) can lead to heavy in-memory graphs; referencing by id can help but introduces coordination concerns.
- **Domain ↔ SQLAlchemy mapping:** not trivial. Session identity maps, integrity constraints, and merges require care (checking for existing instances, handling detached objects, updating relationships). Integration tests are essential.
- **Anemic models:** when domain objects devolve into data bags with behavior pushed outward, the architecture can likely be simpler. For some areas, **CRUD may be enough**.

**Net effect:** Ports & Adapters with explicit mappers gave me **low switching cost** between runtimes (FastAPI ⇄ Lambda). I can add a FastAPI shim later and keep the Lambda endpoints in parallel.

---

## What runs today

- **Local HTTP server:** not yet (infra repo required for full deployment; FastAPI shim planned).
- **AWS Lambda deployment:** Optimized with container-scoped caching for 80-90% cache hit rates.
- **Proof via tests:**
  - Unit tests (services and domain via fakes) are fast and deterministic.
  - Integration tests verify repository/UoW behavior and ORM mappings against a real engine.
  - Lambda E2E tests invoke real handlers with API Gateway events; Cognito calls are stubbed.
  - Cache performance tests verify container-scoped caching behavior and statistics tracking.

---

## Testing strategy & commands

- **Unit (default):** services and domain via fakes, no I/O.
- **Integration:** repositories, ORM mappings, UoW with a real DB engine.
- **End-to-end:** Lambda in-process (API GW events) with Cognito stubbed.

### Test Setup
```bash
# Copy test environment configuration
cp .env.test .env

# Source environment variables
source ./scripts/setenvs.sh
```

### Running Tests
```bash
uv run python -m pytest tests/ -q                        # unit
uv run python -m pytest tests/ --integration -q         # integration
uv run python -m pytest tests/ --e2e -q                 # end-to-end
uv run python -m pytest tests/ --e2e --slow -q      # opt-in slow/perf
```

---

## Caching Architecture

### Current Caching Systems
- **Configuration**: `@lru_cache` on settings functions (thread-safe, function-level)
- **Authentication**: Simple dict cache in `UnifiedIAMProvider` (not thread-safe)
- **Entities**: `@cached_property` on computed properties (✅ instance-level, thread-safe)
- **Repositories**: Placeholder for future cache backend implementation

### Thread Safety Status
- **Lambda (Current)**: ✅ Single-threaded per container, no thread safety needed
- **FastAPI (Future)**: ⚠️ Multi-threaded, requires request-scoped authentication middleware
- **MessageBus**: ✅ Safe (new instances per request via dependency injection)
- **UnitOfWork**: ✅ Safe (new instances per request via dependency injection)
- **Authentication**: ❌ **CRITICAL** - shared cache across threads causes race conditions

### Caching Strategy Recommendations
- **For Lambda**: Current approach is optimal (container-scoped, simple dict)
- **For FastAPI**: Request-scoped authentication middleware + `cachetools.TTLCache`
- **For Entities**: Current `@cached_property` approach is optimal (instance-level, thread-safe)
- **For Configuration**: Current `@lru_cache` approach is correct and thread-safe

---

## Current Architecture Decisions

### Authentication & Caching
- **Current**: AWS Lambda with container-scoped caching for optimal performance
- **Performance**: 80-90% cache hit rate, ~0.1-0.2 IAM calls per request (vs 1 call per request previously)
- **Thread Safety**: Not required for Lambda (single-threaded per container)
- **Monitoring**: Built-in cache statistics and hit rate tracking via `get_cache_stats()`

### Future Considerations
- **FastAPI Support**: Request-scoped authentication middleware required (CRITICAL)
- **Thread Safety**: Authentication cache is the primary concern (not MessageBus/UnitOfWork)
- **Advanced Caching**: Bounded cache with LRU eviction for long-running processes
- **Key Rotation**: Automatic handling for native JWT validation in FastAPI
- **Context-Aware**: Conditional caching strategies based on deployment context

---

## Roadmap (short)

### Authentication & Performance Optimizations
- [x] **Container-scoped caching** for AWS Lambda (80-90% cache hit rate, reduced IAM calls)
- [x] **Cache performance monitoring** with built-in statistics and hit rate tracking
- [ ] **FastAPI authentication middleware** with request-scoped instances (CRITICAL for thread safety)
- [ ] **Bounded cache with LRU eviction** for long-running FastAPI processes
- [ ] **Key rotation handling** for native JWT validation in FastAPI

### Core Features
- [ ] Add **FastAPI shim** to enable local HTTP runs while keeping Lambda endpoints
- [ ] Seed realistic data and finalize a polished end-to-end "create menu with macronutrient targets" flow
- [ ] Add **contract tests** to keep fake and real port implementations aligned
- [ ] Introduce **pagination and filtering** on list endpoints
- [ ] Harden security (headers, tenant walls/claims)
- [ ] Small **CLI** for local ops (seed DB, recalc nutrition)

### Architecture Evolution
- [ ] **Request-scoped authentication middleware** for FastAPI deployment (CRITICAL)
- [ ] **Thread safety audit completion** - authentication middleware is the main issue
- [ ] **Performance benchmarking** comparing Lambda vs FastAPI performance characteristics
- [ ] **Advanced monitoring** for cache performance across different deployment contexts
- [x] **MessageBus/UnitOfWork thread safety** ✅ already safe (new instances per request)
- [x] **Entity caching audit** ✅ already optimal with @cached_property (instance-level, thread-safe)
- [ ] **Thread safety documentation** comprehensive guide for multi-threaded vs single-threaded patterns

### Known limitations
- No local server run yet; infra repo is required for a full deployment.
- Lambda E2E uses botocore Stubber for Cognito; no real user pool in tests.
- Pagination and complex querying are in progress.
- Database migrations are managed with Alembic and currently tuned for development.
- **FastAPI migration blocked** by authentication middleware thread safety issues.

---

## License

MIT — see `LICENSE`.

---

