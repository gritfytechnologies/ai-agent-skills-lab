# Project 06 — Email Assistant with Send Approval

**Skill isolated: human-in-the-loop.** The agent drafts; a human decides;
the system can prove both happened.

## Why this skill

Every previous project acted inside the sandbox of your own machine. Sending
email is the canonical step outside: it's irreversible, it carries your name,
and a hallucinated sentence becomes a real-world fact the moment it leaves.
Production agent design has a standard answer, and this project builds it
properly:

- The graph **pauses durably** before the send — state persisted in Postgres,
  so the pause survives restarts, deploys, and a reviewer who takes two days.
- A human **approves, edits, or rejects** — all three are first-class
  outcomes, and edit is the one beginners forget.
- **Nothing resumes except through the approval**, and every decision lands
  in an **audit log**: who, when, what was approved, what was changed.

This is LangGraph's `interrupt()` mechanism used for its intended purpose,
and it's the pattern behind every "AI proposes, human disposes" workflow in
regulated industries — which is why it's the capstone.

## What you'll build

A FastAPI service over your Gmail: fetch a thread, the assistant drafts a
reply informed by your style profile, and the graph stops. An approval UI
(FastAPI endpoints + a minimal page) shows the draft next to the thread.
Approve → the email sends and the decision is logged. Edit → you modify the
draft, then it sends, and the log records that it was edited. Reject →
nothing sends, and the rejection is logged with your reason.

## Architecture, in words

- **LangGraph graph:** `fetch_thread → draft_reply → [INTERRUPT] →
  send | discard → audit`. Compiled with a **Postgres checkpointer**
  (`PostgresSaver`) so paused state is durable — this is the detail that
  separates a demo from a system. Each email thread maps to a graph
  `thread_id` (the LangGraph kind — name your variables carefully, both
  kinds of "thread" are in this project).
- **Style profile:** a short text file (or DB row) describing how you write:
  greeting habits, sign-off, typical length, formality. The drafter reads
  recent sent mail *once*, with your help, to build it — then the profile,
  not your mailbox, is what every draft consults.
- **Gmail tools:** `get_thread(thread_id)` (read), `send_reply(thread_id,
  body)` (write — callable from exactly one node, after the interrupt).
- **Postgres table:** `audit_log(id, created_at, gmail_thread_id,
  decision [approved|edited|rejected], draft_original, draft_sent,
  decided_by, reason)`.

## Before you start

- Root setup done; `docker compose up -d` from the repo root.
- Extra packages: `pip install google-api-python-client google-auth
  google-auth-oauthlib` and a Postgres checkpointer package for LangGraph
  (`pip install langgraph-checkpoint-postgres`).
- Gmail OAuth: `credentials.json` in this folder, Gmail API enabled, scopes
  for reading and sending (see SETUP.md §4). **Use a test Gmail account or a
  secondary mailbox for this project.** You are building a machine that can
  send email as you; develop it against an account where a mistake is cheap.

## Build steps

### Step 1 — Read-only first

Implement `get_thread` and an endpoint that returns a thread's messages
(sender, date, body). No drafting, no sending. Verify against a real thread
in the test account.

**Check:** the endpoint renders a 5-message thread in order, bodies intact.
Read-only week-one discipline is how real integrations start.

### Step 2 — Drafting with a style profile

Write `style_profile.md` by hand first (five honest bullets about how you
write email), then `draft_reply(state)`: prompt = thread + profile →
draft body. Add an endpoint that returns the draft *without* any send path
existing in the code yet.

**Check:** draft three replies to different threads. They should sound like
the profile (your greeting, your sign-off, your length). If they sound like
a press release, the profile is too vague — make it more specific, not the
prompt longer.

### Step 3 — The interrupt

Rebuild as a LangGraph graph with the Postgres checkpointer. The approval
node calls `interrupt({...draft, thread summary...})`. The run returns with
the interrupt payload and *stops* — the state sits in Postgres. Resume with
`Command(resume=decision)` where decision is a small Pydantic model:
`{action: approved|edited|rejected, edited_body: str | None, reason: str |
None}`.

Read the LangGraph interrupts documentation's **rules** section before this
step, twice: don't wrap `interrupt()` in try/except, keep side effects
*after* the interrupt, and remember the node re-runs from its start on
resume (so the send call must live after the interrupt call, or in the next
node).

**Check:** start a draft, kill the server, restart it, then approve — the
resume must still work. If it does, your pause is durable. That test is the
whole project in miniature.

### Step 4 — The send node (and only the send node)

`send_reply` executes only when the resume decision is `approved` (send the
draft) or `edited` (send `edited_body`). `rejected` routes to a discard node
that sends nothing. Put the Gmail send call in exactly one place in the
codebase and grep to prove it.

**Check:** reject a draft and confirm — in the Gmail account itself — that
nothing was sent. Then approve one and confirm exactly one message arrived.
One. (Duplicate sends on resume are the classic interrupt bug: a side effect
placed before the interrupt re-runs. If you get two, you now know why.)

### Step 5 — Audit everything

Every resume writes an `audit_log` row: original draft, final sent body (or
null), decision, reason, timestamp. Add `GET /audit` to read it back.

**Check:** after one approve, one edit, and one reject, the audit table
tells the whole story — including *what the edit changed*. Diff
`draft_original` vs `draft_sent` mentally; if you can't see the change, log
more.

### Step 6 — The approval UI

Endpoints: `POST /drafts` (start: thread id → runs graph to the interrupt,
returns draft + graph thread id), `GET /drafts/{id}` (current state),
`POST /drafts/{id}/decision` (the resume), `GET /audit`. Then a minimal HTML
page served by FastAPI: thread on the left, editable draft on the right,
three buttons. Ugly is fine. *Clear* is mandatory — the human must see
exactly what will be sent, to whom, in which thread.

## Run / deploy locally

```bash
docker compose up -d              # from the repo root, once
cd 06-human-approval
uvicorn app:app --reload          # http://127.0.0.1:8000, UI at /docs
```

## Done when

- [ ] A draft survives a server restart while paused, and resumes correctly
      afterward (durable checkpoint, proven — not assumed).
- [ ] Reject sends nothing (verified in the mailbox) and is audit-logged
      with its reason.
- [ ] Edit-then-approve sends the *edited* text, and the audit log shows
      both versions.
- [ ] `grep` finds exactly one Gmail send call site in the codebase, located
      after the interrupt.

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Resume starts a fresh draft instead of continuing | Different graph `thread_id` on resume, or in-memory checkpointer | Same thread_id end to end; PostgresSaver, not MemorySaver |
| Email sent twice | Send call placed before `interrupt()` in the node — nodes re-run on resume | Move all side effects after the interrupt or into the next node (see the docs' rules) |
| Interrupt never fires / exception swallowed | `interrupt()` wrapped in try/except | Never catch around it — the pause *is* an exception mechanism |
| Draft ignores the style profile | Profile too generic | Write the profile from 3 real sent emails; specifics in, adjectives out |
| OAuth token keeps expiring | App in Testing mode → 7-day refresh tokens | Fine for this lab; re-run the consent flow, or publish the app to Production for your own account |
| Audit log missing the edit | Logging the decision before the edit is applied | Write the audit row in the node *after* resume, with both draft versions |

## Stretch exercise

Add **expiry**: a paused draft older than 48 hours auto-rejects (a scheduled
check writes the audit row with decision `expired`). Then add a second
approver rule: emails to recipients outside your domain need a note in the
reason field before approval is accepted. You've just invented two real
governance controls — timeout and conditional justification — that
enterprise approval systems charge a great deal of money for.

## Project references

- Interrupts / human-in-the-loop — https://docs.langchain.com/oss/python/langgraph/human-in-the-loop
- LangGraph persistence — https://docs.langchain.com/oss/python/langgraph/persistence
- Gmail API overview — https://developers.google.com/gmail/api/guides
- FastAPI — https://fastapi.tiangolo.com/
