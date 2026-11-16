# AI Agent Skills Lab

Six agent skills. Six small projects. One skill at a time, learned by building.

Most agent tutorials try to teach everything at once: tools, memory, planning,
orchestration, evaluation, safety — all tangled into one demo that collapses the
moment you change anything. This lab takes the opposite approach. Each project
isolates **one core agent skill**, builds the smallest useful agent around it,
and stops there. When you finish a project you don't just have code — you have a
mental model of one building block, and you know exactly which block it is.

By the end, the six blocks compose: the capstone agent you could build from
these parts would call tools (Project 1), remember its user (Project 2), plan
before acting (Project 3), route work to specialists (Project 4), coordinate a
team (Project 5), and pause for a human before doing anything irreversible
(Project 6). That composition — not any single framework — is what production
agent engineering actually looks like.

This repo is the hands-on companion to the **AI Engineering Lab** learning path.
Guides here are written to be followed at the keyboard, not skimmed.

## The six projects

| # | Folder | Project | Skill it isolates | Stack |
|---|--------|---------|-------------------|-------|
| 1 | `01-tool-calling` | Weather & Calendar Assistant | **Tool calling** — the model decides, your code executes | Python, Claude API, OpenWeather API, Google Calendar API, Pydantic, FastAPI |
| 2 | `02-memory` | Study Coach That Remembers Progress | **Memory** — structured state + semantic recall across sessions | Python, Claude API, Postgres, pgvector, LangGraph, Streamlit |
| 3 | `03-planning` | Trip Itinerary Planner | **Planning** — draft a plan, check it, revise it, then act | Python, Claude API, LangGraph, Google Maps API, Pydantic, Streamlit |
| 4 | `04-routing` | Support Ticket Router | **Routing** — classify, score confidence, hand off or escalate | Python, Claude API, LangGraph, FastAPI, Postgres, Pydantic |
| 5 | `05-multi-agent` | Researcher, Writer & Reviewer Team | **Multi-agent collaboration** — roles, least privilege, review loops | Python, Claude API, LangGraph, Tavily, Pydantic, Streamlit |
| 6 | `06-human-approval` | Email Assistant with Send Approval | **Human-in-the-loop** — pause, approve, resume, audit | Python, Claude API, LangGraph, Gmail API, FastAPI, Postgres |

## How the pieces compose

Read the table bottom-up and you get the anatomy of a serious agent system:

- **Tool calling (1)** is the atom. Everything else assumes an agent that can
  reliably invoke functions and survive their errors.
- **Memory (2)** gives the atom a past. Structured rows for facts you can query;
  embeddings for notes you need to *recall by meaning*, not by keyword.
- **Planning (3)** gives it a future. The agent writes the plan down *before*
  spending API calls, then validates the plan against hard constraints
  (budget, travel time) instead of hoping the first draft works.
- **Routing (4)** is how one agent becomes a front door. A cheap, well-scoped
  classifier with a confidence score beats one giant prompt — and the score
  tells you when *not* to trust it.
- **Multi-agent (5)** splits the work by role. The key lesson is least
  privilege: the writer never searches the web, the researcher never writes
  prose, and the reviewer can only judge against a rubric.
- **Human approval (6)** is the safety case. Any action that leaves the
  building — sending an email is the canonical example — goes through a
  durable pause that a human releases, with an audit trail.

## Suggested order and pace

Do them **in order**. Each project reuses the previous project's hard-won
intuition (the tool loop from 1 becomes a node in 3's graph; the Postgres
setup from 2 returns in 4 and 6).

At 5–7 focused hours per week, budget roughly **1–2 weeks per project**:

| Phase | Projects | What you're really learning |
|-------|----------|-----------------------------|
| Phase 1 — Foundations | 01, 02 | The tool-use loop; state that outlives a request |
| Phase 2 — Structure | 03, 04 | Graphs, planning, validation, confidence and escalation |
| Phase 3 — Systems | 05, 06 | Teams of agents; humans in the loop; auditability |

Start with Phase 1 even if it looks easy. The failure modes you meet there
(bad schemas, unhandled API errors, runaway loops) are the ones that hurt in
production, and they're cheapest to learn on a weather bot.

## Setup

Full instructions are in [SETUP.md](SETUP.md). The short version:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in your keys
docker compose up -d        # Postgres + pgvector, needed by projects 02, 04, 06
```

Each project folder has a `GUIDE.md` (the full build walkthrough, with deploy
and test steps) and a starter `app.py` skeleton with the structure in place and
the interesting parts marked `TODO`. Curated documentation links for every
technology used live in [REFERENCES.md](REFERENCES.md).

## Cost

Everything here runs on free tiers or pennies of API usage. Claude API calls
across all six projects, done at a learning pace, typically cost a few dollars
in total. OpenWeather, Google Maps, and Tavily all have free tiers that are
more than sufficient; Postgres runs locally in Docker. See the cost note in
[SETUP.md](SETUP.md).

## License

MIT — see [LICENSE](LICENSE). Build with it, teach with it, break it, fix it.
