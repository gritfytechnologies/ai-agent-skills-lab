"""Project 06 — Email Assistant with Send Approval (starter skeleton).

Skill: human-in-the-loop — the graph drafts, pauses DURABLY (Postgres
checkpointer + LangGraph interrupt), and only a human decision resumes it.
Every decision is audit-logged. The Gmail send call exists in exactly one
place, after the interrupt.

Setup:
    docker compose up -d            # from the repo root
    pip install -r ../requirements.txt
    pip install google-api-python-client google-auth google-auth-oauthlib
    pip install langgraph-checkpoint-postgres
    # credentials.json (Google OAuth, Gmail API) in this folder.
    # USE A TEST / SECONDARY GMAIL ACCOUNT for this project.

Run:
    uvicorn app:app --reload        # http://127.0.0.1:8000/docs

Graph: fetch_thread -> draft_reply -> [INTERRUPT: approve] -> send|discard
       -> audit

Tables:
    CREATE TABLE audit_log (id serial PRIMARY KEY,
        created_at timestamptz DEFAULT now(), gmail_thread_id text,
        decision text, draft_original text, draft_sent text,
        decided_by text, reason text);
    (plus LangGraph's own checkpoint tables, created by PostgresSaver.setup())
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


class Decision(BaseModel):
    """What a human can say to a paused draft. All three are first-class."""

    action: Literal["approved", "edited", "rejected"]
    edited_body: str | None = None  # required when action == "edited"
    reason: str | None = None  # expected when action == "rejected"
    decided_by: str = "me"


class DraftState(BaseModel):
    gmail_thread_id: str
    thread_summary: str = ""
    style_profile: str = ""
    draft: str = ""
    decision: Decision | None = None


# --------------------------------------------------------------------------
# Gmail access — read anywhere; SEND IN EXACTLY ONE PLACE (send_reply).
# --------------------------------------------------------------------------
def _gmail_service():
    """Authenticated Gmail client via OAuth desktop flow.

    TODO(step 1): same pattern as project 01, Gmail scopes
    (gmail.readonly + gmail.send). Import google libs lazily here.
    """
    raise NotImplementedError


def get_thread(gmail_thread_id: str) -> dict:
    """Fetch a thread: ordered messages with sender/date/body."""
    # TODO(step 1): users().threads().get; trim to what drafting needs.
    raise NotImplementedError


def send_reply(gmail_thread_id: str, body: str) -> dict:
    """THE send call site. Called only by the send node, after approval.

    TODO(step 4): build a MIME reply in-thread (same subject + threadId,
    In-Reply-To/References headers) and users().messages().send.
    grep this codebase: this must remain the only .send( on Gmail.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Drafting — the style profile is consulted, not the whole mailbox.
# --------------------------------------------------------------------------
def load_style_profile() -> str:
    """Read style_profile.md (write it by hand in step 2: greeting,
    sign-off, typical length, formality — from 3 real sent emails)."""
    # TODO(step 2)
    raise NotImplementedError


def draft_reply(state: DraftState) -> DraftState:
    """Draft a reply from thread + style profile. No send path exists in
    this function — drafting and sending are different nodes on purpose."""
    # TODO(step 2)
    raise NotImplementedError


# --------------------------------------------------------------------------
# The approval node — the heart of the project.
# --------------------------------------------------------------------------
def approve(state: DraftState) -> DraftState:
    """Pause the graph until a human decides.

    TODO(step 3): from langgraph.types import interrupt
        decision = interrupt({
            "gmail_thread_id": state.gmail_thread_id,
            "thread_summary": state.thread_summary,
            "draft": state.draft,
        })
        state.decision = Decision.model_validate(decision); return state

    Rules (from the LangGraph interrupts docs — read them twice):
    - NEVER wrap interrupt() in try/except; the pause IS an exception.
    - NO side effects before interrupt(): this node re-runs from the top
      on resume. The send lives in the NEXT node for this reason.
    - The resume value arrives via Command(resume=...) with the SAME
      graph thread_id used to start the run.
    """
    raise NotImplementedError


def send_or_discard(state: DraftState) -> DraftState:
    """Act on the decision: approved -> send draft; edited -> send
    edited_body; rejected -> send nothing."""
    # TODO(step 4)
    raise NotImplementedError


def audit(state: DraftState) -> DraftState:
    """Write the audit_log row AFTER the outcome is known: decision,
    original draft, final sent body (or NULL), reason, who, when."""
    # TODO(step 5)
    raise NotImplementedError


def build_graph():
    """Compile with a Postgres checkpointer so pauses survive restarts.

    TODO(step 3): from langgraph.checkpoint.postgres import PostgresSaver;
    with PostgresSaver.from_conn_string(DATABASE_URL) as saver:
        saver.setup(); graph.compile(checkpointer=saver)
    Keep the saver/connection lifetime managed at app level.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# HTTP surface
# --------------------------------------------------------------------------
class StartDraftRequest(BaseModel):
    gmail_thread_id: str = Field(min_length=1)


app = FastAPI(title="Email Assistant with Send Approval")


@app.post("/drafts")
def start_draft(req: StartDraftRequest) -> dict:
    """Run the graph to the interrupt; return the paused draft.

    TODO(step 6): graph.invoke(state, config={"configurable":
    {"thread_id": req.gmail_thread_id}}) — the result contains
    __interrupt__ with the draft payload. Return it; send NOTHING.
    """
    raise NotImplementedError


@app.post("/drafts/{gmail_thread_id}/decision")
def decide(gmail_thread_id: str, decision: Decision) -> dict:
    """Resume a paused graph with the human's decision.

    TODO(step 6): graph.invoke(Command(resume=decision.model_dump()),
    config with the SAME thread_id). Return the final state incl. audit.
    """
    raise NotImplementedError


@app.get("/audit")
def get_audit() -> list[dict]:
    """The decision history (step 5)."""
    # TODO(step 5): SELECT from audit_log, newest first.
    raise NotImplementedError
