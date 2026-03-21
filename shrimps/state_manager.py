"""Application state management for Cheeky Shrimps.

State is represented as a plain dict (serialisable to JSON for Dash stores).
All transitions are pure functions that accept a state dict and return a new
one — nothing is mutated in place.

Public surface
--------------
- ``blank_state()``          → initial empty state dict
- ``new_concept_map()``      → build a fresh graph for a root term
- ``expand_node()``          → grow the graph from a clicked node
- ``refresh_explanation()``  → regenerate the explanation text
- ``get_suggestions()``      → ask the LLM for next-step concepts
- ``add_flashcards()``       → generate and store flashcards for a node
- ``mark_practiced()``       → flag a node as practiced
- ``mark_caught()``          → flag a node as caught
- ``remove_node()``          → trim a node from the graph
- ``from_upload()``          → deserialise state from a file upload
- ``to_download()``          → serialise state for file download

``StateManager`` at the bottom is a thin backward-compatible shim.
"""

from __future__ import annotations

import base64
import copy
import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from typing import Any

from shrimps.config import help_markdown, llm_settings
from shrimps.llm_client import generate_text
from shrimps.prompts import (
    build_concept_graph_prompt,
    build_flashcard_prompt,
    build_resource_recommendations_prompt,
    build_weakness_report_prompt,
    expand_concept_graph_prompt,
    explain_concept_concise,
    explain_concept_detailed,
    parse_flashcards,
    parse_resource_recommendations,
    parse_terms,
    suggest_next_concepts,
)

log = logging.getLogger(__name__)

_CFG = llm_settings()
_HELP_MD = help_markdown()

# Path for persistent session storage
_PERSIST_PATH = os.path.join(os.path.dirname(__file__), "..", "shrimps_session.json")

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

State = dict[str, Any]

# ---------------------------------------------------------------------------
# Blank / initial state
# ---------------------------------------------------------------------------

def blank_state() -> State:
    """Return the default application state."""
    return {
        "node_data": {"start": {"parent": None, "distance": 0.0, "label": ""}},
        "clicked_nodes_list": [],
        "unclicked_nodes": [],
        "explanation_paragraph": _HELP_MD,
        "last_clicked": "start",
        "flashcards": {},
        "practiced_nodes": [],
        "caught_nodes": [],
        "quiz_history": [],
        "srs_schedule": {},   # node -> {interval, ease, due_ts, reps}
    }

# ---------------------------------------------------------------------------
# Node distance / breadth normalisation
# ---------------------------------------------------------------------------

def _normalise_nodes(node_data: dict) -> None:
    """Ensure every node carries consistent distance and breadth values.

    Mutates *node_data* in place — only called on freshly deep-copied dicts.
    """
    for data in node_data.values():
        if "raw_breadth" not in data:
            data["raw_breadth"] = 0.8 if data["parent"] is None else 1.2
        data["breadth"] = data["raw_breadth"]

        if data["parent"] is not None:
            if "raw_distance" not in data:
                data["raw_distance"] = 1.0
            data["distance"] = data["raw_distance"]

# ---------------------------------------------------------------------------
# LLM call helpers
# ---------------------------------------------------------------------------

def _call_for_concepts(prompt_fn, *args, max_retries: int = 5, count: int | None = None) -> dict | None:
    """Call the LLM and parse the response as a concept dict."""
    is_starter = prompt_fn is build_concept_graph_prompt
    n_terms = count if count is not None else (_CFG["starter_terms"] if is_starter else _CFG["further_terms"])

    for attempt in range(max_retries):
        try:
            response = generate_text(prompt_fn(*args, n_terms))
            parsed = parse_terms(response, max_terms=n_terms)
            if parsed:
                return parsed
        except Exception:
            log.exception("Concept LLM call failed (attempt %d/%d)", attempt + 1, max_retries)
        if attempt < max_retries - 1:
            time.sleep(_CFG["retry_delay"])

    return None


def _call_for_text(prompt_fn, *args, max_retries: int = 5, strong: bool = False) -> str | None:
    """Call the LLM and return the raw text response."""
    # Explanations and analysis need more room; structured concept lists do not
    max_tokens = 1024 if strong else 256
    for attempt in range(max_retries):
        try:
            return generate_text(prompt_fn(*args), strong=strong, max_tokens=max_tokens)
        except Exception:
            log.exception("Text LLM call failed (attempt %d/%d)", attempt + 1, max_retries)
        if attempt < max_retries - 1:
            time.sleep(_CFG["retry_delay"])

    return None

# ---------------------------------------------------------------------------
# Explanation generation
# ---------------------------------------------------------------------------

def _generate_explanation(term: str, known: list, unknown: list, mode: str = "short") -> str:
    """Generate an explanation for *term* given known/unknown concept lists."""
    prompt_fn = explain_concept_concise if mode == "short" else explain_concept_detailed
    result = _call_for_text(prompt_fn, term, known, unknown, strong=True)
    return result or "Could not generate explanation — please try again."

# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def new_concept_map_from_text(document_text: str, length_mode: str = "short") -> State | None:
    """Build a concept graph from pasted document/PDF text."""
    from shrimps.prompts import build_concept_graph_from_text_prompt, parse_concept_graph_from_text
    log.info("[doc] calling LLM with %d chars of document text", len(document_text))
    response = _call_for_text(lambda: build_concept_graph_from_text_prompt(document_text), strong=True)
    if not response:
        log.warning("[doc] LLM returned no response")
        return None
    log.info("[doc] LLM response: %s", response[:300])
    root, concepts = parse_concept_graph_from_text(response)
    if not root:
        log.warning("[doc] could not parse root concept from response")
        return None
    if not concepts:
        log.warning("[doc] could not parse any concepts from response")
        return None
    log.info("[doc] root=%r concepts=%s", root, list(concepts.keys()))

    node_data: dict = {"start": {"parent": None, "distance": 0.0, "label": root}}
    for name, props in concepts.items():
        node_data[name] = {
            "parent": "start",
            "distance": props["distance"],
            "raw_distance": props["distance"],
            "breadth": props["breadth"],
            "raw_breadth": props["breadth"],
        }
    _normalise_nodes(node_data)

    persisted = load_session()
    state: State = {
        "node_data": node_data,
        "clicked_nodes_list": [],
        "unclicked_nodes": [k for k in node_data if k != "start"],
        "last_clicked": "start",
        "flashcards": {},
        "practiced_nodes": [],
        "caught_nodes": [],
        "quiz_history": persisted.get("quiz_history", []),
        "srs_schedule": persisted.get("srs_schedule", {}),
    }
    state["explanation_paragraph"] = _generate_explanation(
        root, state["clicked_nodes_list"], state["unclicked_nodes"], length_mode
    )
    return state


def new_concept_map(term: str, length_mode: str = "short", node_count: int | None = None) -> State | None:
    """Build a fresh concept graph rooted at *term*."""
    concepts = _call_for_concepts(build_concept_graph_prompt, term, count=node_count)
    if not concepts:
        log.warning("Could not build concept map for %r", term)
        return None

    node_data: dict = {"start": {"parent": None, "distance": 0.0, "label": term}}
    for name, props in concepts.items():
        node_data[name] = {
            "parent": "start",
            "distance": props["distance"],
            "raw_distance": props["distance"],
            "breadth": props["breadth"],
            "raw_breadth": props["breadth"],
        }
    _normalise_nodes(node_data)

    persisted = load_session()
    state: State = {
        "node_data": node_data,
        "clicked_nodes_list": [],
        "unclicked_nodes": [k for k in node_data if k != "start"],
        "last_clicked": "start",
        "flashcards": {},
        "practiced_nodes": [],
        "caught_nodes": [],
        "quiz_history": persisted.get("quiz_history", []),
        "srs_schedule": persisted.get("srs_schedule", {}),
    }
    state["explanation_paragraph"] = _generate_explanation(
        term, state["clicked_nodes_list"], state["unclicked_nodes"], length_mode
    )
    return state


def expand_node(state: State, node: str, node_count: int | None = None) -> State:
    """Grow the graph by expanding *node* and adding new child concepts."""
    if node in state["clicked_nodes_list"]:
        return state

    s = copy.deepcopy(state)
    s["clicked_nodes_list"].append(node)
    if node in s["unclicked_nodes"]:
        s["unclicked_nodes"].remove(node)

    root_term = s["node_data"]["start"].get("label", "start")
    concepts = _call_for_concepts(
        expand_concept_graph_prompt,
        root_term,
        s["unclicked_nodes"],
        s["clicked_nodes_list"],
        count=node_count,
    )

    if not concepts:
        log.warning("Could not expand node %r", node)
        s["last_clicked"] = node
        return s

    for name, props in concepts.items():
        if name not in s["node_data"]:
            s["node_data"][name] = {
                "parent": node,
                "distance": props["distance"],
                "raw_distance": props["distance"],
                "breadth": props["breadth"],
                "raw_breadth": props["breadth"],
            }
            if name not in s["clicked_nodes_list"]:
                s["unclicked_nodes"].append(name)

    _normalise_nodes(s["node_data"])
    s["last_clicked"] = node
    return s


def refresh_explanation(state: State, length_mode: str = "short") -> State:
    """Return a new state with a freshly generated explanation."""
    term = state.get("node_data", {}).get("start", {}).get("label", "")
    if not term:
        return state
    s = copy.deepcopy(state)
    s["explanation_paragraph"] = _generate_explanation(
        term,
        s.get("clicked_nodes_list", []),
        s.get("unclicked_nodes", []),
        length_mode,
    )
    return s


def get_suggestions(state: State) -> list[str]:
    """Return a list of suggested next concepts based on current graph state."""
    if not state.get("node_data", {}).get("start", {}).get("label"):
        return []
    try:
        prompt = suggest_next_concepts(
            state.get("unclicked_nodes", []),
            state.get("clicked_nodes_list", []),
        )
        raw = generate_text(prompt)
        return [s.strip() for s in raw.split(",") if s.strip()][: _CFG["suggestion_terms"]]
    except Exception:
        log.exception("Failed to fetch concept suggestions")
        return []


def add_flashcards(state: State, node: str) -> State:
    """Generate flashcards for *node* and store them in state."""
    root_term = state.get("node_data", {}).get("start", {}).get("label", "")
    response = generate_text(build_flashcard_prompt(node, root_term))
    cards = parse_flashcards(response)
    s = copy.deepcopy(state)
    s["flashcards"][node] = cards
    return s


def mark_practiced(state: State, node: str) -> State:
    """Flag *node* as having had flashcards started."""
    if node in state.get("practiced_nodes", []):
        return state
    s = copy.deepcopy(state)
    s["practiced_nodes"].append(node)
    return s


def mark_caught(state: State, node: str) -> State:
    """Flag *node* as fully reviewed."""
    if node in state.get("caught_nodes", []):
        return state
    s = copy.deepcopy(state)
    s["caught_nodes"].append(node)
    return s


def remove_node(state: State, node: str) -> State:
    """Remove *node* from the graph, re-parenting its children to its parent."""
    if node == "start":
        return state
    s = copy.deepcopy(state)
    nd = s["node_data"]
    fallback_parent = nd.get(node, {}).get("parent", "start") or "start"

    for data in nd.values():
        if data.get("parent") == node:
            data["parent"] = fallback_parent

    nd.pop(node, None)
    s["flashcards"].pop(node, None)

    for key in ("clicked_nodes_list", "unclicked_nodes", "practiced_nodes", "caught_nodes"):
        lst = s.get(key, [])
        if node in lst:
            lst.remove(node)

    return s

def _srs_update(schedule: dict, node: str, was_correct: bool) -> dict:
    """Update the SM-2-inspired spaced repetition schedule for a node."""
    s = copy.deepcopy(schedule)
    entry = s.get(node, {"interval": 1, "ease": 2.5, "reps": 0, "due_ts": 0})
    now = time.time()
    if was_correct:
        entry["reps"] += 1
        if entry["reps"] == 1:
            entry["interval"] = 1
        elif entry["reps"] == 2:
            entry["interval"] = 6
        else:
            entry["interval"] = math.ceil(entry["interval"] * entry["ease"])
        entry["ease"] = max(1.3, entry["ease"] + 0.1)
    else:
        entry["reps"] = 0
        entry["interval"] = 1
        entry["ease"] = max(1.3, entry["ease"] - 0.2)
    entry["due_ts"] = now + entry["interval"] * 86400
    s[node] = entry
    return s


def record_quiz_answer(
    state: State,
    node: str,
    question: str,
    correct_answer: str,
    chosen: str,
    was_correct: bool,
) -> State:
    """Append a quiz answer event to the history log and update SRS schedule."""
    s = copy.deepcopy(state)
    s.setdefault("quiz_history", []).append({
        "node": node,
        "question": question,
        "correct_answer": correct_answer,
        "chosen": chosen,
        "was_correct": was_correct,
        "ts": time.time(),
    })
    s["srs_schedule"] = _srs_update(s.get("srs_schedule", {}), node, was_correct)
    return s


def get_weakness_report(state: State) -> str:
    """Ask the LLM to analyse wrong answers and return a remediation report."""
    wrong = [e for e in state.get("quiz_history", []) if not e["was_correct"]]
    if not wrong:
        return "No mistakes recorded yet — keep quizzing!"
    prompt = build_weakness_report_prompt(wrong)
    result = _call_for_text(lambda: prompt, strong=True)
    return result or "Could not generate report — please try again."


def get_resource_recommendations(state: State) -> list[dict]:
    """Ask the LLM to recommend online resources for the student's weak areas."""
    wrong = [e for e in state.get("quiz_history", []) if not e["was_correct"]]
    if not wrong:
        return []
    prompt = build_resource_recommendations_prompt(wrong)
    result = _call_for_text(lambda: prompt, strong=True)
    if not result:
        return []
    return parse_resource_recommendations(result)


def get_srs_due_nodes(state: State) -> list[str]:
    """Return nodes whose SRS review is due now, sorted by most overdue first."""
    now = time.time()
    schedule = state.get("srs_schedule", {})
    due = [(node, entry["due_ts"]) for node, entry in schedule.items() if entry["due_ts"] <= now]
    due.sort(key=lambda x: x[1])
    return [node for node, _ in due]


def get_node_quiz_stats(state: State) -> dict[str, dict]:
    """Return per-node quiz performance stats for graph colouring."""
    stats: dict[str, dict] = {}
    for entry in state.get("quiz_history", []):
        node = entry["node"]
        if node not in stats:
            stats[node] = {"correct": 0, "wrong": 0}
        if entry["was_correct"]:
            stats[node]["correct"] += 1
        else:
            stats[node]["wrong"] += 1
    return stats


# ---------------------------------------------------------------------------
# Persistence (disk-backed session)
# ---------------------------------------------------------------------------

def save_session(state: State) -> None:
    """Persist quiz_history and srs_schedule to disk so they survive restarts."""
    try:
        payload = {
            "quiz_history": state.get("quiz_history", []),
            "srs_schedule": state.get("srs_schedule", {}),
        }
        with open(_PERSIST_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        log.exception("Failed to save session to disk")


def load_session() -> dict:
    """Load persisted quiz_history and srs_schedule from disk."""
    try:
        if os.path.exists(_PERSIST_PATH):
            with open(_PERSIST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        log.exception("Failed to load session from disk")
    return {"quiz_history": [], "srs_schedule": {}}


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def from_upload(contents: str) -> State | None:
    """Deserialise state from a Dash upload component's base64 payload."""
    try:
        _, encoded = contents.split(",", 1)
        data = json.loads(base64.b64decode(encoded).decode("utf-8"))
        node_data = data.get("node_data", {})
        _normalise_nodes(node_data)
        persisted = load_session()
        return {
            "node_data": node_data,
            "clicked_nodes_list": data.get("clicked_nodes_list", []),
            "unclicked_nodes": data.get("unclicked_nodes", []),
            "explanation_paragraph": data.get("explanation", _HELP_MD),
            "last_clicked": "start",
            "flashcards": data.get("flashcards", {}),
            "practiced_nodes": data.get("practiced_nodes", []),
            "caught_nodes": data.get("caught_nodes", []),
            "quiz_history": data.get("quiz_history", persisted.get("quiz_history", [])),
            "srs_schedule": data.get("srs_schedule", persisted.get("srs_schedule", {})),
        }
    except Exception:
        log.exception("Failed to deserialise uploaded state")
        return None


def to_download(state: State) -> str:
    """Serialise state to a JSON string suitable for file download."""
    return json.dumps({
        "node_data": state["node_data"],
        "clicked_nodes_list": state["clicked_nodes_list"],
        "unclicked_nodes": state["unclicked_nodes"],
        "explanation": state["explanation_paragraph"],
        "flashcards": state.get("flashcards", {}),
        "practiced_nodes": state.get("practiced_nodes", []),
        "caught_nodes": state.get("caught_nodes", []),
        "quiz_history": state.get("quiz_history", []),
        "srs_schedule": state.get("srs_schedule", {}),
    }, indent=2)

# ---------------------------------------------------------------------------
# Backward-compatible shim
# ---------------------------------------------------------------------------

class StateManager:
    """Thin shim mapping the old static-method API onto the module functions.

    Kept so that ``callback_handlers.py`` requires no changes.
    """

    @staticmethod
    def get_initial_state() -> State:
        persisted = load_session()
        s = blank_state()
        s["quiz_history"] = persisted.get("quiz_history", [])
        s["srs_schedule"] = persisted.get("srs_schedule", {})
        return s

    @staticmethod
    def recompute_node_distances(node_data: dict) -> None:
        _normalise_nodes(node_data)

    @staticmethod
    def create_new_concept_map(term: str, length_flag: str = "short", node_count: int | None = None) -> State | None:
        return new_concept_map(term, length_flag, node_count)

    @staticmethod
    def create_concept_map_from_text(text: str, length_flag: str = "short") -> State | None:
        return new_concept_map_from_text(text, length_flag)

    @staticmethod
    def expand_concept_map(state: State, node: str, node_count: int | None = None) -> State:
        return expand_node(state, node, node_count)

    @staticmethod
    def generate_explanation(term: str, known: list, unknown: list, mode: str = "short") -> str:
        return _generate_explanation(term, known, unknown, mode)

    @staticmethod
    def get_suggested_concepts(state: State) -> list[str]:
        return get_suggestions(state)

    @staticmethod
    def update_explanation_length(state: State, length_flag: str) -> State:
        return refresh_explanation(state, length_flag)

    @staticmethod
    def reload_explanation(state: State, length_flag: str) -> State:
        return refresh_explanation(state, length_flag)

    @staticmethod
    def get_current_term(state: State) -> str:
        return state.get("node_data", {}).get("start", {}).get("label", "")

    @staticmethod
    def has_valid_concept(state: State) -> bool:
        return bool(StateManager.get_current_term(state))

    @staticmethod
    def generate_flashcards(state: State, node: str) -> State:
        return add_flashcards(state, node)

    @staticmethod
    def mark_practiced(state: State, node: str) -> State:
        return mark_practiced(state, node)

    @staticmethod
    def mark_caught(state: State, node: str) -> State:
        return mark_caught(state, node)

    @staticmethod
    def trim_node(state: State, node: str) -> State:
        return remove_node(state, node)

    @staticmethod
    def record_quiz_answer(state: State, node: str, question: str, correct_answer: str, chosen: str, was_correct: bool) -> State:
        new_state = record_quiz_answer(state, node, question, correct_answer, chosen, was_correct)
        save_session(new_state)
        return new_state

    @staticmethod
    def get_weakness_report(state: State) -> str:
        return get_weakness_report(state)

    @staticmethod
    def get_resource_recommendations(state: State) -> list[dict]:
        return get_resource_recommendations(state)

    @staticmethod
    def get_srs_due_nodes(state: State) -> list[str]:
        return get_srs_due_nodes(state)

    @staticmethod
    def get_node_quiz_stats(state: State) -> dict[str, dict]:
        return get_node_quiz_stats(state)

    @staticmethod
    def load_state_from_upload(contents: str) -> State | None:
        return from_upload(contents)

    @staticmethod
    def export_state_for_download(state: State) -> str:
        return to_download(state)