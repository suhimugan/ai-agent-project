# AI Knowledge Copilot

> A local AI agent that answers questions about your documents and business data —
> built as a real-world example of a modern AI engineer's local dev stack.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Docker-29.x-blue)
![Claude](https://img.shields.io/badge/Claude-Haiku-purple)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What is this?

This project is two things at once:

1. **A working AI agent** — ask it questions, it searches your local documents and
   database, returns structured answers with sources
2. **A reference implementation** — shows what a modern AI engineer's local dev
   environment actually looks like in practice, not just theory

Built with Claude API, MCP-style tool architecture, Docker, and Python.
No cloud storage. No third-party vector databases. Everything runs locally.

---

## Why this project exists

Most AI tutorials show you how to call an API and print the result.
This project shows you how to build a real system:

- How an agent decides which tool to call
- How to keep your data secure (AI never reads files directly)
- How to structure outputs so they are testable and debuggable
- How to run the whole thing in a container

The companion blog post **"Mapping My AI Stack for 2025"** walks through every
decision made while building this — infrastructure-first, not model-first.

---

## Architecture

```
User Question
      ↓
  AI Agent (Claude)
  Plans · Reasons · Decides
      ↓
  Tool Router
   ↙           ↘
Document      SQL Query
 Search       (customers,
(policies,     orders,
  guides)      tickets)
      ↓
Structured Response
  answer + sources + confidence + tool_used
```

### The security boundary

The most important design decision in this project:

```
❌ Wrong:  User → Agent → reads files directly → answers
✅ Right:  User → Agent → calls tool → tool reads file →
           passes only relevant excerpt → Agent answers
```

The AI never sees your full documents. Tools extract only what is relevant
and pass that to the model. This pattern is inspired by MCP
(Model Context Protocol) — the emerging standard for how AI agents
connect to data sources.

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.11 | Best AI library support |
| AI model | Claude Haiku (Anthropic) | Fast, cheap, capable |
| API client | anthropic 0.84.0 | Official SDK |
| Local database | SQLite | No server needed |
| Config | python-dotenv | Secrets never in code |
| Logging | Python logging | Timestamped audit trail |
| Container | Docker + Compose | Runs anywhere |
| Editor | VS Code | Best Python + Docker DX |

---

## Project structure

```
ai-agent-project/
├── agents/
│   └── copilot_agent.py      # AI brain — tool routing, retry, structured output
├── tools/
│   ├── document_search.py    # Relevance-scored search across local .txt and .md files
│   └── sql_query.py          # Safe SELECT-only queries against local SQLite
├── data/
│   ├── docs/                 # Drop your documents here
│   │   ├── company_policy.txt
│   │   ├── hr_policy.txt
│   │   └── product_guide.txt
│   ├── company.db            # SQLite database (customers, orders, tickets)
│   └── create_database.py    # Script to seed sample data
├── config/
│   ├── settings.py           # All config in one place
│   └── logger.py             # Logging setup
├── docker/
│   └── Dockerfile
├── logs/                     # Auto-created, one log file per day
├── docker-compose.yml
├── .dockerignore
├── .env.example              # Template — copy to .env and add your key
├── requirements.txt
└── main.py                   # Entry point
```

---

## Setup

### Prerequisites

- Python 3.11+
- Docker Desktop (optional, for containerised run)
- Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

### 1. Clone the repo

```bash
git clone https://github.com/suhimugan/ai-agent-project.git
cd ai-agent-project
```

### 2. Set up environment

```bash
# Copy the template
cp .env.example .env
```

Open `.env` and add your key:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 3. Install dependencies

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Create the sample database

```bash
python data/create_database.py
```

### 5. Run

```bash
python main.py
```

---

## Run with Docker

No Python installation needed — Docker handles everything.

```bash
# Build and run interactively
docker compose run --rm ai-copilot
```

First run downloads the Python base image (~45MB) and installs dependencies.
Every run after that is instant.

---

## Example questions

### Document questions (searches local .txt and .md files)

```
What is our refund policy?
How many days of annual leave do I get?
What platforms does the product support?
What is the pro plan price?
Can I get my money back?
```

### Database questions (queries SQLite)

```
Who is on the Pro plan?
Are there any open support tickets?
What is our total revenue?
How many customers do we have?
Show me all refunded orders
```

### Out of scope (handled gracefully — no hallucination)

```
What is the weather today?
Who won the election?
```

The agent will tell you it cannot find the answer rather than making one up.

---

## How the agent works

### Step 1 — Question received

```python
run_agent("Who is on the Pro plan?")
```

### Step 2 — Claude decides which tool to use

Claude reads the question and the tool descriptions.
It chooses `sql_query` for data questions, `document_search` for policy questions.

```
[Agent] Using tool: sql_query | question: 'Who is on the Pro plan?'
```

### Step 3 — Tool runs locally

The SQL tool queries `data/company.db` and returns matching rows.
The document tool scans `data/docs/` and returns relevance-scored excerpts.
Neither tool sends full files to the API.

### Step 4 — Claude forms the answer

The tool result is sent back to Claude, which writes a concise answer
citing the source.

### Step 5 — Structured response returned

```python
AgentResponse(
    answer="There are 2 customers on the Pro plan: Alice Johnson and David Lee.",
    sources=["company.db"],
    confidence="high",
    tool_used="sql_query"
)
```

---

## Adding your own documents

Drop any `.txt` or `.md` file into `data/docs/` and restart the app.
No configuration needed — the agent automatically searches all files in that folder.

---

## Security design

| Risk | Mitigation |
|---|---|
| API key exposed | Loaded from `.env`, gitignored, excluded from Docker image |
| Full documents sent to API | Tools extract only relevant excerpts (max 3 chunks) |
| SQL injection | Only SELECT statements allowed — INSERT/UPDATE/DELETE blocked |
| Secrets in Docker image | `.env` in `.dockerignore` — never baked into image |
| Uncaught API failures | Retry logic with exponential wait, graceful error responses |

---

## Logs

Every session is logged to `logs/agent_YYYYMMDD.log`:

```
2026-03-17 09:33:10 | INFO | Question received: Who is on the Pro plan?
2026-03-17 09:33:11 | INFO | Tool selected: sql_query
2026-03-17 09:33:11 | INFO | SQL question: 'Who is on the Pro plan?'
2026-03-17 09:33:11 | INFO | Tool result status: success
2026-03-17 09:33:12 | INFO | Answer generated | tool: sql_query | confidence: high
```

---

## Roadmap

### v2 — Local disk search (in progress)
- [ ] Search any folder path on local disk (not just `data/docs/`)
- [ ] Support PDF files (`pypdf`)
- [ ] Support Word documents (`python-docx`)
- [ ] File index cache — avoid re-reading unchanged files
- [ ] Search by filename as well as content

### v3 — Better search
- [ ] Replace keyword scoring with embeddings (semantic search)
- [ ] `sentence-transformers` for local embedding generation
- [ ] FAISS or ChromaDB for vector storage

### v4 — Web UI
- [ ] FastAPI backend
- [ ] Simple HTML/JS frontend
- [ ] Conversation memory across questions
- [ ] File upload via browser

### v5 — Full MCP integration
- [ ] Claude Code workflow integration
- [ ] Proper MCP server implementation
- [ ] Connect to external tools (calendar, email, web search)

---

## Blog post — Mapping My AI Stack for 2025

This project is the working example behind the article
**"What does a modern AI engineer's local dev environment actually look like?"**

Topics covered:

- Why infrastructure-first beats model-first when building AI systems
- Setting up Claude API + Claude Code locally
- MCP-style tool architecture — what it is and why it matters
- Wiring document search, SQL, and future tool connections
- Security patterns every AI engineer should use
- Docker for AI projects — the full workflow

*Coming soon — follow for updates.*

---

## What I learned building this

- **Prompt engineering is tool engineering.** The biggest improvements came
  from better tool descriptions and system prompts, not model changes.
- **The security boundary is the most important design decision.**
  Deciding what the AI can and cannot touch directly shapes everything else.
- **Structured outputs are non-negotiable.** A typed `AgentResponse` object
  is infinitely more useful than a raw string for testing, logging, and UI.
- **Start with the cheapest model.** Claude Haiku handled everything in this
  project. Sonnet is there when you need it.

---

## License

MIT — use it, extend it, build on it.

---

## Author

Built by [@suhimugan(https://github.com/suhimugan)
as a real-world AI engineering learning project.

If this helped you, star the repo ⭐ and share it.
