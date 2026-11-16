"""Project 05 — Researcher, Writer & Reviewer Team (starter skeleton).

Skill: multi-agent collaboration — one role, one prompt, one toolset per
agent (least privilege); findings are the only bridge between research and
writing; a rubric-scored reviewer closes a capped revision loop.

Setup:
    pip install -r ../requirements.txt
    # .env needs ANTHROPIC_API_KEY and TAVILY_API_KEY

Run:
    streamlit run app.py            # http://localhost:8501

Graph: research -> write -> review --(approved or revisions==3)--> END
                              +--(rejected, revisions<3)--> write
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_REVISIONS = 3
APPROVAL_MIN_SCORE = 4  # every rubric criterion must reach this; code decides


# --------------------------------------------------------------------------
# Contracts — the state between agents is an API. Design it like one.
# --------------------------------------------------------------------------
class Finding(BaseModel):
    claim: str
    source_url: str
    source_title: str
    excerpt: str


class Review(BaseModel):
    scores: dict[str, int]  # accuracy, sourcing, clarity, audience_fit (1-5)
    fixes: list[str] = []  # specific: paragraph + conflicting finding

    @property
    def approved(self) -> bool:
        """Approval is computed in code from scores — never trusted from
        the model's own say-so."""
        return bool(self.scores) and all(
            s >= APPROVAL_MIN_SCORE for s in self.scores.values()
        )


class TeamState(BaseModel):
    topic: str
    audience: str
    findings: list[Finding] = []
    draft: str = ""
    review: Review | None = None
    revisions: int = 0


# --------------------------------------------------------------------------
# Researcher — the ONLY agent with tools (Tavily). Returns cited findings.
# --------------------------------------------------------------------------
RESEARCHER_PROMPT = (
    "You are a researcher. Return findings, not prose: each finding is one "
    "claim with the source that supports it. Use only URLs from the search "
    "results provided — never invent a source."
)


def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """One Tavily search; returns trimmed result dicts.

    TODO(step 1): from tavily import TavilyClient; client.search(query,
    max_results=..., include_answer=False) — you want sources, not a
    summary. Return [{title, url, content}].
    """
    raise NotImplementedError


def research(state: TeamState) -> TeamState:
    """Generate queries, search, distill results into Findings.

    TODO(step 1): 3-5 queries from topic+audience; collect results; ask the
    model to distill Finding objects; validate each Finding's source_url
    against the allowlist of URLs Tavily actually returned.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Writer — NO tools, by construction. Findings in the prompt are its world.
# --------------------------------------------------------------------------
WRITER_PROMPT = (
    "You are a writer. Draft using ONLY the numbered findings provided; "
    "cite as [n]. If the findings don't cover something, leave it out. "
    "On revision rounds, address every reviewer fix."
)


def write(state: TeamState) -> TeamState:
    """Draft (or revise) from state.findings alone.

    TODO(step 2): prompt = topic + audience + numbered findings +
    (state.review.fixes if revising). Bind NO tools to this call.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Reviewer — scores against the rubric; specificity is mandatory.
# --------------------------------------------------------------------------
REVIEWER_PROMPT = (
    "You are a reviewer. Score 1-5 on accuracy, sourcing, clarity, and "
    "audience fit. Every fix must name the paragraph and the finding it "
    "conflicts with — 'make it better' is not a fix. Check claims against "
    "the findings, not against your own knowledge."
)


def review(state: TeamState) -> TeamState:
    """Score the draft; store a Review (approval computed by the model
    class, enforced by the router below)."""
    # TODO(step 3): model returns scores + fixes as JSON -> Review.
    raise NotImplementedError


def route_after_review(state: TeamState) -> str:
    """Conditional edge: the cap is what makes this a loop, not a trap."""
    if state.review and state.review.approved:
        return "end"
    if state.revisions >= MAX_REVISIONS:
        return "end"  # deliver best draft, flagged unapproved
    return "write"


def build_graph():
    """Compile research -> write -> review -> (write | END).

    TODO(step 4): StateGraph over TeamState fields; increment revisions
    each time review rejects.
    """
    raise NotImplementedError


def run_team(topic: str, audience: str) -> TeamState:
    """Run the graph and return the final state (draft may be unapproved —
    check state.review.approved and say so in the UI)."""
    # TODO(step 4)
    raise NotImplementedError


# --------------------------------------------------------------------------
# Streamlit UI — three panels so the handoffs are visible.
# --------------------------------------------------------------------------
def main() -> None:
    """Topic/audience inputs; findings, draft, and review panels.

    TODO(step 5): render findings with clickable source links, the draft
    with [n] citations linked, and the review scores + fixes; show the
    revision count and a clear UNAPPROVED flag when the cap was hit.
    """
    import streamlit as st

    st.title("Researcher · Writer · Reviewer")
    st.info("Starter skeleton — implement the functions above per GUIDE.md.")


if __name__ == "__main__":
    main()
