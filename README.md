# CareerPilot AI

> An AI-powered career copilot that turns a resume and a few job preferences into explainable, reviewable job matches.

CareerPilot AI is a full-stack application for personalized job discovery. It parses and verifies a candidate's resume, searches multiple job sources, analyzes job descriptions, ranks roles against the candidate profile, and explains why each role is a match. A human review step keeps the candidate in control: users can approve results or refine the search and run another iteration.

## Why this project stands out

- **Agentic workflow:** LangGraph coordinates role expansion, job search, job-description analysis, matching, explanations, and human review.
- **Human-in-the-loop by design:** The workflow pauses before final approval and can either finish, re-search, or re-rank based on user feedback.
- **Practical AI product engineering:** Resume parsing, structured profile storage, streaming progress updates, caching, guardrails, authentication, and deployment are connected into one usable flow.
- **Resilient integrations:** Adzuna and RemoteOK searches run concurrently through MCP tools; individual source failures do not discard the rest of the search.
- **Production-minded delivery:** PostgreSQL migrations, Redis-backed caching, rate limiting, Playwright E2E coverage, and CI-gated EC2 deployment are included.

## Product flow

```mermaid
flowchart LR
    A[Create account or sign in] --> B[Upload PDF resume]
    B --> C[Parse and verify profile]
    C --> D[Choose role, locations, salary, remote preference]
    D --> E[Search and rank jobs]
    E --> F[Review match explanations]
    F --> G{Candidate decision}
    G -->|Approve| H[Start applying]
    G -->|Refine role or location| D
    G -->|Adjust salary or remote preference| E
```

## Architecture

```mermaid
flowchart TB
    User[Candidate] --> UI[React + TypeScript + Vite]
    UI --> API[FastAPI REST API]
    API --> Auth[JWT authentication]
    API --> Profile[Resume parser and verifier]
    API --> Graph[LangGraph orchestration]

    Profile --> DB[(PostgreSQL)]
    Graph --> Supervisor[Supervisor / role expansion]
    Supervisor --> Search[Concurrent job search]
    Search --> MCP[MCP job-board server]
    MCP --> Adzuna[Adzuna]
    MCP --> RemoteOK[RemoteOK]
    Search --> Analysis[Job description analysis]
    Analysis --> Cache[(Upstash Redis cache)]
    Analysis --> Matching[Profile matching and ranking]
    Matching --> Explanation[Match explanations]
    Explanation --> HITL[Human review checkpoint]
    HITL --> UI

    API --> DB
    Graph --> Checkpoint[(PostgreSQL LangGraph checkpoints)]
```

## LangGraph workflow

```mermaid
flowchart LR
    S[Supervisor] --> J[Job search]
    J --> A[JD analysis]
    A --> M[Matching and ranking]
    M --> X[Explanations]
    X --> H[Human review interrupt]
    H -->|Approve| End((End))
    H -->|Role or location changed| S
    H -->|Salary or remote preference changed| M
```

## Core capabilities

### Candidate profile

- Email/password registration and JWT-based login
- PDF resume upload with file-size, page-count, text-quality, and prompt-injection guardrails
- Structured extraction of basics, skills, experience, education, and projects
- Resume verification flags surfaced by the backend

### Personalized job discovery

- Role and location search with salary and remote-work preferences
- Supervisor node expands search terms from the candidate profile
- Concurrent searches across Adzuna and RemoteOK through an MCP server
- Cross-source deduplication using normalized title and company keys
- Streaming progress updates for long-running searches

### Explainable review

- Job-description analysis and profile-based ranking
- Per-job explanations for why a role matches
- Human-in-the-loop checkpoint before approval
- Targeted refinement: source-affecting changes trigger a new search, while ranking-only changes reuse existing listings
- Session persistence through LangGraph PostgreSQL checkpoints

## Technology stack

| Area | Technologies |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, React Router, TanStack Query, Playwright |
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic |
| AI orchestration | LangGraph, LangChain, Groq, Google Gemini |
| Integrations | MCP, Adzuna, RemoteOK |
| Data and performance | PostgreSQL, asyncpg, LangGraph Postgres checkpointer, Upstash Redis |
| Security and reliability | JWT, Argon2 password hashing, rate limiting, input guardrails |
| Delivery | GitHub Actions, SSH deployment to AWS EC2, Nginx, systemd |

## Repository structure

```text
careerpilot_ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph nodes, routing, state, and HITL flow
│   │   ├── api/             # Authentication routes
│   │   ├── core/            # Parsing, matching, caching, security, guardrails
│   │   ├── mcp_servers/     # Job-board MCP server and client
│   │   └── models/          # SQLAlchemy and Pydantic models
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed API clients
│   │   ├── components/      # Job cards, score ring, inputs, route protection
│   │   ├── context/         # Auth and search session state
│   │   └── pages/            # Auth, dashboard, search, review, upload views
│   ├── tests/               # Playwright E2E tests
│   └── package.json
└── .github/workflows/
    ├── e2e.yml              # CI: backend, services, migrations, E2E tests
    └── cd.yml               # CD: deploys after successful CI on main
```

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 24+
- PostgreSQL 15+
- Redis-compatible cache (optional for local development)
- API credentials for Groq, Gemini, Adzuna, and RemoteOK as applicable

### 1. Clone and configure

```bash
git clone <repository-url>
cd careerpilot_ai
```

Create `backend/.env` with values for your environment:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/careerpilot
JWT_SECRET_KEY=replace-with-a-long-random-secret
GROQ_API_KEY=your-groq-key
GEMINI_API_KEY=your-gemini-key
ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key
ADZUNA_COUNTRY=in
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Optional Redis cache
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
```

Never commit real credentials. `backend/.env` is ignored by Git.

### 2. Start the backend

PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

The API health endpoint is available at `http://localhost:8000/health`.

### 3. Start the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Testing and quality checks

Backend tests:

```powershell
cd backend
pytest
```

Frontend lint and production build:

```powershell
cd frontend
npm run lint
npm run build
```

Frontend E2E tests require the backend and test services configured. The CI workflow provisions PostgreSQL and Redis, runs migrations, starts the API, performs a health check, installs Playwright browsers, and runs the browser suite:

```powershell
cd frontend
npx playwright install
npx playwright test
```

## CI/CD

The delivery pipeline is intentionally gated:

```mermaid
flowchart LR
    Push[Push or pull request] --> CI[GitHub Actions: E2E Tests]
    CI -->|Success on main| CD[GitHub Actions: CD]
    CI -->|Failure| Stop[No deployment]
    CD --> SSH[SSH to AWS EC2]
    SSH --> Deploy[Pull code, migrate DB, build frontend]
    Deploy --> Restart[Restart backend and reload Nginx]
    Restart --> Health[Backend health check]
```

- **CI:** PostgreSQL and Redis services, backend setup, Alembic migrations, API health check, and Playwright tests.
- **CD:** Triggered only after the `E2E Tests` workflow completes successfully for `main`; manual dispatch remains available.
- **Deployment target:** AWS EC2 with systemd-managed backend and Nginx-served frontend.
- **Deployment verification:** The workflow waits for `/health` before reporting success.

Required GitHub repository secrets for deployment:

- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`

## API surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create an account and receive a token |
| `POST` | `/api/auth/login` | Authenticate with OAuth2 form credentials |
| `GET` | `/api/profile/status` | Read the current candidate profile summary |
| `POST` | `/api/resume/upload` | Parse and verify a PDF resume |
| `POST` | `/api/jobs/search` | Run a complete job search |
| `POST` | `/api/jobs/search/stream` | Run a search with progress events |
| `POST` | `/api/jobs/resume` | Approve or refine a paused search |
| `GET` | `/health` | Service health check |

## Engineering highlights

- Async FastAPI endpoints and async SQLAlchemy sessions
- Typed React API clients and query-based server state
- LangGraph checkpointing for resumable search sessions
- MCP tool boundary for external job-board integrations
- Concurrent fan-out with graceful per-source failure handling
- Deterministic job deduplication to improve cache reuse
- Rate limits on authentication, resume upload, and job-search endpoints
- Database migrations tracked with Alembic
- Automated browser coverage and deployment health verification

## Project status

CareerPilot AI is an active portfolio project demonstrating end-to-end AI application engineering: product workflow design, agent orchestration, external integrations, persistence, security controls, testing, and deployment automation.
