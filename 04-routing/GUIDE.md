# Project 04 — Support Ticket Router

**Skill isolated: routing.** Classify, score your confidence, hand off to a
specialist — or admit you're not sure and escalate.

## Why this skill

One giant agent with every tool and a five-page system prompt is the
architecture beginners reach for and production teams regret. Routing is the
alternative: a small, cheap, *measurable* front door that sends each request
to a narrow specialist. Three ideas make it work, and each one is a lesson:

- **Structured classification.** The router outputs data (category +
  confidence + reason), not prose. Data can be validated, logged, thresholded,
  and tested. Prose can only be read.
- **Confidence as a control signal.** Below 0.7, the system doesn't guess
  harder — it escalates to a human queue. Knowing when *not* to act is the
  difference between automation and a liability.
- **Measurement.** Every route is logged, and a labeled test set tells you
  the router's actual accuracy. An agent you can't measure is an agent you're
  guessing about.

## What you'll build

A FastAPI service: `POST /tickets` takes a support message, classifies it as
**billing**, **technical**, or **account**, routes it to a specialist agent
(each with its own prompt and tools), and returns the specialist's reply.
Low-confidence tickets land in a human queue table instead. Every decision is
logged to Postgres, and a test script scores the router against a labeled
set you write.

## Architecture, in words

- **LangGraph graph:** `classify → route` (conditional edge on category and
  confidence) → one of `billing_agent`, `technical_agent`, `account_agent`,
  or `human_queue` → `log`.
- **Classifier:** a single Claude call with a strict output contract —
  a Pydantic model `Classification{category, confidence, reason}`. Use the
  cheapest/fastest model tier you have for this node; classification is the
  highest-volume, lowest-complexity call in the system, and routing it to a
  small model is itself a routing decision.
- **Specialists:** three small agents, each a system prompt + 1–2 tools:
  - *Billing:* `lookup_invoice(customer_id)`, `issue_refund(invoice_id)`
    (stub them against local data — the point is the boundary, not billing).
  - *Technical:* `search_runbook(query)`, `check_service_status(service)`.
  - *Account:* `lookup_account(email)`, `start_password_reset(email)`.
  Stub data is fine and encouraged: in-memory dicts or a Postgres table.
- **Postgres tables:** `route_log(id, created_at, ticket_text, category,
  confidence, routed_to, correct)` — `correct` stays null until your test
  set or a human fills it in — and `human_queue(id, created_at, ticket_text,
  reason)`.

## Before you start

- Root setup done; `docker compose up -d` from the repo root.
- Keys in `.env`: `ANTHROPIC_API_KEY`, `DATABASE_URL` (default fine).

## Build steps

### Step 1 — The classifier contract

Write `Classification` (Pydantic): `category` as a Literal/enum of the three
values, `confidence` float 0–1, `reason` short string. Prompt the model for
JSON only; parse and validate. Then write 15 example tickets by hand —
5 per category, including 2–3 deliberately nasty ones ("I was charged twice
and now I can't log in to dispute it") — and eyeball the outputs.

**Check:** all 15 parse as valid `Classification` objects. The nasty ones
should show lower confidence or a reason that names the ambiguity. If the
model returns 0.99 confidence on everything, your prompt is not asking it to
*judge* — add: "Confidence below 0.7 means a human should handle this; use
it whenever two categories fit or key facts are missing."

### Step 2 — Threshold and the human queue

Implement the routing rule in code (not in the prompt): `confidence < 0.7` →
`human_queue`, regardless of category. Insert into `human_queue` and return
a polite "a person will follow up" response.

**Check:** feed the double-charge/login ticket. If it classifies billing at
0.62, it must land in the queue. Verify the row exists in Postgres.

### Step 3 — One specialist, end to end

Build the billing specialist first: its own system prompt ("You are a
billing specialist. You may look up invoices and issue refunds up to $100;
anything larger, explain and escalate.") plus its two stub tools, reusing
Project 01's loop. Wire the graph: classify → billing → log → respond.

**Check:** "I was charged twice for invoice 1042" produces a lookup, a
refund of the duplicate, and a reply naming the invoice and amount.

### Step 4 — The other two specialists + least privilege

Add technical and account specialists the same way. Then prove the
boundaries: ask the *billing* agent (via a billing-classified ticket) to
reset a password. It must refuse or escalate — it has no such tool and its
prompt doesn't cover it. Specialists that can do everything are just the
giant agent again, wearing a hat.

**Check:** a small matrix — 3 categories × (in-scope, out-of-scope) — behaves
correctly in all 6 cells.

### Step 5 — Log everything, then measure

Every request writes a `route_log` row *including* human-queued ones (they
are data too — a rising queue rate is your earliest warning that the router
or the product is drifting). Then build `test_router.py`: a labeled set of
at least 30 tickets (write them, label them honestly, include edge cases),
run each through `classify` only, and print accuracy overall and per
category, plus the confusion pairs (what gets mistaken for what).

**Check:** you can state your router's accuracy as a number and name its
worst confusion pair. Below ~85% on your own test set, fix the classifier
prompt/descriptions before touching anything else — that's the measurement
telling you where the problem lives.

### Step 6 — Serve it

FastAPI per the starter: `POST /tickets` → `{reply, category, confidence,
routed_to}`. Add `GET /queue` listing human-queued tickets, and `GET /stats`
returning counts by route from `route_log`. These two endpoints are the
operational face of the system — the part a support lead would actually
look at every morning.

## Run / deploy locally

```bash
docker compose up -d              # from the repo root, once
cd 04-routing
uvicorn app:app --reload          # http://127.0.0.1:8000, UI at /docs
python test_router.py             # accuracy report (you create this in step 5)
```

## Done when

- [ ] The 6-cell specialist matrix passes: each specialist handles its own
      category and refuses/escalates outside it.
- [ ] A genuinely ambiguous ticket (confidence < 0.7) lands in `human_queue`
      and appears on `GET /queue` — never silently forced into a category.
- [ ] `test_router.py` prints an overall accuracy number and per-category
      breakdown from a labeled set of 30+ tickets.
- [ ] Every request — routed or queued — has a matching `route_log` row.

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Confidence is always ~0.95+ | Prompt asks for a label, not a judgment | Instruct the model on what low confidence means and when to use it (step 1) |
| JSON parse failures | Model adds prose around the JSON | "Output only JSON", strip fences, validate with Pydantic, retry once with the error |
| Everything routes to technical | Category descriptions overlap; technical is the vaguest | Sharpen each category's description with exclusions ("not X — that's billing") |
| Queue is empty in tests but huge in real use | Test set too clean | Write test tickets from real phrasing: typos, mixed problems, missing facts |
| Accuracy number is meaningless | Test set written by the same intuitions as the prompt | Include tickets you *expect* to fail; label before you run, not after |
| Refund tool fires on lookups | Specialist prompt doesn't sequence its tools | State the workflow in the prompt: look up first, act second, confirm in the reply |

## Stretch exercise

Add a fourth route: **urgent** — an override category for tickets mentioning
outages, security, or legal threats, detected *before* the main classifier
runs (a cheap keyword + model check). Urgent tickets skip the queue rules and
page the human queue with a priority flag. Notice the design tension you now
own: every override you add makes the system safer for one case and less
predictable overall. That trade-off, made consciously, is routing design.

## Project references

- Claude API overview — https://docs.claude.com/en/api/overview
- LangGraph overview — https://docs.langchain.com/oss/python/langgraph/overview
- FastAPI — https://fastapi.tiangolo.com/ · Pydantic — https://docs.pydantic.dev/latest/
