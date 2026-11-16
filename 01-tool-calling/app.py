"""Project 01 — Weather & Calendar Assistant (starter skeleton).

Skill: tool calling. The agent loop lives in run_agent(); the tools are
defined as JSON schemas in TOOLS and implemented as plain functions.

Setup:
    pip install -r ../requirements.txt
    pip install google-api-python-client google-auth google-auth-oauthlib
    # .env needs ANTHROPIC_API_KEY and OPENWEATHER_API_KEY
    # credentials.json (Google OAuth, Desktop app) in this folder

Run:
    uvicorn app:app --reload
    curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
        -d '{"message": "Will it rain in Toronto on Saturday?"}'
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_TOOL_ROUNDS = 10  # hard cap: the loop must always be able to stop

SYSTEM_PROMPT = (
    "You are a weather and calendar assistant. Before booking any outdoor "
    "event, check the forecast and the existing calendar. Explain what you "
    "did and why."
)


# --------------------------------------------------------------------------
# Tool input validation (Pydantic) — invalid input becomes an error result.
# --------------------------------------------------------------------------
class ForecastRequest(BaseModel):
    city: str = Field(min_length=1)
    days: int = Field(default=3, ge=1, le=5)


class CreateEventRequest(BaseModel):
    title: str = Field(min_length=1)
    start_iso: str  # ISO 8601, e.g. 2026-11-21T12:00:00-05:00
    end_iso: str
    attendees: list[str] = []


# --------------------------------------------------------------------------
# Tool implementations — plain functions. Return small dicts, not raw API
# payloads: the model pays tokens for everything you hand back.
# --------------------------------------------------------------------------
def get_forecast(city: str, days: int = 3) -> dict[str, Any]:
    """Call OpenWeather's 5-day forecast endpoint and trim the result."""
    # TODO(step 1): GET https://api.openweathermap.org/data/2.5/forecast
    #   params: q=city, appid=OPENWEATHER_API_KEY, units=metric
    # TODO(step 1): aggregate the 3-hour entries into per-day summaries:
    #   {city, days: [{date, summary, temp_min, temp_max, rain_mm}]}
    raise NotImplementedError


def list_events(date: str) -> dict[str, Any]:
    """List events on the primary Google Calendar for one YYYY-MM-DD date."""
    # TODO(step 4): build the Calendar service via _calendar_service(),
    #   query events().list with timeMin/timeMax for that day,
    #   return {date, events: [{title, start, end}]}
    raise NotImplementedError


def create_event(
    title: str, start_iso: str, end_iso: str, attendees: list[str] | None = None
) -> dict[str, Any]:
    """Create a Google Calendar event; return its id and link."""
    # TODO(step 4): events().insert on the primary calendar,
    #   return {event_id, html_link}
    raise NotImplementedError


def _calendar_service():
    """Build an authenticated Google Calendar client (OAuth desktop flow).

    TODO(step 4): load token.json if it exists; otherwise run
    InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE,
    scopes=["https://www.googleapis.com/auth/calendar"]) and save the token.
    Import google libraries here, not at module top, so the app imports
    cleanly before they are installed.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Tool schemas — the descriptions are part of the program. They tell the
# model WHEN each tool applies.
# --------------------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_forecast",
        "description": (
            "Get the weather forecast for a city for the next 1-5 days. "
            "Use whenever the user asks about upcoming weather or is "
            "planning something outdoors."
        ),
        "input_schema": ForecastRequest.model_json_schema(),
    },
    {
        "name": "list_events",
        "description": (
            "List what is already on the user's calendar for a date "
            "(YYYY-MM-DD). Use before booking anything, to check conflicts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"date": {"type": "string"}},
            "required": ["date"],
        },
    },
    {
        "name": "create_event",
        "description": (
            "Create an event on the user's calendar. Only call after "
            "checking the forecast (for outdoor events) and list_events "
            "for the same slot."
        ),
        "input_schema": CreateEventRequest.model_json_schema(),
    },
]

TOOL_FUNCTIONS = {
    "get_forecast": get_forecast,
    "list_events": list_events,
    "create_event": create_event,
}


def execute_tool(name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
    """Run one tool; return (result_text, is_error).

    TODO(step 3): never let an exception escape — catch API errors and
    validation errors and return them as error results so the model can
    recover in conversation.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# The agent loop — the heart of this project.
# --------------------------------------------------------------------------
def run_agent(user_message: str) -> tuple[str, list[str]]:
    """Run the tool-use loop; return (final_reply, tool_names_used).

    TODO(step 2):
      messages = [{"role": "user", "content": user_message}]
      for _ in range(MAX_TOOL_ROUNDS):
          response = client.messages.create(
              model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT,
              tools=TOOLS, messages=messages)
          messages.append({"role": "assistant", "content": response.content})
          if response.stop_reason != "tool_use":
              return extracted_text, tools_used
          results = [execute each tool_use block -> tool_result dicts]
          messages.append({"role": "user", "content": results})
      return "Stopped: too many tool rounds.", tools_used
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# HTTP surface
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[str] = []


app = FastAPI(title="Weather & Calendar Assistant")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    reply, tools_used = run_agent(req.message)
    return ChatResponse(reply=reply, tool_calls=tools_used)
