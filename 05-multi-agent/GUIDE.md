# Project 05 — Researcher, Writer & Reviewer Team

**Skill isolated: multi-agent collaboration.** Split the work by role, give
each role only what it needs, and let a reviewer close the loop.

## Why this skill

So far every system had one agent wearing different hats. Teams of agents
earn their complexity in exactly one situation: when the *quality bar*
requires separation of duties. A writer who also does the research grades
their own homework; a researcher who also writes buries the evidence under
prose. This project builds the canonical team —

- **Researcher** — searches the web (Tavily), returns *findings with cited
  sources*, never prose.
- **Writer** — drafts **using only those findings**. No search tool. If a
  fact isn't in the findings, it doesn't go in the draft.
- **Reviewer** — scores the draft against a written rubric and returns
  *specific* fixes, or approves it.

— wired into a loop that ends on approval or a hard cap of 3 revisions. The
cap is not a detail: multi-agent loops without caps are how demos become
invoices.

## What you'll build

A Streamlit app: give it a topic and an audience ("Explain passkeys to
non-technical small-business owners, ~600 words"). Watch the researcher
gather cited findings, the writer draft from them, and the reviewer send it
back with notes — until the draft passes the rubric. The final piece shows
its sources.

## Architecture, in words

- **LangGraph graph:** `research → write → review`, with a conditional edge
  from `review`: approved → END; rejected and revisions < 3 → back to
  `write` (with the reviewer's notes in state); rejected at cap → END with
  the best draft + a note that it didn't pass.
- **Shared state** (the contract between agents — design it like an API):
  `topic, audience, findings: list[Finding], draft: str,
  review: Review | None, revisions: int`.
- **Contracts (Pydantic):**
  - `Finding{claim, source_url, source_title, excerpt}` — a claim with its
    evidence attached. No claim without a source survives this schema.
  - `Review{scores: dict[str, int], fixes: list[str], approved: bool}` —
    rubric scores (accuracy, clarity, audience fit, sourcing) plus concrete
    fix instructions.
- **Least privilege, enforced by construction:** the Researcher's tool list
  contains only Tavily search/extract; the Writer's tool list is *empty* —
  it receives findings in its prompt and nothing else; the Reviewer gets the
  rubric and the findings (so it can check sourcing) but no tools either.

## Before you start

- Root setup done.
- Keys in `.env`: `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`.

## Build steps

### Step 1 — The Researcher alone

Build `research(state)`: turn the topic into 3–5 search queries (model
generates them, or start with the topic itself plus two angles), call
Tavily search with `include_answer=False` (you want sources, not Tavily's
summary), then have the model distill results into `Finding` objects —
claim, URL, title, short excerpt. Validate with Pydantic; drop any finding
whose URL didn't come from the search results (models invent citations;
the schema + a URL allowlist is how you stop them).

**Check:** print the findings for your topic. Every URL must open to a real
page that supports the claim. Click three. This ten-minute habit is the
difference between research and fan fiction.

### Step 2 — The Writer, deliberately tool-less

Build `write(state)`: the prompt contains the topic, audience, the findings
(numbered), and — on revision rounds — the reviewer's fixes. Instruct: "Use
only the numbered findings. Cite as [n]. If the findings don't cover
something, leave it out." No tools are bound to this call at all.

**Check:** ask for a draft on a topic, then delete one finding and re-run.
The corresponding claim must disappear from the draft. If it doesn't, the
writer is writing from memory — tighten the prompt and lower the temperature
of your expectations (and of the call, if you set one).

### Step 3 — The Reviewer and the rubric

Write the rubric into the reviewer's prompt as scored criteria (1–5 each):
**accuracy** (claims match findings), **sourcing** (claims carry citations),
**clarity**, **audience fit**. Approval rule in code: `approved = all
scores >= 4` — the model scores, code decides. Fixes must be specific and
actionable ("Paragraph 2 claims X but finding [3] says Y — rewrite or cut"),
not vibes ("make it better"). Reject vague reviews in your prompt design:
"Every fix must name the paragraph and the finding it conflicts with."

**Check:** hand the reviewer a draft with one planted false claim. It must
catch it, score accuracy low, and name the conflict. If it approves, your
rubric isn't a rubric yet.

### Step 4 — The loop, with a cap

Wire the graph. State carries `revisions`; the conditional edge routes
rejected drafts back to `write` with `review.fixes` in state. At 3
revisions, exit with the latest draft flagged as unapproved.

**Check:** pick a hard topic/audience combo and watch at least one full
reject → revise → approve cycle in the logs. Then set the rubric impossibly
strict (all 5s required) and confirm the loop stops at the cap instead of
running forever.

### Step 5 — Show the work in the UI

Streamlit: topic + audience inputs; a progress view with three panels —
findings (with links), current draft, latest review (scores + fixes) — and
the revision count. Final output renders citations as links to the actual
sources. The UI matters here because *watching* the handoffs is how you
learn where teams break: usually at the contract, not the model.

## Run / deploy locally

```bash
cd 05-multi-agent
streamlit run app.py               # http://localhost:8501
```

## Done when

- [ ] Every claim in a final draft traces to a finding whose URL you clicked
      and verified supports it.
- [ ] Removing a finding removes its claim from the next draft (writer truly
      has no other source).
- [ ] A planted false claim is caught by the reviewer with a specific,
      paragraph-level fix.
- [ ] With an impossible rubric, the run terminates at 3 revisions and
      labels the draft unapproved.

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Invented citations | Writer or researcher generating URLs from memory | URL allowlist from actual Tavily results; validate in code |
| Writer ignores findings | Findings buried in a wall of prompt text | Number findings, demand [n] citations, restate the only-findings rule last |
| Reviewer approves everything | Rubric has no teeth; approval in the prompt, not code | Numeric scores + code-side threshold; require per-criterion justification |
| Fixes are useless ("improve clarity") | No specificity requirement | "Name the paragraph and the conflicting finding" rule in the reviewer prompt |
| Loop oscillates (fix A breaks B) | Writer gets only the latest fixes, forgets earlier ones | Pass the full review history; reviewer re-checks prior fixes explicitly |
| Costs creep up | Full draft + findings resent every round | Expected at this scale; note it — this is the real multi-agent tax, and why caps exist |

## Stretch exercise

Add a fourth agent: a **Fact-checker** between Writer and Reviewer whose
only job is claim-by-claim verification of the draft against the findings
(returns a list of unsupported claims). Compare its catch rate on planted
errors against the Reviewer's. You've just run your first agent-architecture
experiment — one role, one variable, measured outcome. That's the scientific
version of multi-agent design, and it beats intuition every time.

## Project references

- Tavily docs — https://docs.tavily.com/welcome
- LangGraph overview — https://docs.langchain.com/oss/python/langgraph/overview
- Tool use with Claude — https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
- Pydantic docs — https://docs.pydantic.dev/latest/
