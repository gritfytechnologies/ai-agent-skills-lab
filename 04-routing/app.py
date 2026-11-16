"""Project 04 — Support Ticket Router (starter skeleton).

Skill: routing — classify into structured data, threshold on confidence,
hand off to least-privilege specialists, escalate the unsure to humans,
log everything, and measure accuracy on a labeled set.

Setup:
    docker compose up -d            # from the repo root
    pip install -r ../requirements.txt
    # .env needs ANTHROPIC_API_KEY and DATABASE_URL

Run:
    uvicorn app:app --reload        # http://127.0.0.1:8000/docs
    python test_router.py           # you create this in GUIDE.md step 5

Tables (create on first run):
    CREATE TABLE route_log (id serial PRIMARY KEY,
        created_at timestamptz DEFAULT now(), ticket_text text,
        category text, confidence real, routed_to text, correct boolean);
    CREATE TABLE human_queue (id serial PRIMARY KEY,
        created_at timestamptz DEFAULT now(), ticket_text text,
        reason text);
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lab:lab@localhost:5432/lab")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
# Classification is high-volume and low-complexity — a smaller/faster model
# tier is the right call here. Routing the router is part of the lesson.
CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", MODEL)
CONFIDENCE_THRESHOLD = 0.7

Category = Literal["billing", "technical", "account"]


class Classification(BaseModel):
    category: Category
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class TicketRequest(BaseModel):
    ticket_text: str = Field(min_length=3)
    customer_id: str | None = None


class TicketResponse(BaseModel):
    reply: str
    category: Category | None = None
    confidence: float | None = None
    routed_to: str  # billing | technical | account | human_queue


# --------------------------------------------------------------------------
# Classifier — one call, strict JSON contract.
# --------------------------------------------------------------------------
CLASSIFIER_PROMPT = """Classify this support ticket as billing, technical,
or account. Output ONLY JSON matching: {"category": ..., "confidence": ...,
"reason": ...}.

Confidence is a judgment, not a formality: below 0.7 means a human should
handle it. Use low confidence whenever two categories fit, key facts are
missing, or the request is ambiguous.

Ticket: {ticket}
"""


def classify(ticket_text: str) -> Classification:
    """Return a validated Classification for the ticket.

    TODO(step 1): call CLASSIFIER_MODEL with CLASSIFIER_PROMPT, parse with
    Classification.model_validate_json; on failure retry once with the
    validation error appended.
    """
    raise NotImplementedError


def route_for(c: Classification) -> str:
    """The routing rule lives in CODE, not in the prompt."""
    if c.confidence < CONFIDENCE_THRESHOLD:
        return "human_queue"
    return c.category


# --------------------------------------------------------------------------
# Specialists — each gets ONLY its own prompt and tools (least privilege).
# Tools are stubbed against local data on purpose: the boundary is the lesson.
# --------------------------------------------------------------------------
INVOICES = {  # stub billing data
    "1042": {"customer_id": "cust_1", "amount": 49.0, "charges": 2},
}


def lookup_invoice(invoice_id: str) -> dict:
    """Billing tool."""
    # TODO(step 3): return INVOICES.get(invoice_id) or a not-found dict.
    raise NotImplementedError


def issue_refund(invoice_id: str) -> dict:
    """Billing tool — refunds above $100 must escalate per the prompt."""
    # TODO(step 3)
    raise NotImplementedError


def search_runbook(query: str) -> dict:
    """Technical tool — stub: return canned runbook entries by keyword."""
    # TODO(step 4)
    raise NotImplementedError


def check_service_status(service: str) -> dict:
    """Technical tool — stub status page."""
    # TODO(step 4)
    raise NotImplementedError


def lookup_account(email: str) -> dict:
    """Account tool — stub directory."""
    # TODO(step 4)
    raise NotImplementedError


def start_password_reset(email: str) -> dict:
    """Account tool."""
    # TODO(step 4)
    raise NotImplementedError


SPECIALISTS: dict[str, dict] = {
    "billing": {
        "system": (
            "You are a billing specialist. Look up the invoice before "
            "acting. You may refund up to $100; above that, explain and "
            "escalate. You cannot reset passwords or fix technical issues."
        ),
        "tools": {"lookup_invoice": lookup_invoice, "issue_refund": issue_refund},
    },
    "technical": {
        "system": (
            "You are a technical support specialist. Search the runbook and "
            "check service status before answering. You cannot touch "
            "billing or account credentials."
        ),
        "tools": {
            "search_runbook": search_runbook,
            "check_service_status": check_service_status,
        },
    },
    "account": {
        "system": (
            "You are an account specialist. Verify the account before "
            "starting a password reset. You cannot issue refunds or change "
            "billing."
        ),
        "tools": {
            "lookup_account": lookup_account,
            "start_password_reset": start_password_reset,
        },
    },
}


def run_specialist(category: str, ticket_text: str) -> str:
    """Run one specialist's tool loop (Project 01 pattern, scoped tools)."""
    # TODO(step 3/4): same loop as project 01, but tools/prompts come from
    # SPECIALISTS[category] only.
    raise NotImplementedError


# --------------------------------------------------------------------------
# Persistence — every decision is a row. Queued tickets are data too.
# --------------------------------------------------------------------------
def log_route(ticket_text: str, c: Classification | None, routed_to: str) -> None:
    """Insert a route_log row (correct stays NULL until evaluated)."""
    # TODO(step 5)
    raise NotImplementedError


def enqueue_human(ticket_text: str, reason: str) -> None:
    """Insert into human_queue."""
    # TODO(step 2)
    raise NotImplementedError


# --------------------------------------------------------------------------
# Graph: classify -> route -> specialist|human_queue -> log
# --------------------------------------------------------------------------
def build_graph():
    """TODO(step 3): StateGraph with classify, a conditional edge on
    route_for(), the three specialist nodes, human_queue, and log."""
    raise NotImplementedError


def handle_ticket(ticket_text: str) -> TicketResponse:
    """Orchestrate one ticket end to end (graph or plain functions)."""
    # TODO: classify -> route_for -> specialist or enqueue_human ->
    # log_route -> TicketResponse.
    raise NotImplementedError


# --------------------------------------------------------------------------
# HTTP surface
# --------------------------------------------------------------------------
app = FastAPI(title="Support Ticket Router")


@app.post("/tickets", response_model=TicketResponse)
def post_ticket(req: TicketRequest) -> TicketResponse:
    return handle_ticket(req.ticket_text)


@app.get("/queue")
def get_queue() -> list[dict]:
    """List human-queued tickets (step 6)."""
    # TODO(step 6): SELECT from human_queue, newest first.
    raise NotImplementedError


@app.get("/stats")
def get_stats() -> dict:
    """Counts by route from route_log (step 6)."""
    # TODO(step 6): SELECT routed_to, count(*) ... GROUP BY routed_to.
    raise NotImplementedError
