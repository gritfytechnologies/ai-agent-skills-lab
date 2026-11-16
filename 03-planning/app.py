"""Project 03 — Trip Itinerary Planner (starter skeleton).

Skill: planning — draft a plan as data BEFORE calling tools, ground it with
real lookups, check it against hard constraints in code, revise in a bounded
loop, deliver a validated structure.

Setup:
    pip install -r ../requirements.txt
    # .env needs ANTHROPIC_API_KEY and GOOGLE_MAPS_API_KEY
    # (Places, Geocoding, and Distance Matrix / Routes APIs enabled)

Run:
    streamlit run app.py            # http://localhost:8501

Graph: intake -> draft_plan -> ground -> check --(violations & revs<2)-->
       draft_plan ; check --(ok or cap reached)--> deliver
"""

from __future__ import annotations

import os
from datetime import date

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
MAX_REVISIONS = 2
PACE_LIMITS = {"relaxed": 3, "standard": 5, "packed": 7}


# --------------------------------------------------------------------------
# Contracts — intake and itinerary are schemas, not vibes.
# --------------------------------------------------------------------------
class TripRequest(BaseModel):
    destination: str = Field(min_length=2)
    start_date: date
    end_date: date
    budget_total: float = Field(gt=0)
    currency: str = "CAD"
    interests: list[str] = Field(min_length=1)
    pace: str = "standard"  # relaxed | standard | packed

    @model_validator(mode="after")
    def _dates_sane(self) -> "TripRequest":
        # TODO(step 1): raise ValueError if end_date < start_date or
        # pace not in PACE_LIMITS.
        return self


class Stop(BaseModel):
    name: str
    address: str | None = None
    start_time: str  # "09:00"
    est_cost: float = 0.0
    verified: bool = False  # set by grounding; False = model-invented
    travel_minutes_from_prev: int | None = None


class DayPlan(BaseModel):
    day: date
    stops: list[Stop] = []


class Itinerary(BaseModel):
    destination: str
    days: list[DayPlan] = []
    total_est_cost: float = 0.0
    violations: list[str] = []  # remaining problems, admitted honestly


# --------------------------------------------------------------------------
# Maps tools — called by the ground node deterministically, NOT by the model.
# --------------------------------------------------------------------------
def search_places(destination: str, interest: str, limit: int = 5) -> list[dict]:
    """Real venues for an interest near a destination (Places API).

    TODO(step 3): GET https://maps.googleapis.com/maps/api/place/textsearch/json
    with query=f"{interest} in {destination}", key=MAPS_KEY.
    Return [{name, address, rating, place_id}] — trimmed, as always.
    """
    raise NotImplementedError


def travel_time(origin: str, destination: str) -> int:
    """Minutes between two addresses (Distance Matrix API).

    TODO(step 3): GET .../distancematrix/json, parse
    rows[0].elements[0].duration.value // 60. Cache by (origin, destination)
    pair — the revision loop will ask the same questions repeatedly.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Graph nodes
# --------------------------------------------------------------------------
def draft_plan(state: dict) -> dict:
    """Ask the model for a complete itinerary as JSON. NO tool calls here.

    TODO(step 2): prompt with the TripRequest (+ state["violations"] on
    revision rounds, quoted with exact numbers). Parse with
    Itinerary.model_validate_json; on failure retry once with the error
    appended, then raise.
    """
    raise NotImplementedError


def ground(state: dict) -> dict:
    """Replace guesses with facts: verify stops, fill travel times.

    TODO(step 3): for each stop, snap to the best search_places match
    (verified=True + real address) or leave verified=False; set
    travel_minutes_from_prev for consecutive stops via travel_time().
    """
    raise NotImplementedError


def check_plan(itinerary: Itinerary, request: TripRequest) -> list[str]:
    """Pure-Python constraint check. Arithmetic belongs in code, not in
    the model. Returns violation strings with exact figures.

    TODO(step 4): budget (sum of stop costs + daily allowance vs
    budget_total), any same-half-day leg > 60 travel minutes, stops/day
    over the pace limit.
    """
    raise NotImplementedError


def check(state: dict) -> dict:
    """Run check_plan and store violations in state (step 4)."""
    raise NotImplementedError


def route_after_check(state: dict) -> str:
    """Conditional edge: revise or deliver.

    TODO(step 5): return "draft_plan" if violations and
    state["revisions"] < MAX_REVISIONS, else "deliver". The cap is what
    makes this a loop instead of a trap.
    """
    raise NotImplementedError


def build_graph():
    """Compile: intake -> draft_plan -> ground -> check -> (revise|deliver).

    TODO(step 5): StateGraph(dict); intake just validates the TripRequest
    into state. deliver is a passthrough — the UI renders final state.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Streamlit UI
# --------------------------------------------------------------------------
def main() -> None:
    """Intake form + day-by-day itinerary rendering.

    TODO(step 6): form for TripRequest fields; on submit, run the graph;
    render one expander per day with stops, travel legs, per-day and total
    cost vs budget; show itinerary.violations prominently if non-empty;
    st.download_button for the itinerary JSON.
    """
    import streamlit as st

    st.title("Trip Itinerary Planner")
    st.info("Starter skeleton — implement the functions above per GUIDE.md.")


if __name__ == "__main__":
    main()
