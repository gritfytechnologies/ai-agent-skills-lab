# References

The official documentation for everything this lab uses. When a guide and a
doc disagree, believe the doc — APIs move faster than tutorials. All links
verified live on 2026-11-16.

## Claude / Anthropic

- **Tool use with Claude** — https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
  How tool definitions, `tool_use` blocks, and `tool_result` round-trips work. The foundation of Project 01.
- **Claude API overview** — https://docs.claude.com/en/api/overview
  The Messages API surface, authentication, SDKs, and rate limits. Start here for any API question.

## LangGraph

- **LangGraph overview** — https://docs.langchain.com/oss/python/langgraph/overview
  What LangGraph is: a runtime for stateful agent graphs with durable execution and human-in-the-loop. (The docs moved here from langchain-ai.github.io/langgraph, which now redirects.)
- **Persistence** — https://docs.langchain.com/oss/python/langgraph/persistence
  Checkpointers (thread-scoped state) vs. stores (cross-thread memory). Required reading for Projects 02 and 06.
- **Interrupts / human-in-the-loop** — https://docs.langchain.com/oss/python/langgraph/human-in-the-loop
  How `interrupt()` pauses a graph, persists state, and resumes with `Command(resume=...)`. The core mechanism of Project 06 — read the "Rules of interrupts" section twice.

## Data & validation

- **pgvector README** — https://github.com/pgvector/pgvector
  Vector types, distance operators (`<->`, `<=>`, `<#>`), and HNSW/IVFFlat indexing for Postgres. Project 02's semantic recall lives here.
- **Pydantic docs** — https://docs.pydantic.dev/latest/
  Models, validators, and JSON Schema generation. Used in every project for tool inputs and structured outputs.

## App frameworks

- **FastAPI docs** — https://fastapi.tiangolo.com/
  Type-hint-driven APIs with automatic OpenAPI docs. The serving layer for Projects 01, 04, and 06.
- **Streamlit docs** — https://docs.streamlit.io/
  Python-only interactive apps — chat UI, session state, forms. The UI for Projects 02, 03, and 05.

## External APIs

- **OpenWeather API** — https://openweathermap.org/api
  Current weather and forecast endpoints used by Project 01. Note the free tier and the key-activation delay.
- **Google Calendar API overview** — https://developers.google.com/calendar/api/guides/overview
  Events, calendars, and ACL concepts behind Project 01's booking tool.
- **Google Maps Platform** — https://developers.google.com/maps
  Entry point for the Places, Geocoding, and Distance Matrix / Routes APIs used by Project 03.
- **Gmail API overview** — https://developers.google.com/gmail/api/guides
  Messages, threads, drafts, and labels — the surface Project 06 reads from and (only after approval) sends through.
- **Tavily docs** — https://docs.tavily.com/welcome
  Agent-oriented web search and extraction with cited results. Powers the Researcher in Project 05.
