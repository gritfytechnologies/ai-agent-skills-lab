# Project 03 — Trip Itinerary Planner

**Skill isolated: planning.** Write the plan down *before* acting, check it
against reality, revise it — then act.

## Why this skill

Projects 01 and 02's agents react: a request comes in, tools fire, an answer
comes out. That works until the task has interlocking constraints — a trip
must fit a budget, places close on certain days, and you can't be across town
in ten minutes. Reactive agents discover these problems *after* committing.
Planning agents catch them on paper, where mistakes are free.

The pattern you'll build is the one serious agents use everywhere:

1. **Intake** — turn a fuzzy request into structured data.
2. **Draft** — the model writes a complete plan *as data* before any tool is
   called.
3. **Ground** — tools replace guesses with facts (real places, real travel
   times, real distances).
4. **Check & revise** — deterministic code validates the plan against hard
   constraints (budget, travel-time sanity); violations go back to the model
   for a bounded number of revisions.
5. **Deliver** — a Pydantic-validated itinerary a program could consume, not
   just prose a human can read.

Note the division of labor: the model *proposes*, code *disposes*. Constraint
checking is arithmetic — never ask the model to do arithmetic it can get
wrong when a function can get it right.

## What you'll build

A Streamlit app: enter destination, dates, budget, and interests; get back a
day-by-day itinerary (morning/afternoon/evening blocks with places, travel
times between them, and estimated costs) that has been checked against your
budget and revised if it didn't fit.

## Architecture, in words

- **Intake model** — `TripRequest` (Pydantic): destination, start/end dates,
  budget_total, currency, interests list, pace (relaxed/standard/packed).
- **LangGraph graph** with five nodes:
  `intake → draft_plan → ground (Maps lookups) → check → deliver`,
  with a conditional edge from `check` back to `draft_plan` (max 2 revisions)
  when constraints fail.
- **Maps tools** (plain functions, called by the `ground` node — not by the
  model directly, which is itself a planning lesson: grounding is a
  deterministic step, not a creative one):
  - `search_places(destination, interest)` — Places API: real venues with
    ratings and addresses.
  - `travel_time(origin, destination)` — Distance Matrix / Routes API:
    minutes between consecutive stops.
- **Itinerary model** — `Itinerary` / `DayPlan` / `Stop` (Pydantic): the
  contract the final answer must satisfy. If it doesn't validate, it doesn't
  ship.

## Before you start

- Root setup done.
- Keys in `.env`: `ANTHROPIC_API_KEY`, `GOOGLE_MAPS_API_KEY` (Places,
  Geocoding, and Distance Matrix or Routes APIs enabled — see SETUP.md §4).

## Build steps

### Step 1 — Structured intake

Build `TripRequest` and a tiny Streamlit form for it. Validate hard: end
after start, budget > 0, at least one interest. Print the parsed object.

**Check:** invalid inputs (end before start, budget of −50) fail with clear
messages. Boring step, foundational habit: *every* agent boundary gets a
schema.

### Step 2 — Draft before tools

Write `draft_plan(state)`: prompt the model with the `TripRequest` and demand
the itinerary as JSON matching `Itinerary` — no tool calls allowed in this
node. Parse with `Itinerary.model_validate_json`. If parsing fails, retry
once with the validation error appended to the prompt ("fix these errors"),
then give up loudly.

**Check:** the draft *looks* plausible but contains invented places and
guessed travel times. That's expected — write down two specific inventions.
You're about to fix exactly those.

### Step 3 — Ground the draft

Write the Maps functions. `search_places` returns real venues per interest
(name, address, rating, place_id). `travel_time` returns minutes between two
addresses. The `ground` node walks the draft: for each stop, snap it to the
nearest real place match (or flag it `unverified` if none matches), and fill
in travel minutes between consecutive stops.

**Check:** the two inventions from step 2 are now either replaced by real
venues or visibly flagged. Nothing in the itinerary should be silently fake —
flagged is fine, hidden is not.

### Step 4 — Check constraints in code

Write `check_plan(itinerary, request) -> list[str]` in pure Python:

- Sum of estimated stop costs + a per-day food/transport allowance vs.
  `budget_total` → violation string with the overage amount.
- Any leg with travel time > 60 minutes between consecutive stops in the
  same half-day → violation.
- More stops per day than the pace allows (relaxed 3, standard 5, packed 7)
  → violation.

**Check:** set the budget absurdly low ($50 for three days). The checker must
report a specific overage, not a vibe.

### Step 5 — The revision loop

Wire the conditional edge: violations present and revisions < 2 → back to
`draft_plan`, this time with the violation strings in the prompt ("Revise:
the plan is $212 over budget; day 2 has a 95-minute leg between lunch and
the museum"). Revisions exhausted → deliver the best plan *with the remaining
violations attached and displayed*. A plan that admits its problems beats a
loop that never ends.

**Check:** with the $50 budget, watch one or two revision rounds actually
reduce the overage in the logs, and confirm the final output either fits or
honestly says it couldn't.

### Step 6 — Deliver in the UI

Render the validated `Itinerary`: one expander per day, stops with times,
travel legs, and per-day + total estimated cost vs. budget. Add a download
button for the JSON — the itinerary is data, so let it leave as data.

## Run / deploy locally

```bash
cd 03-planning
streamlit run app.py               # http://localhost:8501
```

## Done when

- [ ] A 3-day trip request returns a fully Pydantic-validated itinerary —
      every stop a real, Maps-verified place or explicitly flagged.
- [ ] Travel times between stops come from the Maps API, not the model's
      imagination (spot-check one leg against Google Maps).
- [ ] An impossibly small budget triggers at least one visible revision
      round and ends with a fitting plan or an honest violation report.
- [ ] The revision loop provably stops at the cap even when constraints
      can't be satisfied.

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Draft JSON won't parse | Model wrapped it in prose/fences, or schema too loose | Demand raw JSON, strip fences defensively, retry once with the validation error |
| Places search returns nothing | Interest text too specific, or API not enabled | Search per interest category; check the API is enabled and the key unrestricted enough |
| Every stop "unverified" | Matching draft names to Places results by exact string | Match on the top result within the destination; keep the flag for true misses |
| Revision loop makes it worse | Violations passed as vague prose | Pass exact numbers ("$212 over", "95-minute leg, day 2") — specifics get fixed |
| Costs never fit budget | Model's per-stop estimates are fantasy | Give the model a price-tier hint per interest, and let the checker use conservative per-stop defaults |
| Maps bill anxiety | Grounding calls every stop pair repeatedly | Cache travel_time results by (origin, destination) pair in a dict |

## Stretch exercise

Add opening-hours awareness: pull each venue's opening hours from Places and
add a checker rule — no stop scheduled when the venue is closed. You'll find
the revision loop suddenly doing genuinely clever things (moving the museum
from Monday to Tuesday). That moment — the planner visibly *reasoning around
reality* — is the whole skill in one demo.

## Project references

- LangGraph overview — https://docs.langchain.com/oss/python/langgraph/overview
- Google Maps Platform — https://developers.google.com/maps
- Pydantic docs — https://docs.pydantic.dev/latest/
- Streamlit docs — https://docs.streamlit.io/
