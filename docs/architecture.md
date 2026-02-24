# Architecture Documentation — LeetCode Clone (Remote Code Execution Engine)

> **Version:** Current (v1) → Ideal (v2)  
> **Last updated:** 2026-02-24

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Current Architecture (v1)](#2-current-architecture-v1)
   - [System Diagram](#21-system-diagram)
   - [Component Breakdown](#22-component-breakdown)
   - [Request Lifecycle](#23-request-lifecycle)
   - [Data Model](#24-data-model)
   - [Security Model](#25-security-model)
   - [Strengths](#26-strengths)
   - [Bottlenecks & Weaknesses](#27-bottlenecks--weaknesses)
3. [Ideal Architecture (v2)](#3-ideal-architecture-v2)
   - [System Diagram](#31-system-diagram)
   - [What Changes and Why](#32-what-changes-and-why)
   - [Component Breakdown](#33-component-breakdown)
   - [New Request Lifecycle](#34-new-request-lifecycle)
   - [Scalability Profile](#35-scalability-profile)
4. [Migration Roadmap](#4-migration-roadmap)
5. [Tech Stack Summary](#5-tech-stack-summary)

---

## 1. Project Overview

This project is a **full-stack online judge** modelled after platforms like LeetCode and HackerRank. Users can write Python or C++ code in a browser-based editor, submit it, and receive a verdict (Accepted / Failed / Time Limit Exceeded) evaluated against hidden server-side test cases.

Core design priorities:
- **Security** — untrusted code must never affect the host system
- **Correctness** — test cases are hidden and stored server-side
- **Extensibility** — support multiple languages via a clean factory pattern

---

## 2. Current Architecture (v1)

### 2.1 System Diagram

> See [`arch.mmd`](./arch.mmd) for the Mermaid source.

```
React Frontend (Monaco Editor)
        │
        │  POST /submit {code, language, problem_id}
        ▼
FastAPI Backend (main.py)
        │
        ├──► SQLite DB ──► fetch hidden test cases
        │
        ├──► Generate runner script (runner.py / runner.cpp)
        │        written to a temp directory on host
        │
        ├──► Docker SDK ──► spin up Alpine container
        │        mount temp dir as /app
        │        run script → writes /app/output.json
        │        wait(timeout=2s) ──► kill if TLE
        │
        ├──► Read output.json from host temp dir
        │
        ├──► Save Submission record to SQLite
        │
        └──► Return JSON result to frontend
```

### 2.2 Component Breakdown

| File | Role |
|---|---|
| `main.py` | FastAPI app — all routes, script generation, Docker orchestration |
| `models.py` | SQLAlchemy ORM models: `Problem`, `TestCase`, `Submission` |
| `database.py` | SQLite engine + session factory |
| `Dockerfile` | Python Alpine sandbox image (`python-sandbox`) |
| `Dockerfile.cpp` | Alpine + g++ sandbox image (`cpp-sandbox`) |
| `frontend/src/App.jsx` | React UI with Monaco editor, submission handler, history panel |

### 2.3 Request Lifecycle

```
1. User writes code in Monaco Editor
2. Clicks Submit → Axios POST /submit {problem_id, language, code}
3. FastAPI:
   a. Query Problem table → get function_name
   b. Query TestCase table → get all test cases (including hidden)
   c. Call generate_test_script() or generate_cpp_script()
      → injects user code + test cases into a wrapper template
   d. Write runner.py / runner.cpp into a host tempdir
4. Docker SDK:
   a. client.containers.run(image, command, volumes={tempdir:/app})
   b. detach=True → container runs asynchronously
   c. container.wait(timeout=2) → BLOCKS thread up to 2 seconds
   d. On timeout → container.kill() → return TLE
5. Read output.json from host tempdir
6. container.remove() → cleanup
7. Save Submission(problem_id, user_code, status) to SQLite
8. Return result JSON to frontend
```

### 2.4 Data Model

```
┌─────────────┐       ┌──────────────┐       ┌─────────────────┐
│   Problem   │1    * │   TestCase   │       │   Submission    │
│─────────────│───────│──────────────│       │─────────────────│
│ id          │       │ id           │       │ id              │
│ title       │       │ problem_id   │       │ problem_id      │
│ description │       │ inputs (JSON)│       │ user_code (TEXT)│
│ difficulty  │       │ expected (J.)│       │ status (STRING) │
│ function_   │       │ is_hidden    │       └─────────────────┘
│   name      │       └──────────────┘
└─────────────┘
```

Key design note: `inputs` and `expected_output` are stored as **JSON columns**, allowing flexible test case shapes (single int, list, tuple, etc.) without schema changes.

### 2.5 Security Model

| Control | Implementation | Protection |
|---|---|---|
| Container isolation | `docker.containers.run()` with Alpine base | User code can't access host filesystem (beyond mounted app dir) |
| Network disabled | `network_disabled=True` | No exfiltration, no external HTTP calls |
| Memory cap | `mem_limit="128m"` | No OOM attacks |
| CPU cap | `cpu_quota=50000` (50% of one core) | No CPU starvation |
| Time limit | `container.wait(timeout=2)` → `container.kill()` | No infinite loops |
| Hidden test cases | Stored in DB, never sent to client | No hardcoded-answer cheating |
| Ephemeral containers | `auto_remove=False` + manual `container.remove()` | No persistent state across runs |

### 2.6 Strengths

- **Solid security posture** — multiple layered controls (network, memory, CPU, timeout)
- **No shared state** — each submission gets a fresh container
- **Clean factory pattern** — language routing is easy to extend
- **Hidden test cases** — evaluated server-side, clients never see them
- **Monaco editor** — professional VS Code-quality editing experience
- **Submission history** — past code and verdicts persisted and retrievable

### 2.7 Bottlenecks & Weaknesses

#### 🔴 Critical

**Synchronous blocking execution**
```python
container.wait(timeout=2)  # Blocks the FastAPI thread
```
Every `/submit` call blocks a thread for up to 2 seconds. With FastAPI's default thread pool (~40 threads), only ~40 concurrent submissions are possible before requests queue up. Under real traffic this is a hard ceiling.

**No job queue**
All 100 concurrent submissions spin up 100 Docker containers simultaneously. This creates memory/CPU spikes that will OOM the host.

**SQLite under concurrent writes**
SQLite is single-writer. Concurrent submission saves will serialize or raise `OperationalError: database is locked`.

#### 🟡 Moderate

**Docker cold-start latency (~200–500ms per submission)**
Each container starts from scratch. No pooling or pre-warming.

**Temp directory in project root**
```python
current_dir = os.getcwd()
with tempfile.TemporaryDirectory(dir=current_dir) as temp_dir:
```
Pollutes the project directory; breaks if the app is running from a read-only path.

**No authentication**
Any client can list problems, submit code, and read submission history. There's no user identity.

**No rate limiting**
A single client can flood the `/submit` endpoint.

#### 🟢 Minor

- No pagination on `/problems` or `/submissions` endpoints
- No structured logging or metrics
- C++ test harness is limited to `int` return types (hardcoded in `generate_cpp_script`)

---

## 3. Ideal Architecture (v2)

### 3.1 System Diagram

> See [`target.mmd`](./target.mmd) for the Mermaid source.

```
React Frontend
        │
        │  POST /submit → returns {job_id}
        │  WebSocket / poll /jobs/{job_id}/status
        ▼
FastAPI (async, stateless, horizontally scalable)
        │
        ├──► PostgreSQL ──► problems, test cases, users, submissions
        │
        ├──► Redis ──────► enqueue job {problem_id, language, code}
        │
        └──► Return {job_id: "abc123", status: "queued"}

Redis Queue
        │
        ├──► Worker 1 (Docker executor)
        ├──► Worker 2 (Docker executor)
        └──► Worker N ...
                │
                ├──► Spin up sandboxed container
                ├──► Execute user code
                ├──► Write result → PostgreSQL (jobs table)
                └──► Publish result event → Redis Pub/Sub

Frontend polls or receives WS push → shows verdict
```

### 3.2 What Changes and Why

| Problem in v1 | Solution in v2 | Benefit |
|---|---|---|
| Blocking `container.wait()` | Async job queue (Redis) | API never blocks; sub-ms response |
| No concurrency control | N configurable workers | Predictable load; easy autoscaling |
| SQLite single-writer | PostgreSQL | True concurrent writes, ACID guarantees |
| No auth | JWT + user accounts | Submissions linked to users |
| No rate limiting | Redis-based token bucket per user | Fair usage enforcement |
| No observability | Structured logs + Prometheus metrics | Debuggable in production |
| Cold container starts | Pre-warmed container pool | Lower p99 latency |

### 3.3 Component Breakdown

#### API Layer (`FastAPI`)
- Fully `async` — no blocking calls
- Stateless — can run behind a load balancer as N replicas
- Responsibilities: auth, validation, DB reads, job enqueue, result polling/streaming
- Auth: JWT access tokens, refresh tokens in httpOnly cookies

#### Job Queue (`Redis` + `ARQ` or `Celery`)
- Submissions are serialized as JSON jobs pushed to a Redis list/stream
- Workers pop jobs, execute, write results, then publish events
- Dead-letter queue for failed jobs

#### Execution Workers
- Python processes (one per CPU core or container)
- Each worker manages its own Docker SDK client
- Pulls a job → runs container → reads output → writes to PostgreSQL
- Optionally: maintain a small pool of pre-started containers to eliminate cold-start

#### Database (`PostgreSQL`)
- New tables: `Users`, `Jobs`
- `Jobs` table tracks: `id`, `status` (queued/running/done), `result` (JSON), timestamps
- Read replicas for heavy query workloads (leaderboards, etc.)

#### Real-time Results (`WebSocket` or Server-Sent Events)
- After submitting, frontend connects to `/ws/jobs/{job_id}`
- Worker publishes to Redis Pub/Sub channel when done
- API server relays to the connected WebSocket client
- Fallback: HTTP polling `/jobs/{job_id}/status` every 500ms

### 3.4 New Request Lifecycle

```
1. User submits code → POST /submit
2. API validates request, checks rate limit (Redis token bucket)
3. API writes Job record to PostgreSQL (status=queued)
4. API pushes job payload to Redis queue
5. API returns {job_id, status: "queued"} immediately (< 5ms)
6. Frontend opens WebSocket on /ws/jobs/{job_id}

--- async, in worker process ---
7. Worker pops job from Redis
8. Updates Job status → "running" in PostgreSQL
9. Generates runner script → writes to /tmp/{job_id}/
10. Spins up Docker container (or checks out pre-warmed one)
11. Waits for completion (non-blocking asyncio.wait_for)
12. Reads output.json, evaluates result
13. Updates Job record → status="done", result=JSON
14. Publishes {job_id, result} to Redis Pub/Sub
--- end worker ---

15. API relay receives Pub/Sub event
16. Pushes result to client WebSocket
17. Frontend displays verdict
```

### 3.5 Scalability Profile

| Metric | v1 (current) | v2 (target) |
|---|---|---|
| Concurrent submissions | ~40 (thread pool limit) | Thousands (queue-backed) |
| Throughput | ~20 submissions/sec | Limited only by worker count |
| DB write concurrency | 1 (SQLite) | Unlimited (PostgreSQL) |
| Horizontal scaling | ❌ Single process | ✅ API + Workers scale independently |
| Container cold-start | 200–500ms always | Near-zero with pre-warming |
| Fault tolerance | If process dies, jobs lost | Jobs survive in Redis/DB |

---

## 4. Migration Roadmap

### Phase 1 — Immediate fixes (no architectural change)
- [ ] Move temp dir from `os.getcwd()` → `/tmp`
- [ ] Fix C++ generator to support non-`int` return types
- [ ] Add pagination to list endpoints
- [ ] Add basic input validation (max code length, language whitelist)

### Phase 2 — Async & Database
- [ ] Replace SQLite with PostgreSQL (SQLAlchemy URL change + migrations via Alembic)
- [ ] Make `/submit` endpoint `async def`
- [ ] Offload `container.wait()` to `asyncio.to_thread` as an interim fix

### Phase 3 — Job Queue
- [ ] Add Redis (Docker Compose service)
- [ ] Integrate ARQ or Celery as the task queue
- [ ] Create a `jobs` table in PostgreSQL
- [ ] `/submit` returns `job_id`; add `/jobs/{id}` polling endpoint

### Phase 4 — Real-time & Auth
- [ ] Add FastAPI WebSocket endpoint for job result streaming
- [ ] Add user registration/login (bcrypt + JWT)
- [ ] Link submissions to users
- [ ] Redis-based rate limiting per user

### Phase 5 — Production Hardening
- [ ] Pre-warmed container pool
- [ ] Structured logging (structlog or JSON logs)
- [ ] Prometheus metrics (submission rate, TLE rate, error rate, execution latency)
- [ ] Docker Compose → Kubernetes manifests (if needed)
- [ ] CI/CD pipeline for automated testing + deployment

---

## 5. Tech Stack Summary

### v1 (Current)

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Monaco Editor, Axios |
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite, SQLAlchemy ORM |
| Code Execution | Docker SDK (Python), Alpine Linux containers |

### v2 (Target)

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Monaco Editor, Axios + WebSocket |
| Backend API | Python, FastAPI (async), Uvicorn + Gunicorn |
| Job Queue | Redis + ARQ (or Celery) |
| Database | PostgreSQL, SQLAlchemy (async) + Alembic migrations |
| Code Execution | Docker SDK, Alpine containers, pre-warmed pool |
| Auth | JWT (PyJWT), bcrypt, httpOnly refresh cookies |
| Observability | structlog, Prometheus, Grafana |
| Deployment | Docker Compose (dev) → Kubernetes (prod) |
