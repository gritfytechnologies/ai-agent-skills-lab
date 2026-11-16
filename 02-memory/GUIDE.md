# Project 02 — Study Coach That Remembers Progress

**Skill isolated: memory.** Facts in tables, meaning in vectors, and a profile
that loads before the first message.

## Why this skill

Project 01's assistant forgot everything the moment a request ended. Real
agents can't. Memory is what turns a stateless tool-caller into something
that improves with use — but "memory" is not one thing, and picking the wrong
kind is the classic beginner mistake. This project makes you build both kinds,
side by side, so the difference becomes obvious:

- **Structured memory** — Postgres rows: sessions, topics, quiz scores, weak
  spots. Exact, queryable, aggregable ("my average on recursion this month").
- **Semantic memory** — notes embedded into pgvector: recall by *meaning*
  ("what did we figure out about that confusing base-case thing?") even when
  the words don't match.

On top of both sits a third pattern: **compression**. Old sessions get
summarized into a short profile that loads into context at chat start, so the
agent "knows you" without replaying your entire history every turn.

## What you'll build

A Streamlit chat app backed by Postgres + pgvector and a small LangGraph
graph. The coach quizzes you on a topic you're learning, records how you did,
notices weak spots, schedules spaced-repetition reviews, and next week greets
you with what it remembers.

## Architecture, in words

- **Postgres schema** (created by the app on first run):
  - `sessions(id, started_at, topic, summary)`
  - `attempts(id, session_id, topic, question, answer, correct, created_at)`
  - `notes(id, session_id, text, embedding vector(1024))` — study notes and
    session takeaways, embedded for semantic recall.
  - `reviews(topic, due_on, interval_days)` — the spaced-repetition schedule.
  - `profile(id=1, profile_text, updated_at)` — the compressed learner
    profile, one row, rewritten by the summarizer.
- **Embeddings:** produced through the Claude API stack you already have —
  use an embeddings call available to your account, or any small local model;
  the guide's code takes a vector and stores it, so the source is swappable.
  Keep the dimension consistent (`vector(1024)` above — match whatever your
  embedding source produces).
- **LangGraph graph** with four nodes: `load_profile` → `coach` (chat +
  quiz) → `record` (writes attempts/notes) → `maybe_summarize` (compacts old
  sessions into the profile when they pile up). The graph is thin; the point
  is the state flow, not graph cleverness.
- **Streamlit UI:** chat window, a sidebar showing the loaded profile, due
  reviews, and per-topic accuracy — the memory made visible.

## Before you start

- Root setup done; `docker compose up -d` from the repo root (Postgres +
  pgvector).
- Keys in `.env`: `ANTHROPIC_API_KEY`, `DATABASE_URL` (default is fine).

## Build steps

### Step 1 — Schema and the write path

Create the tables (SQL in the starter's comments; run via `psycopg`). Enable
the extension first: `CREATE EXTENSION IF NOT EXISTS vector;`.

Then write the dumbest possible recorder: after each quiz answer in a plain
CLI loop, insert a row into `attempts`. No graph, no UI yet.

**Check:** answer three questions, then
`SELECT topic, count(*), avg(correct::int) FROM attempts GROUP BY topic;`
in `psql`. If the numbers are right, your write path is honest.

### Step 2 — Semantic notes

After each session, have the model produce 2–3 short takeaway notes ("Learner
confuses base case with base value in recursion"). Embed each note and insert
into `notes` with its session id. Write `recall_notes(query_text, k=4)`:
embed the query, then
`SELECT text FROM notes ORDER BY embedding <=> %s LIMIT %s` (cosine
distance).

**Check:** store a note about "base case confusion," then recall with the
query "why do my recursive functions never stop?" — different words, same
meaning. The note should come back first. If keyword search would have
failed and vector search didn't, you've felt why this exists.

### Step 3 — The profile: memory that loads itself

Write `refresh_profile()`: pull the last N session summaries plus aggregate
stats (accuracy by topic, current weak spots = topics under 70% over the last
20 attempts), and ask the model to rewrite `profile.profile_text` as a tight
paragraph (~150 words): who's learning what, what's solid, what's shaky,
what's due for review. At chat start, load this text into the system prompt.

**Check:** start a fresh chat and ask "What do you know about my progress?"
The coach should answer from the profile — topics, weak spots, due reviews —
without any tool call.

### Step 4 — Summarize to stay compact

Raw history grows; context windows and attention don't. Add the rule: when
`sessions` rows without summaries exceed 5, summarize the oldest batch into
one paragraph each, store in `sessions.summary`, and let `refresh_profile`
read summaries instead of raw logs. Delete nothing — compression is about
what you *load*, not what you keep.

**Check:** token count of the system prompt before/after summarization on a
seeded history. It should drop sharply while the profile still names your
weak spots correctly.

### Step 5 — Spaced repetition for weak topics

When a session ends, for each topic practiced: if accuracy ≥ 80%, double the
review interval (1 → 2 → 4 → 7 → 15 days…); if below, reset to tomorrow.
Upsert into `reviews`. At chat start, surface due topics: "Recursion is due
for review — want a quick round?" This is a tiny algorithm (a simplified
SM-2); the lesson is that *scheduling is memory too*.

**Check:** fake the dates (insert a review due yesterday) and confirm the
coach offers it unprompted at startup.

### Step 6 — Graph + UI

Move the flow into LangGraph: `load_profile` node puts the profile + due
reviews into state; `coach` runs the conversation turn (reusing the tool-loop
intuition from Project 01, with `recall_notes` offered as a tool); `record`
persists attempts and notes; `maybe_summarize` runs steps 4–5 when thresholds
are met. Then put Streamlit in front: `st.chat_input` for the conversation,
sidebar for profile/accuracy/due reviews so you can *watch* memory change.

## Run / deploy locally

```bash
docker compose up -d              # from the repo root, once
cd 02-memory
streamlit run app.py               # opens http://localhost:8501
```

## Done when

- [ ] Progress survives a restart: close everything, relaunch, and the coach
      still knows your topics, scores, and weak spots.
- [ ] Semantic recall works across vocabulary: a query phrased completely
      differently from the stored note still retrieves it first.
- [ ] The loaded profile stays compact (a paragraph, not a transcript) while
      remaining accurate after summarization runs.
- [ ] A review seeded as due yesterday is offered at startup without being
      asked for.

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `extension "vector" is not available` | You're connected to a Postgres without pgvector | Use the compose image (`pgvector/pgvector:pg16`); run `CREATE EXTENSION vector` |
| Dimension mismatch on insert | Embedding size ≠ column's `vector(N)` | Pick one embedding source; set N to its output size everywhere |
| Recall returns irrelevant notes | Embeddings stored but querying with raw text distance, or wrong operator | Use `<=>` (cosine) and embed the query with the same model as the notes |
| Profile keeps growing | Summarizer appends instead of rewriting | `refresh_profile` must *replace* `profile_text`, capped at a target length |
| Coach "forgets" within one chat | Profile loaded but conversation turns not kept in graph state | Keep the message list in LangGraph state across turns of the session |
| Everything is slow | Loading all notes/attempts into context each turn | Load the profile + top-k recall only; aggregate stats in SQL |

## Stretch exercise

Add a "forget me" feature: a sidebar button that deletes one topic's
attempts, notes, and reviews, and refreshes the profile. Then think through
what *complete* deletion means when a summary paragraph already absorbed the
topic — and make the summarizer re-derive the profile without it. Memory
systems that can't forget are liabilities; this is the cheapest place to
learn that.

## Project references

- LangGraph persistence — https://docs.langchain.com/oss/python/langgraph/persistence
- pgvector README — https://github.com/pgvector/pgvector
- Streamlit docs — https://docs.streamlit.io/
- Claude API overview — https://docs.claude.com/en/api/overview
