"""Project 02 — Study Coach That Remembers Progress (starter skeleton).

Skill: memory — structured facts in Postgres, meaning in pgvector, and a
compressed learner profile that loads into context at chat start.

Setup:
    docker compose up -d            # from the repo root (Postgres + pgvector)
    pip install -r ../requirements.txt
    # .env needs ANTHROPIC_API_KEY and DATABASE_URL

Run:
    streamlit run app.py            # http://localhost:8501

Schema (create on first run — see GUIDE.md step 1):
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE sessions (id serial PRIMARY KEY, started_at timestamptz
        DEFAULT now(), topic text, summary text);
    CREATE TABLE attempts (id serial PRIMARY KEY, session_id int,
        topic text, question text, answer text, correct boolean,
        created_at timestamptz DEFAULT now());
    CREATE TABLE notes (id serial PRIMARY KEY, session_id int, text text,
        embedding vector(1024));
    CREATE TABLE reviews (topic text PRIMARY KEY, due_on date,
        interval_days int DEFAULT 1);
    CREATE TABLE profile (id int PRIMARY KEY, profile_text text,
        updated_at timestamptz DEFAULT now());
"""

from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lab:lab@localhost:5432/lab")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
EMBEDDING_DIM = 1024  # must match the vector(N) column AND your embedder


class Attempt(BaseModel):
    topic: str
    question: str
    answer: str
    correct: bool


# --------------------------------------------------------------------------
# Storage layer — psycopg against the compose Postgres.
# --------------------------------------------------------------------------
def get_conn():
    """Return a psycopg connection; register the vector type.

    TODO(step 1): psycopg.connect(DATABASE_URL), then
    from pgvector.psycopg import register_vector; register_vector(conn).
    """
    raise NotImplementedError


def init_schema() -> None:
    """Create tables + the vector extension if they don't exist."""
    # TODO(step 1): execute the DDL from this module's docstring.
    raise NotImplementedError


def record_attempt(session_id: int, attempt: Attempt) -> None:
    """Insert one graded answer into attempts."""
    # TODO(step 1)
    raise NotImplementedError


def topic_stats() -> list[dict]:
    """Per-topic attempt counts and accuracy, computed in SQL."""
    # TODO(step 1): SELECT topic, count(*), avg(correct::int) ... GROUP BY
    raise NotImplementedError


# --------------------------------------------------------------------------
# Semantic memory — notes embedded into pgvector, recalled by meaning.
# --------------------------------------------------------------------------
def embed(text: str) -> list[float]:
    """Return an embedding vector for text.

    TODO(step 2): call the embeddings source you chose (see GUIDE.md) and
    assert len(result) == EMBEDDING_DIM. One source, used for BOTH storing
    and querying — mixing embedders silently breaks recall.
    """
    raise NotImplementedError


def store_note(session_id: int, text: str) -> None:
    """Embed a takeaway note and insert it into notes."""
    # TODO(step 2)
    raise NotImplementedError


def recall_notes(query_text: str, k: int = 4) -> list[str]:
    """Return the k notes closest in meaning to the query.

    TODO(step 2): SELECT text FROM notes ORDER BY embedding <=> %s LIMIT %s
    with the embedded query as the parameter.
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Profile + scheduling — the compressed, self-loading memory.
# --------------------------------------------------------------------------
def refresh_profile() -> str:
    """Rewrite the one-row learner profile from stats + session summaries.

    TODO(step 3): gather topic_stats(), weak spots (<70% over last 20
    attempts) and due reviews; ask the model for a ~150-word paragraph;
    REPLACE profile.profile_text (never append).
    """
    raise NotImplementedError


def load_profile() -> str:
    """Return the current profile text for the system prompt."""
    # TODO(step 3)
    raise NotImplementedError


def update_reviews(session_topics: dict[str, float]) -> None:
    """Spaced repetition: accuracy >= 0.8 doubles the interval, else the
    topic is due tomorrow. Upsert into reviews."""
    # TODO(step 5)
    raise NotImplementedError


def due_reviews(today: date | None = None) -> list[str]:
    """Topics whose review date has arrived."""
    # TODO(step 5)
    raise NotImplementedError


def maybe_summarize(threshold: int = 5) -> None:
    """Summarize old sessions once unsummarized ones pile up (step 4)."""
    # TODO(step 4): summarize the oldest batch into sessions.summary,
    # then refresh_profile() so it reads summaries, not raw history.
    raise NotImplementedError


# --------------------------------------------------------------------------
# LangGraph flow: load_profile -> coach -> record -> maybe_summarize
# --------------------------------------------------------------------------
def build_graph():
    """Compile the coach graph.

    TODO(step 6): StateGraph with a messages list + profile in state.
    - load_profile: state["profile"] = load_profile(); attach due reviews.
    - coach: one conversation turn; offer recall_notes as a tool.
    - record: persist attempts + takeaway notes from the turn.
    - maybe_summarize: run maybe_summarize() + update_reviews().
    """
    raise NotImplementedError


# --------------------------------------------------------------------------
# Streamlit UI
# --------------------------------------------------------------------------
def main() -> None:
    """Chat UI with a sidebar that makes memory visible.

    TODO(step 6): st.chat_input / st.chat_message for the conversation;
    sidebar shows load_profile(), topic_stats() as a small table, and
    due_reviews(). Keep the graph in st.session_state.
    """
    import streamlit as st  # local import: keeps this module importable in tests

    st.title("Study Coach")
    st.info("Starter skeleton — implement the functions above per GUIDE.md.")


if __name__ == "__main__":
    main()
