"""Dash callback wiring for the Cheeky Shrimps app.

Each function in this module registers a cohesive group of callbacks onto a
Dash app instance.  The public entry point is ``attach(app)``, which calls
every group in the correct order.

Structure
---------
attach(app)
  ├── _wire_reset(app)
  ├── _wire_interactions(app)
  ├── _wire_controls(app)
  ├── _wire_animations(app)
  ├── _wire_display(app)
  └── _wire_flashcards(app)
"""

from __future__ import annotations

import json
import random
from typing import Any

from dash import ALL, Input, Output, State, ctx, dcc, html, no_update

from shrimps.components import cytoscape_graph, info_box_content, suggested_concepts
from shrimps.config import palette, ui_styles
from shrimps.graph_layout_cytoscape import build_cytoscape_elements
from shrimps.llm_client import generate_text
from shrimps.prompts import build_quiz_prompt, parse_quiz_options
from shrimps.state_manager import StateManager

# ---------------------------------------------------------------------------
# Shared style constants
# ---------------------------------------------------------------------------

_COLORS = palette()
_STYLES = ui_styles()
_BTN_BASE = _STYLES["buttons"]["common"]
_BTN_TOOLBAR = _STYLES["buttons"]["toolbar"]

# ---------------------------------------------------------------------------
# Output lists used by multiple wiring functions
# ---------------------------------------------------------------------------

# The 8 outputs shared by all graph-interaction callbacks.
_GRAPH_OUTPUTS = [
    Output("graph-container", "children", allow_duplicate=True),
    Output("upload-graph", "contents", allow_duplicate=True),
    Output("input-overlay-visible", "data", allow_duplicate=True),
    Output("start-input", "value", allow_duplicate=True),
    Output("app-state-store", "data", allow_duplicate=True),
    Output("graph-key", "data", allow_duplicate=True),
    Output("input-flash", "data", allow_duplicate=True),
    Output("node-flash", "data", allow_duplicate=True),
]
_N_GRAPH = len(_GRAPH_OUTPUTS)

# Quiz outputs reused by both single-node and multi-card quiz callbacks.
_QUIZ_OUTPUTS = [
    Output("quiz-data", "data", allow_duplicate=True),
    Output("quiz-index", "data", allow_duplicate=True),
    Output("quiz-question", "children", allow_duplicate=True),
    Output("quiz-options", "children", allow_duplicate=True),
    Output("quiz-feedback", "children", allow_duplicate=True),
    Output("quiz-counter", "children", allow_duplicate=True),
    Output("quiz-streak", "data", allow_duplicate=True),
    Output("quiz-streak-display", "children", allow_duplicate=True),
    Output("quiz-answered", "data", allow_duplicate=True),
]
_N_QUIZ = len(_QUIZ_OUTPUTS)


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _chip(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a toolbar-chip style dict with optional overrides."""
    base = {**_BTN_BASE, **_BTN_TOOLBAR, "fontSize": "0.82em", "padding": "5px 13px"}
    if overrides:
        base.update(overrides)
    return base


_CHIP_HIDDEN = _chip({"display": "none"})
_DIV_HIDDEN  = {"color": "rgba(255,255,255,0.2)", "margin": "0 8px", "display": "none"}
_DIV_SHOWN   = {"color": "rgba(255,255,255,0.2)", "margin": "0 8px", "display": "inline"}

_TOPBAR_BASE = {
    "alignItems": "center", "gap": "6px", "flexWrap": "wrap",
    "paddingBottom": "12px", "marginBottom": "12px",
    "borderBottom": "1px solid rgba(255,255,255,0.1)",
}

_MODAL_BASE = {
    "position": "fixed", "top": 0, "left": 0,
    "width": "100vw", "height": "100vh",
    "backgroundColor": "rgba(0,0,0,0.6)", "zIndex": 1000,
    "alignItems": "center", "justifyContent": "center",
}

_OVERLAY_BASE = {
    "position": "absolute", "left": "50%", "top": "50%",
    "transform": "translate(-50%, -50%)", "zIndex": 10,
    "width": "100%", "display": "flex",
    "justifyContent": "center", "alignItems": "center",
    "transition": "opacity 0.3s ease, transform 0.3s ease",
}

# ---------------------------------------------------------------------------
# Component helpers
# ---------------------------------------------------------------------------

def _quiz_option_buttons(options: list[str]) -> list:
    """Render a list of strings as quiz answer buttons."""
    style = {
        "display": "block", "width": "100%", "textAlign": "left",
        "backgroundColor": "rgba(0,40,60,0.7)", "color": "#e8f4f0",
        "border": "1px solid rgba(168,218,220,0.3)", "borderRadius": "6px",
        "padding": "8px 12px", "marginBottom": "6px", "cursor": "pointer",
        "fontSize": "0.85em",
    }
    return [
        html.Button(opt, id={"type": "quiz-option", "index": i}, n_clicks=0, style=style)
        for i, opt in enumerate(options)
    ]

# ---------------------------------------------------------------------------
# Graph rebuild helper
# ---------------------------------------------------------------------------

def _rebuild_graph(state: dict, graph_key: int, **kwargs) -> tuple:
    """Rebuild cytoscape elements and return ``(graph_component, new_key)``."""
    elements = build_cytoscape_elements(
        state["node_data"],
        state["clicked_nodes_list"],
        state.get("last_clicked", "start"),
        practiced=state.get("practiced_nodes", []),
        caught=state.get("caught_nodes", []),
        flashcards=state.get("flashcards", {}),
        **kwargs,
    )
    new_key = (graph_key or 0) + 1
    return cytoscape_graph(elements, new_key), new_key

# ---------------------------------------------------------------------------
# Interaction result builders
# ---------------------------------------------------------------------------

def _graph_result(graph, new_key, state, *, overlay_hidden=False, flash=False):
    """Build the standard 8-value list expected by _GRAPH_OUTPUTS callbacks."""
    return [graph], no_update, not overlay_hidden, no_update, state, new_key, flash, None


def _submit_new_concept(term: str, graph_key: int, *, flash: bool = False) -> list:
    """Create a fresh concept map and return the _GRAPH_OUTPUTS-sized result."""
    new_state = StateManager.create_new_concept_map(term, "short")
    if not new_state:
        return [no_update] * _N_GRAPH
    graph, new_key = _rebuild_graph(new_state, graph_key)
    return [[graph], no_update, False, no_update, new_state, new_key, flash, None]


def _load_from_upload(contents: str, graph_key: int) -> list:
    """Restore state from an uploaded JSON file."""
    new_state = StateManager.load_state_from_upload(contents)
    if not new_state:
        return [no_update] * _N_GRAPH
    graph, new_key = _rebuild_graph(new_state, graph_key)
    return [[graph], None, False, no_update, new_state, new_key, False, None]


def _expand_node(tap_data: dict, state: dict, graph_key: int) -> list:
    """Expand the graph when an unvisited node is tapped."""
    node_id = tap_data.get("id", "")
    if not node_id or node_id == "start" or node_id.startswith("__emoji_"):
        return [no_update] * _N_GRAPH
    if node_id in state["clicked_nodes_list"]:
        return [no_update] * _N_GRAPH
    new_state = StateManager.expand_concept_map(state, node_id)
    graph, new_key = _rebuild_graph(new_state, graph_key, node_flash=node_id, selected_node=node_id)
    return [[graph], no_update, False, no_update, new_state, new_key, False, None]


def _run_quiz(node_label: str, state: dict, cards: list) -> list:
    """Call the LLM, parse quiz options, return _QUIZ_OUTPUTS-sized result or no_update list."""
    root_term = StateManager.get_current_term(state)
    response = generate_text(build_quiz_prompt(node_label, root_term, cards))
    quiz = parse_quiz_options(response, cards)
    if not quiz:
        return [None, 0, "Could not generate quiz.", [], "", "", 0, "", False]
    q = quiz[0]
    return [quiz, 0, q["q"], _quiz_option_buttons(q["options"]), "", f"1 / {len(quiz)}", 0, "", False]


# ---------------------------------------------------------------------------
# Reset / initialisation
# ---------------------------------------------------------------------------

def _wire_reset(app):

    @app.callback(
        [Output("graph-container", "children"),
         Output("upload-graph", "contents"),
         Output("input-overlay-visible", "data"),
         Output("start-input", "value"),
         Output("app-state-store", "data"),
         Output("graph-key", "data"),
         Output("input-flash", "data"),
         Output("node-flash", "data"),
         Output("toggle-animating", "data"),
         Output("submit-btn-flash", "data", allow_duplicate=True),
         Output("reload-triggered", "data", allow_duplicate=True),
         Output("reload-spinning", "data"),
         Output("reload-last-click", "data"),
         Output("reload-timer", "n_intervals"),
         Output("explanation-length-flag", "data")],
        Input("reset-term-btn", "n_clicks"),
        State("graph-key", "data"),
        prevent_initial_call=True,
    )
    def on_reset(_, graph_key):
        state = StateManager.get_initial_state()
        graph, new_key = _rebuild_graph(state, graph_key or 0)
        return [graph], None, True, "", state, new_key, False, None, False, False, False, False, 0, 0, "short"


# ---------------------------------------------------------------------------
# Main graph interactions (node tap, text submit, file upload)
# ---------------------------------------------------------------------------

def _wire_interactions(app):

    @app.callback(
        _GRAPH_OUTPUTS + [Output("selected-node", "data", allow_duplicate=True)],
        [Input({"type": "cyto-graph", "key": ALL}, "tapNodeData"),
         Input("start-input", "n_submit"),
         Input("upload-graph", "contents"),
         Input("submit-btn", "n_clicks")],
        [State("start-input", "value"),
         State("app-state-store", "data"),
         State("graph-key", "data"),
         State("explanation-length-flag", "data"),
         State("trim-mode", "data")],
        prevent_initial_call=True,
    )
    def on_main_interaction(tap_list, _n_submit, upload_contents, _n_clicks,
                            user_input, state, graph_key, _length_flag, trim_mode):
        trigger = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
        tap_data = next((d for d in tap_list if d), None)

        if trigger == "upload-graph" and upload_contents:
            return _load_from_upload(upload_contents, graph_key) + [no_update]

        if trigger in ("start-input", "submit-btn") and user_input:
            return _submit_new_concept(user_input.strip(), graph_key) + [None]

        if tap_data:
            node_id = tap_data.get("id", "")
            if node_id and node_id != "start" and not node_id.startswith("__emoji_"):

                if trim_mode:
                    new_state = StateManager.trim_node(state, node_id)
                    graph, new_key = _rebuild_graph(new_state, graph_key)
                    return [[graph], no_update, no_update, no_update, new_state, new_key, no_update, no_update, None]

                result = _expand_node(tap_data, state, graph_key)
                if result[0] is not no_update:
                    return result + [node_id]

                # Already-visited node — just refresh highlight
                graph, new_key = _rebuild_graph(state, graph_key, selected_node=node_id)
                return [[graph], no_update, no_update, no_update, no_update, new_key, no_update, no_update, node_id]

        return [no_update] * (_N_GRAPH + 1)

    @app.callback(
        _GRAPH_OUTPUTS + [Output("explanation-length-flag", "data", allow_duplicate=True)],
        Input({"type": "suggested-term", "term": ALL}, "n_clicks"),
        [State({"type": "suggested-term", "term": ALL}, "id"),
         State("app-state-store", "data"),
         State("graph-key", "data"),
         State("explanation-length-flag", "data")],
        prevent_initial_call=True,
    )
    def on_suggestion_click(all_clicks, all_ids, state, graph_key, _length_flag):
        if not ctx.triggered or not all_clicks or not all_ids:
            return [no_update] * (_N_GRAPH + 1)
        clicked_idx = next((i for i, n in enumerate(all_clicks) if n and n > 0), None)
        if clicked_idx is None:
            return [no_update] * (_N_GRAPH + 1)
        term = all_ids[clicked_idx]["term"]
        return _submit_new_concept(term, graph_key, flash=True) + ["short"]


# ---------------------------------------------------------------------------
# Controls: explanation toggle, reload, save
# ---------------------------------------------------------------------------

def _wire_controls(app):

    @app.callback(
        [Output("explanation-length-flag", "data", allow_duplicate=True),
         Output("app-state-store", "data", allow_duplicate=True)],
        Input("toggle-explanation-btn", "n_clicks"),
        [State("explanation-length-flag", "data"),
         State("app-state-store", "data")],
        prevent_initial_call=True,
    )
    def on_toggle_length(n_clicks, current_flag, state):
        if not n_clicks:
            return current_flag, no_update
        new_flag = "long" if current_flag == "short" else "short"
        if not StateManager.has_valid_concept(state):
            return new_flag, no_update
        return new_flag, StateManager.update_explanation_length(state, new_flag)

    @app.callback(
        [Output("reload-triggered", "data", allow_duplicate=True),
         Output("reload-spinning", "data", allow_duplicate=True),
         Output("reload-timer", "disabled", allow_duplicate=True),
         Output("reload-last-click", "data", allow_duplicate=True),
         Output("reload-timer", "n_intervals", allow_duplicate=True)],
        Input("reload-explanation-btn", "n_clicks"),
        State("reload-last-click", "data"),
        prevent_initial_call=True,
    )
    def on_reload_click(n_clicks, last_count):
        if n_clicks and n_clicks > (last_count or 0):
            return True, True, False, 0, 0
        return False, False, True, last_count or 0, no_update

    @app.callback(
        [Output("app-state-store", "data", allow_duplicate=True),
         Output("reload-spinning", "data", allow_duplicate=True),
         Output("reload-triggered", "data", allow_duplicate=True),
         Output("reload-timer", "disabled", allow_duplicate=True),
         Output("reload-explanation-btn", "n_clicks")],
        Input("reload-timer", "n_intervals"),
        [State("app-state-store", "data"),
         State("explanation-length-flag", "data"),
         State("reload-triggered", "data")],
        prevent_initial_call=True,
    )
    def on_reload_timer(n_intervals, state, length_flag, triggered):
        if not triggered or n_intervals < 1:
            return [no_update] * 5
        if not StateManager.has_valid_concept(state):
            return no_update, False, False, True, 0
        return StateManager.reload_explanation(state, length_flag), False, False, True, 0

    @app.callback(
        Output("download-graph", "data"),
        Input("save-btn", "n_clicks"),
        State("app-state-store", "data"),
        prevent_initial_call=True,
    )
    def on_save(n_clicks, state):
        if not n_clicks:
            return no_update
        return {"content": StateManager.export_state_for_download(state), "filename": "shrimps_graph.json"}


# ---------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------

def _wire_animations(app):

    @app.callback(
        Output("submit-btn-flash", "data", allow_duplicate=True),
        [Input("start-input", "n_submit"), Input("submit-btn", "n_clicks")],
        prevent_initial_call=True,
    )
    def on_submit_flash(_n_submit, _n_clicks):
        return True if ctx.triggered else no_update


# ---------------------------------------------------------------------------
# Display: topbar, info box, suggestions, overlay
# ---------------------------------------------------------------------------

def _wire_display(app):

    @app.callback(
        [Output("node-topbar", "style"),
         Output("topbar-node-label", "children"),
         Output("topbar-divider", "style"),
         Output("gen-flashcards-btn", "style"),
         Output("fc-mode-flip-btn", "style"),
         Output("fc-mode-quiz-btn", "style"),
         Output("trim-node-btn", "style"),
         Output("fc-done-btn", "style")],
        [Input("selected-node", "data"),
         Input("app-state-store", "data"),
         Input("trim-mode", "data")],
        prevent_initial_call=True,
    )
    def on_topbar_update(selected_node, state, trim_mode):
        trim_style = _chip({"color": "#ff4444", "borderColor": "rgba(255,80,80,0.7)",
                            "backgroundColor": "rgba(255,80,80,0.25)",
                            "boxShadow": "0 0 10px rgba(255,80,80,0.4)"}) if trim_mode \
                    else _chip({"color": "#ff9a9a", "borderColor": "rgba(255,107,107,0.3)"})

        if not StateManager.has_valid_concept(state):
            return ({**_TOPBAR_BASE, "display": "none"}, "", _DIV_HIDDEN,
                    _CHIP_HIDDEN, _CHIP_HIDDEN, _CHIP_HIDDEN, trim_style, _CHIP_HIDDEN)

        if not selected_node:
            label = "✂️ Trim mode — tap a node" if trim_mode else "← select a node"
            return ({**_TOPBAR_BASE, "display": "flex"}, label, _DIV_HIDDEN,
                    _CHIP_HIDDEN, _CHIP_HIDDEN, _CHIP_HIDDEN, trim_style, _CHIP_HIDDEN)

        has_cards = selected_node in state.get("flashcards", {})
        label = f"📍 {selected_node}"
        gen_s  = _chip({"color": "#ffd166", "borderColor": "rgba(255,209,102,0.3)",
                        "display": "none" if has_cards else "inline-flex"})
        flip_s = _chip({"color": "#ffd166", "borderColor": "rgba(255,209,102,0.3)",
                        "display": "inline-flex" if has_cards else "none"})
        quiz_s = _chip({"color": "#a8dadc", "borderColor": "rgba(168,218,220,0.3)",
                        "display": "inline-flex" if has_cards else "none"})
        done_s = _chip({"color": "#06d6a0", "borderColor": "rgba(6,214,160,0.3)",
                        "display": "inline-flex" if has_cards else "none"})
        return {**_TOPBAR_BASE, "display": "flex"}, label, _DIV_SHOWN, gen_s, flip_s, quiz_s, trim_style, done_s

    @app.callback(
        Output("info-box", "children"),
        [Input("app-state-store", "data"),
         Input("explanation-length-flag", "data"),
         Input("reload-spinning", "data"),
         Input("selected-node", "data")],
        prevent_initial_call="initial_duplicate",
    )
    def on_info_box_update(state, length_flag, spinning, selected_node):
        if not StateManager.has_valid_concept(state):
            return info_box_content(explanation=state.get("explanation_paragraph", ""))
        return info_box_content(
            term=StateManager.get_current_term(state),
            explanation=state.get("explanation_paragraph", ""),
            length_flag=length_flag,
            spinning=spinning,
            selected_node=selected_node,
            state=state,
        )

    @app.callback(
        Output("suggested-concepts-container", "children"),
        Input("app-state-store", "data"),
    )
    def on_suggestions_update(state):
        return suggested_concepts(StateManager.get_suggested_concepts(state))

    @app.callback(
        [Output("centered-input-overlay", "style"),
         Output("submit-btn-flash", "data", allow_duplicate=True)],
        Input("input-overlay-visible", "data"),
        prevent_initial_call=True,
    )
    def on_overlay_toggle(visible):
        if visible:
            return {**_OVERLAY_BASE, "opacity": 1, "pointerEvents": "auto"}, False
        return {**_OVERLAY_BASE, "transform": "translate(-50%, -40%)", "opacity": 0, "pointerEvents": "none"}, False


# ---------------------------------------------------------------------------
# Flashcards and quiz
# ---------------------------------------------------------------------------

def _wire_flashcards(app):

    # ── Generate flashcards for a node ───────────────────────────────────
    @app.callback(
        [Output("app-state-store", "data", allow_duplicate=True),
         Output("selected-node", "data", allow_duplicate=True),
         Output("flashcard-index", "data", allow_duplicate=True),
         Output("flashcard-show-answer", "data", allow_duplicate=True),
         Output("graph-container", "children", allow_duplicate=True),
         Output("graph-key", "data", allow_duplicate=True),
         Output("fc-modal-open", "data")],
        Input("gen-flashcards-btn", "n_clicks"),
        [State("app-state-store", "data"),
         State("selected-node", "data"),
         State("graph-key", "data")],
        prevent_initial_call=True,
    )
    def on_generate_flashcards(n_clicks, state, node, graph_key):
        if not n_clicks or not node:
            return [no_update] * 7
        new_state = StateManager.mark_practiced(StateManager.generate_flashcards(state, node), node)
        graph, new_key = _rebuild_graph(new_state, graph_key, selected_node=node)
        return new_state, node, 0, False, [graph], new_key, True

    # ── Trim mode toggle ─────────────────────────────────────────────────
    @app.callback(
        [Output("trim-mode", "data"),
         Output("trim-node-btn", "children"),
         Output("trim-node-btn", "className"),
         Output("graph-section-wrapper", "className")],
        Input("trim-node-btn", "n_clicks"),
        State("trim-mode", "data"),
        prevent_initial_call=True,
    )
    def on_trim_toggle(n_clicks, trim_mode):
        if not n_clicks:
            return [no_update] * 4
        active = not trim_mode
        return (active,
                "🛑 Stop Trimming" if active else "✂️ Trim",
                "trim-btn-active" if active else "",
                "trim-mode-active" if active else "")

    # ── Flashcard navigation ─────────────────────────────────────────────
    @app.callback(
        [Output("flashcard-index", "data", allow_duplicate=True),
         Output("flashcard-show-answer", "data", allow_duplicate=True)],
        [Input("fc-prev-btn", "n_clicks"),
         Input("fc-next-btn", "n_clicks"),
         Input("fc-flip-btn", "n_clicks")],
        [State("flashcard-index", "data"),
         State("flashcard-show-answer", "data"),
         State("app-state-store", "data"),
         State("selected-node", "data")],
        prevent_initial_call=True,
    )
    def on_card_navigate(_prev, _nxt, _flip, idx, show_ans, state, node):
        prop = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        cards = state.get("flashcards", {}).get(node, [])
        total = len(cards)
        if not total:
            return no_update, no_update
        if "fc-flip-btn" in prop:
            return idx, not show_ans
        if "fc-next-btn" in prop:
            return (idx + 1) % total, False
        if "fc-prev-btn" in prop:
            return (idx - 1) % total, False
        return no_update, no_update

    # ── Flashcard display ────────────────────────────────────────────────
    @app.callback(
        [Output("flashcard-display", "children"),
         Output("fc-counter", "children")],
        [Input("flashcard-index", "data"),
         Input("flashcard-show-answer", "data"),
         Input("app-state-store", "data")],
        State("selected-node", "data"),
        prevent_initial_call=True,
    )
    def on_card_display(idx, show_ans, state, node):
        cards = state.get("flashcards", {}).get(node, [])
        if not cards:
            return "No cards yet.", ""
        card = cards[idx % len(cards)]
        title = card.get("title", "")
        text = card["a"] if show_ans else card["q"]
        side = "Answer" if show_ans else "Question"
        rows = [
            html.Div(title, style={
                "fontSize": "0.75em", "color": "rgba(255,180,80,0.8)", "marginBottom": "6px",
                "fontWeight": "600", "textTransform": "uppercase", "letterSpacing": "0.05em",
            }) if title else None,
            html.Div(text),
        ]
        return [r for r in rows if r is not None], f"{idx % len(cards) + 1} / {len(cards)} — {side}"

    # ── Done button → keep/discard prompt ───────────────────────────────
    @app.callback(
        [Output("fc-keep-confirm", "data"),
         Output("fc-keep-confirm-row", "style"),
         Output("fc-done-btn", "style", allow_duplicate=True)],
        Input("fc-done-btn", "n_clicks"),
        State("selected-node", "data"),
        prevent_initial_call=True,
    )
    def on_done_click(n_clicks, node):
        if not n_clicks or not node:
            return no_update, no_update, no_update
        return (True,
                {"display": "flex", "alignItems": "center", "gap": "6px"},
                _chip({"color": "#06d6a0", "borderColor": "rgba(6,214,160,0.3)", "display": "none"}))

    # ── Keep / discard resolution ────────────────────────────────────────
    @app.callback(
        [Output("app-state-store", "data", allow_duplicate=True),
         Output("graph-container", "children", allow_duplicate=True),
         Output("graph-key", "data", allow_duplicate=True),
         Output("fc-keep-confirm", "data", allow_duplicate=True),
         Output("fc-keep-confirm-row", "style", allow_duplicate=True),
         Output("fc-done-btn", "style", allow_duplicate=True)],
        [Input("fc-keep-btn", "n_clicks"), Input("fc-discard-btn", "n_clicks")],
        [State("app-state-store", "data"),
         State("selected-node", "data"),
         State("graph-key", "data")],
        prevent_initial_call=True,
    )
    def on_keep_or_discard(_keep, _discard, state, node, graph_key):
        if not ctx.triggered or not node:
            return [no_update] * 6
        new_state = StateManager.mark_caught(state, node)
        if "fc-discard-btn" in ctx.triggered[0]["prop_id"]:
            cards = dict(new_state.get("flashcards", {}))
            cards.pop(node, None)
            new_state = {**new_state, "flashcards": cards}
        graph, new_key = _rebuild_graph(new_state, graph_key, selected_node=node)
        return (new_state, [graph], new_key, False,
                {"display": "none", "alignItems": "center", "gap": "6px"},
                _chip({"color": "#06d6a0", "borderColor": "rgba(6,214,160,0.3)", "display": "inline-flex"}))

    # ── Modal visibility ─────────────────────────────────────────────────
    @app.callback(
        Output("fc-modal-open", "data", allow_duplicate=True),
        Input("fc-close-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def on_modal_close(n_clicks):
        return False if n_clicks else no_update

    @app.callback(
        Output("flashcard-modal", "style"),
        Input("fc-modal-open", "data"),
        prevent_initial_call=True,
    )
    def on_modal_visibility(is_open):
        return {**_MODAL_BASE, "display": "flex" if is_open else "none"}

    # ── Flip / quiz mode toggle ──────────────────────────────────────────
    @app.callback(
        [Output("fc-mode", "data"),
         Output("fc-flip-view", "style"),
         Output("fc-quiz-view", "style"),
         Output("fc-modal-open", "data", allow_duplicate=True)],
        [Input("fc-mode-flip-btn", "n_clicks"),
         Input("fc-mode-quiz-btn", "n_clicks")],
        prevent_initial_call=True,
    )
    def on_fc_mode_toggle(_flip, _quiz):
        if "fc-mode-quiz-btn" in (ctx.triggered[0]["prop_id"] if ctx.triggered else ""):
            return "quiz", {"display": "none"}, {"display": "block"}, True
        return "flip", {"display": "block"}, {"display": "none"}, True

    # ── Start quiz for current node ──────────────────────────────────────
    @app.callback(
        _QUIZ_OUTPUTS,
        Input("fc-mode-quiz-btn", "n_clicks"),
        [State("app-state-store", "data"), State("selected-node", "data")],
        prevent_initial_call=True,
    )
    def on_quiz_start(n_clicks, state, node):
        if not n_clicks or not node:
            return [no_update] * _N_QUIZ
        cards = state.get("flashcards", {}).get(node, [])
        if not cards:
            return [None, 0, "Generate flashcards first.", [], "", "", 0, "", False]
        return _run_quiz(node, state, cards)

    # ── Answer a quiz question ───────────────────────────────────────────
    @app.callback(
        [Output("quiz-feedback", "children", allow_duplicate=True),
         Output("quiz-score", "data"),
         Output("quiz-streak", "data"),
         Output("quiz-score-display", "children"),
         Output("quiz-streak-display", "children"),
         Output("quiz-answered", "data")],
        Input({"type": "quiz-option", "index": ALL}, "n_clicks"),
        [State({"type": "quiz-option", "index": ALL}, "children"),
         State("quiz-data", "data"),
         State("quiz-index", "data"),
         State("quiz-score", "data"),
         State("quiz-streak", "data"),
         State("quiz-answered", "data")],
        prevent_initial_call=True,
    )
    def on_quiz_answer(all_clicks, all_labels, quiz, idx, score, streak, already_answered):
        n_out = 6
        if not quiz or not ctx.triggered or already_answered:
            return [no_update] * n_out
        if not any(c for c in all_clicks if c):
            return [no_update] * n_out
        try:
            btn_idx = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["index"]
        except (KeyError, ValueError, json.JSONDecodeError):
            return [no_update] * n_out
        chosen = all_labels[btn_idx]
        correct = quiz[idx % len(quiz)]["answer"]
        if chosen == correct:
            new_streak = streak + 1
            bonus = 5 if new_streak >= 3 else 0
            pts = 10 + bonus
            new_score = score + pts
            streak_msg = f"🔥 {new_streak} streak! +{bonus} bonus" if new_streak >= 3 else ""
            msg = f"✅ +{pts} pts!" + (f"  {streak_msg}" if streak_msg else "")
            return html.Span(msg, style={"color": "#06d6a0", "fontWeight": "600"}), new_score, new_streak, str(new_score), streak_msg, True
        new_score = max(0, score - 5)
        return html.Span(f"❌ -5 pts — correct: {correct}", style={"color": "#ff6b6b", "fontWeight": "600"}), new_score, 0, str(new_score), "", True

    # ── Advance to next quiz question ────────────────────────────────────
    @app.callback(
        [Output("quiz-index", "data", allow_duplicate=True),
         Output("quiz-question", "children", allow_duplicate=True),
         Output("quiz-options", "children", allow_duplicate=True),
         Output("quiz-feedback", "children", allow_duplicate=True),
         Output("quiz-counter", "children", allow_duplicate=True),
         Output("quiz-answered", "data", allow_duplicate=True)],
        Input("quiz-next-btn", "n_clicks"),
        [State("quiz-data", "data"), State("quiz-index", "data")],
        prevent_initial_call=True,
    )
    def on_quiz_next(n_clicks, quiz, idx):
        if not n_clicks or not quiz:
            return [no_update] * 6
        new_idx = (idx + 1) % len(quiz)
        q = quiz[new_idx]
        return new_idx, q["q"], _quiz_option_buttons(q["options"]), "", f"{new_idx + 1} / {len(quiz)}", False

    # ── Saved flashcards panel ───────────────────────────────────────────
    @app.callback(
        Output("fc-all-cards", "children"),
        Input("app-state-store", "data"),
        prevent_initial_call=True,
    )
    def on_all_cards_update(state):
        flashcards = state.get("flashcards", {})
        if not flashcards:
            return html.Div("No saved flashcards yet.",
                            style={"color": "rgba(255,255,255,0.4)", "fontStyle": "italic"})
        sections = []
        for node, cards in flashcards.items():
            rows = []
            for i, card in enumerate(cards):
                card_id = f"{node}||{i}"
                title = card.get("title", "") or card["q"][:35]
                rows.append(html.Div([
                    dcc.Checklist(
                        id={"type": "fc-card-check", "id": card_id},
                        options=[{"label": "", "value": card_id}],
                        value=[card_id],
                        style={"display": "inline-block", "marginRight": "6px"},
                        inputStyle={"accentColor": "#a8dadc", "cursor": "pointer"},
                    ),
                    html.Span(title, style={"color": "rgba(200,230,255,0.85)", "fontSize": "0.82em"}),
                ], style={"display": "flex", "alignItems": "center", "marginBottom": "3px", "paddingLeft": "8px"}))
            sections.append(html.Div([
                html.Div(f"📍 {node}", style={
                    "fontWeight": "700", "color": "rgba(255,180,80,0.95)", "fontSize": "0.85em",
                    "marginTop": "10px", "marginBottom": "4px",
                    "borderBottom": "1px solid rgba(255,180,80,0.2)", "paddingBottom": "3px",
                }),
                *rows,
            ]))
        return sections

    # ── Quiz from selected cards across nodes ────────────────────────────
    @app.callback(
        _QUIZ_OUTPUTS + [Output("fc-flip-view", "style", allow_duplicate=True),
                         Output("fc-quiz-view", "style", allow_duplicate=True)],
        Input("quiz-selected-btn", "n_clicks"),
        [State("app-state-store", "data"),
         State({"type": "fc-card-check", "id": ALL}, "value"),
         State({"type": "fc-card-check", "id": ALL}, "id")],
        prevent_initial_call=True,
    )
    def on_quiz_selected(n_clicks, state, all_values, _all_ids):
        n_out = _N_QUIZ + 2
        if not n_clicks:
            return [no_update] * n_out
        checked = {v for vals in all_values for v in (vals or [])}
        if not checked:
            return [no_update] * n_out
        flashcards = state.get("flashcards", {})
        pool = []
        for card_id in checked:
            parts = card_id.split("||")
            if len(parts) == 2:
                node, idx_str = parts
                try:
                    card_list = flashcards.get(node, [])
                    i = int(idx_str)
                    if i < len(card_list):
                        pool.append(card_list[i])
                except ValueError:
                    pass
        if not pool:
            return [no_update] * n_out
        random.shuffle(pool)
        quiz_result = _run_quiz("selected cards", state, pool)
        if quiz_result[0] is None:
            return [no_update] * n_out
        return quiz_result + [{"display": "none"}, {"display": "block"}]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def attach(app) -> None:
    """Register all Cheeky Shrimps callbacks onto *app*."""
    _wire_reset(app)
    _wire_interactions(app)
    _wire_controls(app)
    _wire_animations(app)
    _wire_display(app)
    _wire_flashcards(app)


# ---------------------------------------------------------------------------
# Backward-compatible shim used by app.py
# ---------------------------------------------------------------------------

class CallbackHandlers:
    """Thin wrapper so app.py can keep ``CallbackHandlers(app)`` unchanged."""

    def __init__(self, app):
        attach(app)
