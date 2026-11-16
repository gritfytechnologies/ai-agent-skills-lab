# Project 01 — Weather & Calendar Assistant

**Skill isolated: tool calling.** The model decides *what* to do; your code
decides *whether and how* it happens.

## Why this skill, why first

Every agent capability in this lab — memory lookups, plan checks, web
research, sending email — reduces to the same round trip:

1. You describe functions to the model as JSON schemas.
2. The model answers with a structured request to call one (`tool_use`).
3. Your code runs the function and returns the output (`tool_result`).
4. The model reads the result and either answers or asks for another call.

If you understand this loop deeply — including what happens when the function
fails — you understand the mechanical heart of every agent. This project
builds that loop by hand, against two real APIs, with a real chaining case:
*"Is it going to rain Saturday? If not, book a picnic with Sam at noon."*
Answering that requires the forecast **before** the booking decision, which is
the smallest honest example of an agent sequencing tools.

## What you'll build

A FastAPI service with one endpoint, `POST /chat`, that takes a user message
and runs the tool-use loop against three tools:

| Tool | Backing API | Purpose |
|------|-------------|---------|
| `get_forecast` | OpenWeather | 5-day forecast for a city |
| `list_events` | Google Calendar | What's already on the calendar for a date |
| `create_event` | Google Calendar | Book an event |

## Architecture, in words

Three layers, kept separate on purpose:

- **Tool definitions** — JSON schemas with descriptions. The description is
  part of the program: it's how the model knows when a tool applies.
- **Tool implementations** — plain Python functions that call the real APIs,
  validate their inputs with Pydantic, and convert failures into structured
  error results instead of exceptions that kill the loop.
- **The loop** — a `while` loop around the Claude Messages API: send messages
  + tool definitions; if the response contains `tool_use` blocks, execute
  them, append `tool_result`s, repeat; if not, that's the final answer. A
  hard iteration cap (10) guarantees the loop can always be stopped.

FastAPI wraps the loop so you can drive it with `curl` or the built-in
Swagger UI at `/docs`.

## Before you start

- Root setup done ([../SETUP.md](../SETUP.md)).
- Extra packages for the Google client:
  `pip install google-api-python-client google-auth google-auth-oauthlib`
- Keys in `.env`: `ANTHROPIC_API_KEY`, `OPENWEATHER_API_KEY`.
- Google Calendar OAuth: `credentials.json` in this folder (Desktop app
  client, Calendar API enabled — see SETUP.md §4).

## Build steps

### Step 1 — Get one raw tool call working (no loop yet)

Write `get_forecast(city: str, days: int)` as a plain function that calls
OpenWeather's 5-day forecast endpoint with `httpx` and returns a compact dict
(city, list of {date, summary, temp_min, temp_max, rain_mm}). Return *less*
than the API gives you — the model pays tokens for everything you hand back,
and raw OpenWeather JSON is mostly noise.

Then define its tool schema (name, description, `input_schema` with `city`
required) and make a single Messages API call with the prompt *"What's the
weather in Toronto this weekend?"* Print the response. You should see
`stop_reason: "tool_use"` and a `tool_use` block whose `input` matches your
schema.

**Check:** deliberately ask about something unrelated ("Write a haiku"). The
model should answer in text with no tool call. If it calls the tool anyway,
your description is too broad — tighten it.

### Step 2 — Close the loop

Implement `run_agent(user_message) -> str`:

```
messages = [user message]
loop up to 10 times:
    response = client.messages.create(model, tools=TOOLS, messages=messages)
    append assistant response to messages
    if stop_reason != "tool_use": return the text
    for each tool_use block: run the matching function, collect tool_result
    append all tool_results as one user message
raise/return an error if the cap is hit
```

Two details that matter:

- **Append the assistant's full response content**, not just the text — the
  API needs the `tool_use` blocks in history to match your `tool_result`s.
- **Batch parallel calls.** If the model requests two independent tools in
  one turn, execute both and return both results in a single user message.

**Check:** "What's the weather in Toronto and in Vancouver?" should produce
two forecast calls (in one turn or two) and one combined answer.

### Step 3 — Errors are results, not exceptions

Wrap every tool execution. If OpenWeather returns 404 (unknown city) or 401
(bad/not-yet-active key), do **not** raise. Return a `tool_result` with
`is_error: true` and a short human-readable message ("City not found:
'Toronot'"). Watch what the model does: it will usually apologize and ask the
user to clarify, or retry with a corrected spelling. That recovery behavior is
the entire point — an agent whose tools throw exceptions is a chatbot with
extra steps.

Also validate inputs *before* the API call with a Pydantic model
(`ForecastRequest`): `days` between 1 and 5, non-empty city. Invalid input
becomes an error result the model can react to.

**Check:** ask for the weather in "Toronot" and for a 40-day forecast. Both
should end in a sensible conversation, not a stack trace.

### Step 4 — Add the calendar tools

Implement OAuth once, in a helper: load `token.json` if present, otherwise run
the installed-app flow from `credentials.json` and save the token. Build the
Calendar service client from those credentials.

- `list_events(date)` → events on the primary calendar that day:
  title + start/end. Use `timeMin`/`timeMax` for the day's bounds in the
  user's timezone.
- `create_event(title, start_iso, end_iso, attendees=[])` → insert the event,
  return its id and HTML link.

Register both in the same tool list, with descriptions that say *when* to use
them ("Use before booking anything, to check for conflicts").

**Check:** "What do I have on Saturday?" lists real events. "Book a dentist
appointment Saturday at 10am for one hour" creates one — verify it in Google
Calendar itself.

### Step 5 — The chaining test

Now the prompt this project exists for:

> "If it's not raining Saturday afternoon, book 'Picnic with Sam' from noon
> to 3. If it is raining, don't book anything and tell me."

Trace the loop (add a `print` of each tool call while developing). Correct
behavior: `get_forecast` first → (check Saturday) → `list_events` to check
for a conflict → `create_event` only if both checks pass → final answer
explaining what it did and why. If the model books before checking the
forecast, strengthen the system prompt: *"Before booking any outdoor event,
check the forecast and the existing calendar."* System prompts are control
flow — treat them that way.

### Step 6 — Serve it

Wrap `run_agent` in the FastAPI app from the starter file: `POST /chat` with a
Pydantic request body (`message: str`) and response (`reply: str`,
`tool_calls: list[str]` — return the names of tools used, it makes debugging
and demos far easier).

## Run / deploy locally

```bash
cd 01-tool-calling
uvicorn app:app --reload          # serves on http://127.0.0.1:8000
```

Try it:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Will it rain in Toronto on Saturday?"}'
```

Or open http://127.0.0.1:8000/docs and use the interactive UI. First calendar
call opens a browser tab for Google consent; after that, `token.json` is
reused silently.

## Done when

- [ ] "Weather in X this weekend?" returns a real forecast with exactly one
      `get_forecast` call.
- [ ] A misspelled city and an out-of-range request both recover gracefully
      (error `tool_result`, sensible reply, no stack trace).
- [ ] The chaining prompt books the picnic **only** when the forecast is dry
      and the slot is free — and explains itself either way.
- [ ] The loop provably terminates: a prompt engineered to bounce between
      tools stops at the iteration cap with a clear message.

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| OpenWeather 401 on a brand-new key | Key not yet activated (up to ~2h) | Wait; test the key with `curl` directly |
| Model never calls the tool | Description too vague, or question answerable from memory | Name the capability and trigger conditions in the description |
| Model calls tools forever | Two tools' outputs keep prompting each other; no cap | Enforce the iteration cap; log each turn to see the cycle |
| `tool_result` rejected by the API | Assistant message not appended verbatim, or results split across messages | Append full response content; batch results in one user message |
| Calendar 403 / consent loop | API not enabled, or your account isn't a test user | Enable Calendar API; add yourself under OAuth consent screen → Test users |
| Huge token bills on weather calls | Returning raw API JSON | Trim tool outputs to the fields the model actually needs |

## Stretch exercise

Add a fourth tool, `cancel_event(event_id)`, and make the assistant confirm
with the user *in conversation* before cancelling ("You have 'Dentist' at
10:00 — cancel it?"). Notice what you just built: a conversational approval
gate. Project 06 turns that idea into a durable, auditable mechanism.

## Project references

- Tool use with Claude — https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
- OpenWeather API — https://openweathermap.org/api
- Google Calendar API — https://developers.google.com/calendar/api/guides/overview
- FastAPI — https://fastapi.tiangolo.com/ · Pydantic — https://docs.pydantic.dev/latest/
