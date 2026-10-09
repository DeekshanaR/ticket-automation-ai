# AI-Powered IT Ticket Automation Engine

![CI](https://github.com/YOUR-USERNAME/ticket-automation-ai/actions/workflows/ci.yml/badge.svg)

An end-to-end workflow automation project in Python. Incoming IT support tickets are
**classified by a machine-learning model**, **prioritised**, **auto-assigned** to the right
team, enriched with an **AI-generated resolution suggestion** (Claude LLM, optional), and
moved through a **validated ticket lifecycle** — all exposed through a **REST API** and a
**batch "master script"** for Linux terminals.

> Built to demonstrate: Python scripting, REST API development, SQL, workflow/lifecycle
> automation, ML/AI integration, automated testing and CI.

## Architecture

```
 incoming ticket (REST API  or  CSV via master_runner.py)
        │
        ▼
 ┌────────────────┐   TF-IDF + Logistic Regression   ┌───────────────┐
 │  service.py    │ ───────────────────────────────▶ │ classifier.py │ category, priority, confidence
 │ (business logic)│                                  └───────────────┘
 │                │   Claude API (fallback: rules)   ┌─────────────────┐
 │                │ ───────────────────────────────▶ │ ai_assistant.py │ resolution suggestion
 │                │                                   └─────────────────┘
 │                │   NEW → TRIAGED → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
 │                │ ───────────────────────────────▶ lifecycle.py (state machine)
 └───────┬────────┘
         ▼
   SQLite (tickets + full audit history)
```

## Features
- **ML classification** of ticket category and priority with a confidence score
- **Low-confidence guard**: uncertain tickets are flagged `needs_review` instead of auto-assigned
- **Lifecycle state machine**: illegal status jumps (e.g. `NEW → CLOSED`) are rejected (HTTP 409)
- **Audit trail**: every status change is stored in `ticket_history`
- **LLM suggestions** with automatic offline fallback (works with no API key)
- **FastAPI** REST API with auto-generated Swagger docs at `/docs`
- **Master script** for batch processing, with logging and exit codes (cron-friendly)
- **13 automated tests** (pytest) and **GitHub Actions CI**

## Quick start

```bash
git clone https://github.com/YOUR-USERNAME/ticket-automation-ai.git
cd ticket-automation-ai

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m scripts.generate_data    # create synthetic dataset
python -m scripts.train_model      # train + show metrics
uvicorn app.main:app --reload      # API at http://127.0.0.1:8000/docs
```

### Run the batch master script
```bash
python -m scripts.master_runner --input data/incoming_tickets.csv
```

### Enable the Claude suggestions (optional)
```bash
export ANTHROPIC_API_KEY="your-key"     # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
```

### Run the tests
```bash
pytest -v
```

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/tickets` | Create + classify + auto-assign a ticket |
| GET | `/tickets?status=&category=` | List / filter tickets |
| GET | `/tickets/{id}` | Ticket details |
| POST | `/tickets/{id}/transition` | Move to the next lifecycle status |
| GET | `/tickets/{id}/history` | Audit trail |
| GET | `/stats` | Counts by status, category, priority |

Example:
```bash
curl -X POST http://127.0.0.1:8000/tickets -H "Content-Type: application/json" \
  -d '{"title":"VPN not connecting","description":"Timeout error when connecting from home"}'
```

## Honest limitations
- The dataset is **synthetic** (generated from templates), so model accuracy on it is
  unrealistically high. On real tickets, expect lower accuracy; the pipeline is built so a
  real labelled CSV can be dropped into `data/sample_tickets.csv` and retrained.
- SQLite is used for simplicity; PostgreSQL/MySQL would be the production choice.

## Ideas for future work
Docker image, web dashboard, Selenium-based UI check, embeddings-based similar-ticket search,
SLA breach alerts.

## Tech stack
Python 3.12 · FastAPI · SQLite · scikit-learn · pandas · Anthropic Claude API · pytest · GitHub Actions
