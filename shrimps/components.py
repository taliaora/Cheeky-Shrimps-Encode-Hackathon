"""Presentation-layer builders for the Cheeky Shrimps interface.

This module assembles reusable Dash components such as:
- header and layout scaffolding
- graph widgets
- controls and overlays
- info/sidebar content
- flashcard and quiz modal UI
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

import dash_cytoscape as cyto
from dash import dcc, html

from shrimps.config import (
    app_title,
    palette,
    ui_styles,
    help_markdown,
    motion_settings,
)

cyto.load_extra_layouts()

# ---------------------------------------------------------------------------
# Theme snapshot
# ---------------------------------------------------------------------------

TITLE_TEXT = app_title()
COLOR_SET = palette()
STYLE_MAP = ui_styles()
GUIDE_MD = help_markdown()
TIMING = motion_settings()


def _icon_map() -> dict[str, str]:
    return {
        "refresh": "↻",
        "details": "📚",
        "send": "↑",
    }


ICONS = _icon_map()


@dataclass(frozen=True)
class ThemeBundle:
    colors: dict[str, Any]
    buttons: dict[str, Any]
    inputs: dict[str, Any]
    layout: dict[str, Any]
    graph: dict[str, Any]
    overlay: dict[str, Any]


THEME = ThemeBundle(
    colors=COLOR_SET,
    buttons=STYLE_MAP["buttons"],
    inputs=STYLE_MAP["inputs"],
    layout=STYLE_MAP["layout"],
    graph=STYLE_MAP["graph"],
    overlay=STYLE_MAP["overlay"],
)

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _merge(*parts: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for part in parts:
        merged.update(part)
    return merged


def _base_button_style() -> dict[str, Any]:
    return _merge(THEME.buttons["common"])


def _toolbar_button_style() -> dict[str, Any]:
    return _merge(THEME.buttons["common"], THEME.buttons["toolbar"])


def _submit_button_style() -> dict[str, Any]:
    return _merge(THEME.buttons["common"], THEME.buttons["submit"])


def _chip_style() -> dict[str, Any]:
    return _merge(THEME.buttons["common"], THEME.buttons["tag"])

# ---------------------------------------------------------------------------
# App shell pieces
# ---------------------------------------------------------------------------

def build_header():
    shrimp_badge = html.Span(
        "🦐",
        style={
            "fontSize": "2.2em",
            "marginRight": "10px",
            "filter": "drop-shadow(0 0 8px rgba(255,160,50,0.7))",
        },
    )
    wordmark = html.Span(
        "Cheeky Shrimps",
        style={
            "fontSize": "2em",
            "fontWeight": "400",
            "fontFamily": "'Fredoka One', 'Bubblegum Sans', cursive",
            "color": "#ff8c35",
            "letterSpacing": "0.02em",
            "textShadow": "0 2px 12px rgba(255,100,0,0.4)",
        },
    )
    subtitle = html.Span(
        "  learn anything",
        style={
            "fontSize": "1em",
            "color": "#ffffff",
            "marginLeft": "14px",
            "fontWeight": "400",
            "fontFamily": "'Inter', sans-serif",
            "opacity": "0.9",
        },
    )
    return html.Div(
        [shrimp_badge, wordmark, subtitle],
        style={
            "display": "flex",
            "alignItems": "center",
            "paddingTop": "20px",
            "paddingBottom": "16px",
            "borderBottom": "1px solid rgba(255,255,255,0.15)",
            "marginBottom": "20px",
        },
    )


def build_state_stores(initial_state: dict[str, Any]) -> list:
    store_defaults = [
        ("app-state-store", initial_state),
        ("input-overlay-visible", True),
        ("graph-key", 0),
        ("input-flash", False),
        ("node-flash", None),
        ("submit-btn-flash", False),
        ("explanation-length-flag", "short"),
        ("toggle-animating", False),
        ("reload-spinning", False),
        ("reload-triggered", False),
        ("reload-last-click", 0),
        ("selected-node", None),
        ("flashcard-index", 0),
        ("flashcard-show-answer", False),
        ("fc-mode", "flip"),
        ("quiz-index", 0),
        ("quiz-data", None),
        ("fc-modal-open", False),
        ("quiz-score", 0),
        ("quiz-streak", 0),
        ("quiz-answered", False),
        ("fc-keep-confirm", False),
        ("trim-mode", False),
        ("quiz-selected-cards", []),
        ("quiz-session-complete", False),
        ("node-count", 4),
    ]
    stores = [dcc.Store(id=store_id, data=value) for store_id, value in store_defaults]
    return stores


def build_timers() -> list:
    return [
        dcc.Interval(
            id="reload-timer",
            interval=TIMING["reload_timer_interval"],
            n_intervals=0,
            disabled=True,
            max_intervals=1,
        ),
        dcc.Interval(
            id="suggestions-timer",
            interval=300,   # fire 300 ms after being armed
            n_intervals=0,
            disabled=True,
            max_intervals=1,
        ),
    ]

# ---------------------------------------------------------------------------
# Buttons and inputs
# ---------------------------------------------------------------------------

def build_length_toggle(current_mode: str = "short"):
    highlight = COLOR_SET["accent_green"] if current_mode == "long" else "transparent"
    return html.Button(
        ICONS["details"],
        id="toggle-explanation-btn",
        title="Toggle short/long explanation",
        className="toggle-btn",
        style={
            **_base_button_style(),
            "background": "none",
            "color": COLOR_SET["text_primary"],
            "fontSize": "2.1em",
            "verticalAlign": "middle",
            "float": "right",
            "marginLeft": "auto",
            "minWidth": "1.5em",
            "height": "1.5em",
            "borderRadius": "0.75em",
            "transition": "all 0.2s ease",
            "border": f"2px solid {highlight}",
            "boxSizing": "border-box",
            "padding": "0",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
        },
    )


def build_reload_button(spinning: bool = False):
    return html.Button(
        ICONS["refresh"],
        id="reload-explanation-btn",
        title="Reload explanation",
        n_clicks=0,
        className=f"reload-btn {'spin-animation' if spinning else ''}".strip(),
        style={
            **_base_button_style(),
            "background": "none",
            "color": COLOR_SET["text_primary"],
            "fontSize": "2.1em",
            "padding": "0",
            "verticalAlign": "middle",
            "minWidth": "1.5em",
            "height": "1.5em",
            "transition": "transform 0.2s",
            "transformOrigin": "center",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "flex": "0 0 auto",
        },
    )


def build_submit_button(glow: bool = False):
    style = {
        **_submit_button_style(),
        "width": "2.2rem",
        "height": "2.2rem",
        "right": "0.4rem",
        "fontSize": "1.25rem",
        "transition": (
            f"box-shadow {TIMING['submit_flash_duration'] / 1000}s, "
            f"background {TIMING['submit_flash_duration'] / 1000}s, "
            f"color {TIMING['submit_flash_duration'] / 1000}s"
        ),
    }
    if glow:
        style.update({
            "backgroundColor": "#fff",
            "color": COLOR_SET["accent_green"],
            "boxShadow": "0 0 1.5rem 0.5rem #f0fff0",
        })
    return html.Button(
        ICONS["send"],
        id="submit-btn",
        n_clicks=0,
        className="submit-btn",
        style=style,
    )


def build_text_input():
    return dcc.Input(
        id="start-input",
        type="text",
        placeholder="Enter root concept...",
        debounce=True,
        n_submit=0,
        style={
            **THEME.inputs["search"],
            "width": "100%",
            "fontSize": "1.4rem",
            "padding": "1.2rem 2.8rem 1.2rem 1.75rem",
            "height": "4.8rem",
        },
    )


def build_standard_button(label: str, component_id: str, *, n_clicks: int = 0):
    return html.Button(
        label,
        id=component_id,
        n_clicks=n_clicks,
        style=_toolbar_button_style(),
    )


def build_suggestion_button(term: str):
    return html.Button(
        term,
        id={"type": "suggested-term", "term": term},
        n_clicks=0,
        style=_merge(_chip_style(), {"transition": "background 0.2s, color 0.2s"}),
    )

# ---------------------------------------------------------------------------
# Graph widgets
# ---------------------------------------------------------------------------

def build_plotly_graph(figure, graph_key: int):
    return dcc.Graph(
        id={"type": "graph", "key": graph_key},
        figure=figure,
        relayoutData=None,
        style=THEME.graph["frame"],
        config=THEME.graph["plotly"],
    )


def build_cytoscape_graph(elements, graph_key: int):
    from shrimps.graph_layout_cytoscape import CYTOSCAPE_STYLESHEET
    return cyto.Cytoscape(
        id={"type": "cyto-graph", "key": graph_key},
        elements=elements,
        stylesheet=CYTOSCAPE_STYLESHEET,
        layout={"name": "preset"},
        style={
            "width": "100%",
            "height": "720px",
            "backgroundColor": "transparent",
        },
        userZoomingEnabled=True,
        userPanningEnabled=True,
        autoungrabify=False,
        minZoom=0.3,
        maxZoom=3.0,
    )

# ---------------------------------------------------------------------------
# Info and sidebar content
# ---------------------------------------------------------------------------

def build_info_content(
    term: Optional[str] = None,
    explanation: str = "",
    detail_mode: str = "short",
    spinning: bool = False,
    selected_node: Optional[str] = None,
    state: Optional[dict[str, Any]] = None,
):
    del selected_node, state  # present for compatibility with existing call sites
    if term is None:
        return [
            html.H4(
                "Time to upgrade your shrimp intelligence.",
                style={"color": COLOR_SET["text_primary"]},
            ),
            dcc.Markdown(explanation or GUIDE_MD),
        ]
    header_row = html.Div(
        [
            html.Div(build_reload_button(spinning=spinning), style={"flex": "1"}),
            html.H4(
                f"About {term}",
                id="about-term-heading",
                style={
                    "color": COLOR_SET["text_primary"],
                    "margin": 0,
                    "fontWeight": 700,
                    "fontSize": "1.2em",
                    "flex": "2",
                    "textAlign": "center",
                    "minWidth": "8em",
                },
            ),
            html.Div(
                build_length_toggle(detail_mode),
                style={"flex": "1", "display": "flex", "justifyContent": "flex-end"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "marginBottom": "1rem",
            "width": "100%",
            "gap": "1rem",
        },
    )
    return [header_row, dcc.Markdown(explanation)]


def build_suggestions_section(suggestions: Optional[Iterable[str]] = None):
    if not suggestions:
        return ""
    chips = html.Div(
        [build_suggestion_button(term) for term in suggestions],
        style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center"},
    )
    return html.Div(
        [
            html.Div(
                "You could now explore:",
                style={
                    "color": COLOR_SET["text_primary"],
                    "fontSize": "1.30em",
                    "marginBottom": "10px",
                },
            ),
            chips,
        ],
        style={"position": "relative", "paddingBottom": "10px"},
    )


def build_info_panel(children):
    return html.Div(
        id="info-box",
        children=children,
        style=THEME.layout["glass_card"],
    )


def build_weakness_panel():
    """Weakness-tracking agent panel shown below the info box."""
    card_style = {**THEME.layout["glass_card"], "marginTop": "16px", "width": "350px", "maxWidth": "350px", "minWidth": "350px"}
    btn_style = _merge(_toolbar_button_style(), {"width": "100%", "marginTop": "8px", "textAlign": "center"})
    divider = {"borderTop": "1px solid rgba(255,255,255,0.1)", "margin": "14px 0"}
    return html.Div([
        # Header with wrong count
        html.Div([
            html.Span("🎯 Weak Spots", style={"fontWeight": "700", "fontSize": "0.95em"}),
            html.Span([
                html.Span(" · ", style={"color": "rgba(255,255,255,0.3)"}),
                html.Span(id="weakness-wrong-count", children="0",
                          style={"color": "#ff6b6b", "fontWeight": "700"}),
                html.Span(" wrong", style={"color": "rgba(255,255,255,0.5)", "fontSize": "0.82em"}),
            ]),
        ], style={"display": "flex", "alignItems": "center", "gap": "4px", "marginBottom": "10px"}),

        # SRS due nodes
        html.Div(id="srs-due-panel", style={"marginBottom": "8px"}),

        # Proactive post-quiz summary (auto-populated)
        html.Div(id="post-quiz-summary", style={"marginBottom": "4px"}),

        # Analyse mistakes
        html.Button("Analyse my mistakes", id="weakness-analyse-btn", n_clicks=0, style=btn_style),
        html.Div("⏳ Analysing...", id="weakness-report-loading", style={"display": "none"}),
        html.Div(id="weakness-report", style={"marginTop": "10px", "color": "rgba(255,255,255,0.85)"}),

        # Divider
        html.Hr(style=divider),

        # Resource recommender
        html.Div("📚 Resources", style={"fontWeight": "700", "fontSize": "0.9em", "marginBottom": "8px"}),
        html.Button("Find resources for my gaps", id="resources-btn", n_clicks=0, style=btn_style),
        html.Div("⏳ Finding resources...", id="resources-loading", style={"display": "none"}),
        html.Div(id="resources-list", style={"marginTop": "10px"}),
    ], style=card_style)


def build_sidebar(control_block, info_block):
    return html.Div(
        [control_block, info_block, build_weakness_panel()],
        style=THEME.layout["side_column"],
    )

# ---------------------------------------------------------------------------
# Overlays and graph area
# ---------------------------------------------------------------------------

def build_center_input_overlay():
    slider = html.Div(
        [
            html.Div(
                [
                    html.Span("Nodes per click:", style={
                        "color": "rgba(255,255,255,0.6)", "fontSize": "0.78em",
                        "whiteSpace": "nowrap",
                    }),
                    html.Span(id="node-count-label", children="4", style={
                        "color": "#ff8c35", "fontWeight": "700", "fontSize": "0.85em",
                        "minWidth": "1.2em", "textAlign": "center",
                    }),
                ],
                style={"display": "flex", "justifyContent": "space-between",
                       "alignItems": "center", "marginBottom": "4px"},
            ),
            dcc.Slider(
                id="node-count-slider",
                min=2, max=8, step=1, value=4,
                marks={i: str(i) for i in range(2, 9)},
                tooltip={"always_visible": False},
                updatemode="drag",
            ),
        ],
        style={"width": "100%", "marginTop": "12px", "padding": "0 4px"},
    )
    inner = html.Div(
        [build_text_input(), build_submit_button(), slider],
        style={**THEME.overlay["center_prompt_inner"], "flexDirection": "column", "alignItems": "stretch"},
    )
    return html.Div(
        inner,
        id="centered-input-overlay",
        style=THEME.overlay["center_prompt"],
    )


def build_control_strip():
    return html.Div(
        [
            build_standard_button("Reset", "reset-term-btn"),
            build_standard_button("Save", "save-btn"),
            dcc.Download(id="download-graph"),
            dcc.Upload(
                id="upload-graph",
                children=build_standard_button("Load", "upload-load-btn"),
                multiple=False,
            ),
            dcc.Upload(
                id="upload-document",
                children=build_standard_button("📄 Doc", "upload-doc-btn"),
                multiple=False,
                accept=".txt,.md,.pdf",
            ),
        ],
        style={
            "marginBottom": "16px",
            "display": "flex",
            "gap": "10px",
            "justifyContent": "center",
            "flexWrap": "wrap",
        },
    )


def build_graph_region(graph_widget):
    return html.Div(
        [
            html.Div(id="graph-container", children=[graph_widget]),
            html.Div(
                id="suggested-concepts-container",
                style={
                    "marginTop": "24px",
                    "marginBottom": "24px",
                    "textAlign": "center",
                    "padding": "0 16px",
                },
            ),
            build_center_input_overlay(),
        ],
        id="graph-section-wrapper",
        style=THEME.layout["map_panel"],
    )

# ---------------------------------------------------------------------------
# Flashcards and quiz modal
# ---------------------------------------------------------------------------

def build_flashcard_modal():
    compact_btn = _merge(_toolbar_button_style(), {"padding": "5px 12px", "fontSize": "0.82em"})

    close_button = html.Button(
        "✕",
        id="fc-close-btn",
        n_clicks=0,
        style={
            **_base_button_style(),
            "background": "none",
            "color": COLOR_SET["text_secondary"],
            "fontSize": "1.2em",
            "padding": "0 4px",
            "lineHeight": "1",
        },
    )
    modal_header = html.Div(
        [
            html.Div(
                id="fc-node-header",
                children=[],
                style={"fontWeight": "700", "fontSize": "1em", "color": "rgba(255,180,80,0.9)"},
            ),
            close_button,
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "marginBottom": "14px",
        },
    )
    flip_view = html.Div(
        id="fc-flip-view",
        children=[
            html.Div(
                id="flashcard-display",
                children="Generating flashcards...",
                style={
                    "backgroundColor": "rgba(0,40,60,0.7)",
                    "borderRadius": "10px",
                    "padding": "20px",
                    "minHeight": "110px",
                    "color": COLOR_SET["text_primary"],
                    "fontSize": "0.95em",
                    "marginBottom": "12px",
                    "border": "1px solid rgba(0,180,160,0.2)",
                    "lineHeight": "1.6",
                    "cursor": "pointer",
                },
            ),
            html.Div(
                [
                    html.Button("◀", id="fc-prev-btn", n_clicks=0, style={**compact_btn, "padding": "6px 16px", "fontSize": "1em"}),
                    html.Button("Flip ↕", id="fc-flip-btn", n_clicks=0, style={**compact_btn, "padding": "6px 20px", "fontSize": "0.9em"}),
                    html.Button("▶", id="fc-next-btn", n_clicks=0, style={**compact_btn, "padding": "6px 16px", "fontSize": "1em"}),
                ],
                style={"display": "flex", "gap": "8px", "justifyContent": "center"},
            ),
            html.Div(
                id="fc-counter",
                style={
                    "color": COLOR_SET["text_secondary"],
                    "fontSize": "0.78em",
                    "marginTop": "8px",
                    "textAlign": "center",
                },
            ),
        ],
    )
    quiz_view = html.Div(
        id="fc-quiz-view",
        style={"display": "none"},
        children=[
            html.Div(id="quiz-streak-display", children="", style={"fontSize": "0.85em", "color": "#06d6a0", "marginBottom": "8px", "minHeight": "20px"}),
            html.Div(id="quiz-question", style={"backgroundColor": "rgba(0,40,60,0.7)", "borderRadius": "10px", "padding": "16px", "color": COLOR_SET["text_primary"], "fontSize": "0.95em", "marginBottom": "12px", "border": "1px solid rgba(168,218,220,0.2)", "lineHeight": "1.6"}),
            html.Div(id="quiz-options", children=[]),
            html.Div(id="quiz-feedback", style={"fontSize": "0.88em", "marginTop": "8px", "minHeight": "22px", "textAlign": "center"}),
            html.Button("Next ▶", id="quiz-next-btn", n_clicks=0, style={**compact_btn, "marginTop": "10px"}),
            html.Div(id="quiz-counter", style={"color": COLOR_SET["text_secondary"], "fontSize": "0.78em", "marginTop": "6px", "textAlign": "center"}),
        ],
    )
    saved_cards_section = [
        html.Hr(style={"borderColor": "rgba(0,180,160,0.12)", "margin": "16px 0"}),
        html.Div(
            [
                html.Span("📚 Saved flashcards", style={"color": COLOR_SET["text_secondary"], "fontSize": "0.78em", "fontWeight": "600"}),
                html.Button(
                    "🧠 Quiz selected",
                    id="quiz-selected-btn",
                    n_clicks=0,
                    style={**compact_btn, "color": "#a8dadc", "borderColor": "rgba(168,218,220,0.3)", "fontSize": "0.75em", "padding": "3px 10px", "marginLeft": "10px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "marginBottom": "8px"},
        ),
        html.Div(
            id="fc-all-cards",
            children=[],
            style={"maxHeight": "220px", "overflowY": "auto", "fontSize": "0.78em", "color": COLOR_SET["text_secondary"]},
        ),
    ]
    card_shell = html.Div(
        [modal_header, flip_view, quiz_view, *saved_cards_section],
        style={
            "backgroundColor": "rgba(2,18,30,0.97)",
            "backdropFilter": "blur(24px)",
            "WebkitBackdropFilter": "blur(24px)",
            "border": "1px solid rgba(255,180,80,0.25)",
            "borderRadius": "18px",
            "padding": "24px",
            "width": "520px",
            "maxWidth": "92vw",
            "maxHeight": "85vh",
            "overflowY": "auto",
            "boxShadow": "0 16px 64px rgba(0,0,0,0.8)",
            "position": "relative",
        },
    )
    return html.Div(
        [card_shell],
        id="flashcard-modal",
        style={
            "display": "none",
            "position": "fixed",
            "top": 0,
            "left": 0,
            "width": "100vw",
            "height": "100vh",
            "backgroundColor": "rgba(0,0,0,0.6)",
            "zIndex": 1000,
            "alignItems": "center",
            "justifyContent": "center",
        },
    )

# ---------------------------------------------------------------------------
# Node top bar
# ---------------------------------------------------------------------------

def build_node_toolbar():
    chip = _merge(_toolbar_button_style(), {"fontSize": "0.82em", "padding": "5px 13px"})
    return html.Div(
        [
            html.Button("✂️ Trim", id="trim-node-btn", n_clicks=0, style={**chip, "color": "#ff9a9a", "borderColor": "rgba(255,107,107,0.3)"}),
            html.Span("│", id="topbar-divider", style={"color": "rgba(255,255,255,0.2)", "margin": "0 8px", "display": "none"}),
            html.Span(id="topbar-node-label", children="", style={"color": "#ffffff", "fontWeight": "600", "fontSize": "1em", "fontFamily": "'Inter', sans-serif", "whiteSpace": "nowrap"}),
            html.Button("📇 Generate Flashcards", id="gen-flashcards-btn", n_clicks=0, style={**chip, "color": "#ffd166", "borderColor": "rgba(255,209,102,0.3)", "display": "none"}),
            html.Button("📇 Flip", id="fc-mode-flip-btn", n_clicks=0, style={**chip, "color": "#ffd166", "borderColor": "rgba(255,209,102,0.3)", "display": "none"}),
            html.Button("🧠 Quiz", id="fc-mode-quiz-btn", n_clicks=0, style={**chip, "color": "#a8dadc", "borderColor": "rgba(168,218,220,0.3)", "display": "none"}),
            html.Button("🎣 Done!", id="fc-done-btn", n_clicks=0, style={**chip, "color": "#06d6a0", "borderColor": "rgba(6,214,160,0.3)", "display": "none"}),
            html.Div(
                id="fc-keep-confirm-row",
                children=[
                    html.Span("Keep flashcards?", style={"color": "#ffffff", "fontSize": "0.85em", "marginRight": "8px"}),
                    html.Button("✅ Keep", id="fc-keep-btn", n_clicks=0, style={**chip, "color": "#06d6a0", "borderColor": "rgba(6,214,160,0.3)"}),
                    html.Button("🗑 Discard", id="fc-discard-btn", n_clicks=0, style={**chip, "color": "#ff9a9a", "borderColor": "rgba(255,107,107,0.3)"}),
                ],
                style={"display": "none", "alignItems": "center", "gap": "6px"},
            ),
            html.Div(style={"flex": "1"}),
            html.Div(
                [
                    html.Span("⭐ ", style={"fontSize": "1em"}),
                    html.Span(id="quiz-score-display", children="0", style={"color": "#ffd166", "fontWeight": "700", "fontSize": "1.05em"}),
                    html.Span(" pts", style={"color": "rgba(255,255,255,0.5)", "fontSize": "0.8em", "marginLeft": "2px"}),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "2px", "backgroundColor": "rgba(0,0,0,0.25)", "borderRadius": "20px", "padding": "4px 12px", "border": "1px solid rgba(255,209,102,0.2)"},
            ),
        ],
        id="node-topbar",
        style={"display": "none", "alignItems": "center", "gap": "6px", "flexWrap": "wrap", "paddingBottom": "12px", "marginBottom": "12px", "borderBottom": "1px solid rgba(255,255,255,0.1)"},
    )

# ---------------------------------------------------------------------------
# Final page assembly
# ---------------------------------------------------------------------------

def build_doc_toast():
    """Floating notification shown while a document is being processed."""
    return html.Div(
        [
            html.Span("⏳", style={"fontSize": "1.2em", "marginRight": "10px"}),
            html.Span("Analysing document and building graph…", style={"fontWeight": "500"}),
        ],
        id="doc-processing-toast",
        style={
            "display": "none",
            "position": "fixed",
            "bottom": "32px",
            "left": "50%",
            "transform": "translateX(-50%)",
            "backgroundColor": "rgba(0,40,60,0.92)",
            "backdropFilter": "blur(12px)",
            "border": "1px solid rgba(0,180,160,0.4)",
            "borderRadius": "40px",
            "padding": "12px 28px",
            "color": "#ffffff",
            "fontSize": "0.95em",
            "zIndex": 2000,
            "boxShadow": "0 8px 32px rgba(0,0,0,0.5)",
            "alignItems": "center",
            "whiteSpace": "nowrap",
        },
    )


def build_main_layout(graph_region, sidebar_region):
    return html.Div(
        [
            build_header(),
            build_node_toolbar(),
            html.Div(id="loading-output", style={"display": "none"}),
            html.Div([graph_region, sidebar_region], style=THEME.layout["content"]),
            build_flashcard_modal(),
            build_doc_toast(),
        ],
        style=THEME.layout["page"],
    )

# ---------------------------------------------------------------------------
# Backward-compatible aliases (used by app.py and callback_handlers.py)
# ---------------------------------------------------------------------------

def header():
    return build_header()

def data_stores(initial_state):
    return build_state_stores(initial_state)

def timers():
    return build_timers()

def toggle_btn(length_flag="short"):
    return build_length_toggle(length_flag)

def reload_btn(spinning=False):
    return build_reload_button(spinning)

def submit_btn(flash=False):
    return build_submit_button(flash)

def control_btn(text, button_id, n_clicks=0):
    return html.Button(text, id=button_id, n_clicks=n_clicks, style=_toolbar_button_style())

def suggestion_chip(term):
    return build_suggestion_button(term)

def input_field():
    return build_text_input()

def plotly_graph(figure, graph_key):
    return build_plotly_graph(figure, graph_key)

def cytoscape_graph(elements, graph_key):
    return build_cytoscape_graph(elements, graph_key)

def flashcard_modal():
    return build_flashcard_modal()

def flashcard_panel():
    return build_flashcard_modal()

def node_action_panel(node, state):
    del node, state
    return []

def sidebar(control_block, info_block):
    return build_sidebar(control_block, info_block)

def info_box_content(term=None, explanation="", length_flag="short", spinning=False, selected_node=None, state=None):
    return build_info_content(term, explanation, length_flag, spinning, selected_node, state)

def suggested_concepts(suggestions=None):
    return build_suggestions_section(suggestions)

def input_overlay():
    return build_center_input_overlay()

def control_panel():
    return build_control_strip()

def info_box(content):
    return build_info_panel(content)

def graph_container(graph_component):
    return build_graph_region(graph_component)

def node_topbar():
    return build_node_toolbar()

def main_layout(graph_region, sidebar_region):
    return build_main_layout(graph_region, sidebar_region)
