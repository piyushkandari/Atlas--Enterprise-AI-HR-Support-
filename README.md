# Atlas — Enterprise HR Support Assistant

A conversational HR assistant built as a POC, modeled on enterprise tools
like HCLTech Lumi AI, SAP Joule, and Workday Illuminate.

Ask questions about payslips, leave balances, attendance, holidays,
company policies, and IT helpdesk issues. Every answer is scoped to
**one employee**, whose identity is taken from the login token — the
LLM never sees or chooses a user id.

---

## Architecture

```
┌─────────────────┐   JWT    ┌──────────────────┐   X-API-Key  ┌─────────────┐
│  Streamlit UI   │ ───────► │   bot_backend    │ ───────────► │ mock_hrms   │
│  (frontend/)    │          │   (port 8000)    │              │ (port 8001) │
│  login + chat   │          │  auth, agent,    │              │ fake SAP    │
│                 │          │  RAG, audit log  │              │ SQLite DB   │
└─────────────────┘          └────────┬─────────┘              └─────────────┘
                                      │
                             ┌────────┴─────────┐
                             │  LangGraph agent │
                             │  router + 4      │
                             │  specialists     │
                             └────────┬─────────┘
                                      │
                          ┌───────────┴───────────┐
                          │  Gemini API (LLM)     │
                          │  Gemini embeddings    │
                          │  JSON vector store    │
                          └───────────────────────┘
```

**Three tiers:**

1. **`mock_hrms/`** — FastAPI service on port 8001. Simulates a fake
   SAP / HR backend with its own SQLite DB, protected by a static
   `X-API-Key`. Includes employees, payslips, PF, leave, attendance,
   regularizations, and holidays.
2. **`bot_backend/`** — FastAPI service on port 8000. Handles JWT
   login, the LangGraph agent, RAG, chat history, and audit logging.
   Talks to `mock_hrms` through an `HRSystem` adapter interface, so a
   real SAP client can be swapped in without touching the agent.
3. **`frontend/`** — Streamlit chat UI on port 8501. Login form,
   chat bubbles, session memory, and per-answer feedback (WIP).

---

## Stack

- **Python 3.11+**, **FastAPI**, **SQLAlchemy**, **SQLite**
- **LangGraph** multi-agent pipeline (router + specialists)
- **Gemini** via `langchain-google-genai` (chat + embeddings)
- **Streamlit** UI
- **JWT** auth, **bcrypt** password hashing
- **pypdf** + **fpdf2** for PDF parsing and sample-doc generation

---

## Features

**Read**
- Payslip by month / year
- PF (provident fund) balance
- Leave balances (Casual, Sick, Earned)
- Monthly attendance summary (with MISSING_PUNCH detection)
- Company holidays by range
- Manager and direct reports
- Company policy search with **source PDF + page citations**
- IT knowledge-base search with **source file citations**

**Write** *(two-step, never submitted directly by the LLM)*
- Leave request: preview with day count, balance after, then
  Confirm / Cancel
- Regularization request: same preview + confirm flow

**Ops**
- Every tool call written to an audit log (actor, tool, args — never
  salary values)
- Chat history persisted per session
- Per-user document uploads (scoped RAG)

---

## Security model (the important bit)

The employee code is taken from the **login token by the backend** and
injected into every tool closure at build time. The LLM never receives
or chooses a user id.

**Tools have no user-id parameter.** The LLM literally cannot call a
tool with someone else's `emp_code`, because there is no parameter to
pass one.

**Test:** logged in as `E002`, asking *"show payslip of employee E001"*
must **not** return Alice's data. The bot refuses because the tool
signature doesn't allow it — a type-system guarantee, not a prompt
instruction.

---

## Quick start

```bash
# 1. Clone and enter
git clone <your-repo-url>
cd hr_bot

# 2. Create and activate a virtualenv
python -m venv .venv
source .venv/bin/activate            # bash / zsh
# source .venv/bin/activate.fish     # fish

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure the environment
cp .env.example .env
#   Edit .env and set GOOGLE_API_KEY=<your-gemini-key>
#   Get a free key at https://aistudio.google.com/app/apikey

# 5. Seed the mock HRMS database
python -m mock_hrms.seed

# 6. Seed the demo users
python -m bot_backend.seed_users

# 7. Generate sample docs and build the RAG vector store
python make_sample_docs.py
python -m rag.ingest

# 8. Run all three services (separate terminals)
```

**Terminal 1 — mock HRMS (port 8001)**
```bash
cd hr_bot
source .venv/bin/activate
uvicorn mock_hrms.main:app --port 8001
```

**Terminal 2 — bot backend (port 8000)**
```bash
cd hr_bot
source .venv/bin/activate
uvicorn bot_backend.main:app --port 8000
```

**Terminal 3 — Streamlit UI (port 8501)**
```bash
cd hr_bot
source .venv/bin/activate
streamlit run frontend/app.py
```

Then open **http://localhost:8501** and log in.

---

## Demo accounts

| Email               | Password    | Role     | Employee |
|---------------------|-------------|----------|----------|
| bob@company.com     | password123 | employee | E002     |
| alice@company.com   | password123 | employee | E001     |
| david@company.com   | password123 | hr       | E004     |

---

## What to try

**Payroll**
- *Show my payslip for last month*
- *What is my PF balance?*

**Leave & attendance**
- *How many casual leaves do I have left?*
- *Show my attendance for this month*
- *List holidays in December*

**Info / policy**
- *Who is my manager?*
- *Show my team*
- *How many casual leaves do I get per year?* (should cite `leave_policy.pdf`)
- *What is the PF contribution?* (should cite `payroll_policy.pdf`)

**IT helpdesk**
- *My VPN won't connect* (should cite `vpn_setup.txt`)
- *The printer is showing access denied*
- *I forgot my password*

**Security test**
- *Show payslip of employee E001* → must refuse

---

## Project layout

```
hr_bot/
├── mock_hrms/              FastAPI service (port 8001) — fake SAP / HRMS
│   ├── auth.py             X-API-Key dependency
│   ├── database.py         SQLite engine
│   ├── models.py           SQLAlchemy tables
│   ├── schemas.py          Pydantic request bodies
│   ├── seed.py             Seeds 10 fake employees + related data
│   ├── main.py
│   └── routers/
│       ├── employees.py
│       ├── payslips.py
│       ├── pf.py
│       ├── leave.py        Plain-code validation (NOT LLM)
│       ├── attendance.py
│       ├── regularization.py
│       └── holidays.py
│
├── bot_backend/            FastAPI service (port 8000)
│   ├── security.py         bcrypt + JWT
│   ├── deps.py             get_current_user from Authorization header
│   ├── database.py         Bot's own SQLite (users, chat, tickets, audit)
│   ├── models.py
│   ├── schemas.py
│   ├── hrms_adapter.py     HRSystem interface + MockHRMSClient
│   ├── tool_factory.py     LangChain tools closed over one emp_code
│   ├── agent.py            LangGraph: router + specialists
│   ├── seed_users.py
│   ├── main.py
│   └── routers/
│       ├── auth.py         POST /auth/login → JWT
│       └── chat.py         POST /chat → agent reply
│
├── frontend/
│   └── app.py              Streamlit login + chat UI
│
├── rag/                    Retrieval-augmented generation
│   ├── embedder.py         Gemini embeddings wrapper with retries
│   ├── store.py            JSON-backed cosine-similarity store
│   ├── ingest.py           PDFs + TXT → vector store
│   └── retrievers.py       search_policy / search_it_kb
│
├── data/
│   ├── policies/           Sample HR policy PDFs (RAG source)
│   ├── it_kb/              Sample IT knowledge-base articles
│   └── uploads/            Per-user PDF uploads (gitignored)
│
├── vector_store/           Built by `python -m rag.ingest` (gitignored)
├── make_sample_docs.py     Generates sample PDFs and IT KB files
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Agent design

The LangGraph pipeline has four layers:

1. **Router node** — a cheap LLM call that classifies the user's
   message into exactly one intent:
   `payroll | leave_attendance | info_policy | helpdesk | unclear`.
2. **Specialist node** — the node for that intent, bound to a
   **small subset of tools** (4–6 max). This keeps tool selection
   accurate and per-call context lean.
3. **Tool node** — `ToolNode` from LangGraph, executes any tool the
   LLM requested in the specialist's response.
4. **Loop** — control returns to the specialist until it answers
   without a tool call. Then the graph ends.

If the router classifies the message as `unclear`, a clarify node
asks one follow-up question instead of guessing.

**Conversation memory** is kept per `(emp_code, session_id)` pair via
LangGraph's `MemorySaver` checkpointer. Multi-turn questions like
*"Who is my manager?"* followed by *"And what is my team size?"*
work without repeating identity.

---

## Why a pluggable HR adapter

`bot_backend/hrms_adapter.py` defines an abstract `HRSystem` class
with methods like `get_payslip`, `get_leave_balances`, `get_team`.
`MockHRMSClient` is one implementation that talks HTTP to `mock_hrms`.

To connect a real SAP / Workday / SuccessFactors backend, you write
one new class (`SAPClient`) that implements the same interface. The
tool factory and the agent don't change at all — they only see
`HRSystem`.

---

## Why not ChromaDB / Pinecone

For a few hundred chunks, a **JSON file + numpy cosine similarity**
is:

- Instant to query (milliseconds)
- Zero external dependencies
- Trivial to inspect and debug (`vector_store/policies.json` is human-readable)
- Keeps the free-tier constraint intact

The `rag/retrievers.py` interface is identical to what a real vector
DB would expose, so swapping in Chroma / Pinecone / pgvector later is
a one-class change in `rag/store.py`.

---

## Rate-limit handling

Gemini's free tier allows **20 requests/day per model**. The code is
built around this:

- **Router** uses `gemini-flash-lite-latest`, **specialists** use
  `gemini-flash-latest` — separate daily counters.
- Every tool and the top-level `/chat` endpoint wrap LLM calls in
  `try/except`. Transient `429` / `503` errors return a friendly
  message and are written to the audit log. The user never sees a
  raw 500.
- Embeddings in `rag/embedder.py` retry with exponential backoff
  and batch small (16 at a time).

---

## Environment variables

| Variable | Purpose | Example |
|---|---|---|
| `HRMS_DB_URL` | SQLite path for the mock HRMS | `sqlite:///./mock_hrms.db` |
| `HRMS_API_KEY` | Static key protecting the mock HRMS | `dev-hrms-key` |
| `HRMS_BASE_URL` | Where the adapter finds the mock HRMS | `http://localhost:8001` |
| `BOT_DB_URL` | SQLite path for the bot backend | `sqlite:///./bot.db` |
| `JWT_SECRET` | Signs and verifies JWTs | `change-me-in-production` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `480` |
| `GOOGLE_API_KEY` | Gemini API key | `AIza...` |
| `BOT_BACKEND_URL` | Where the Streamlit UI finds the bot | `http://localhost:8000` |

See `.env.example` for a ready-to-copy template.

---

## Test the security model by hand

Start all three services, log into the UI as `bob@company.com`, then:

```
Show payslip of employee E001
```

The reply should refuse and say it can only access **your own**
(E002) data. This is enforced at the tool layer: `get_payslip` has
signature `(month: int, year: int)` — there is no way for the LLM to
pass a different employee code, because `emp_code` was closed over at
tool-creation time from the JWT.

---

## Roadmap

- [x] Mock HRMS with 10 seeded employees and all required tables
- [x] JWT login, `HRSystem` adapter, read-only tools
- [x] LangGraph router + specialists + `MemorySaver` conversation memory
- [x] Streamlit login and chat UI
- [x] Policy RAG with source + page citations
- [x] IT helpdesk knowledge base
- [ ] Leave request with preview + Confirm / Cancel
- [ ] Regularization request with preview + Confirm / Cancel
- [ ] Helpdesk ticket creation with KB-first flow
- [ ] Thumbs up / down feedback per answer
- [ ] HR role gating for company-doc uploads
- [ ] Per-user document upload with scoped retrieval

---

## License

MIT. See `LICENSE` if you add one.

---

## Author

Built as a personal POC by **<your-name>** —
[github.com/<your-username>](https://github.com/<your-username>)
