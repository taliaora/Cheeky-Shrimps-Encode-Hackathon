# Cheeky Shrimps — Documentation

Cheeky Shrimps is an AI-powered interactive learning app that builds personalised knowledge graphs, generates flashcards and quizzes, tracks your weak spots, and recommends online resources — all driven by a Groq LLM backend.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Architecture Overview](#architecture-overview)
4. [Configuration](#configuration)
5. [Modules](#modules)
   - [app.py](#apppy)
   - [state_manager.py](#state_managerpy)
   - [callback_handlers.py](#callback_handlerspy)
   - [components.py](#componentspy)
   - [llm_client.py](#llm_clientpy)
   - [prompts.py](#promptspy)
   - [graph_layout_cytoscape.py](#graph_layout_cytoscapepy)
   - [graph_layout.py](#graph_layoutpy)
   - [config.py](#configpy)
6. [Features](#features)
7. [Environment Variables](#environment-variables)
8. [Running the App](#running-the-app)

---

## Getting Started

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com/)
- Conda (recommended) or any Python virtual environment

### Installation

```bash
# Clone the repo
git clone https://github.com/your-org/Cheeky-Shrimps-Encode-Hackathon
cd Cheeky-Shrimps-Encode-Hackathon

# Create and activate the environment
conda create -n cheeky-shrimps python=3.11
conda activate cheeky-shrimps

# Install dependencies
pip install -r requirements.txt
```

### Environment setup

Create a `.env` file in the project root (UTF-8 encoded):

```
GROQ_API_KEY=your_key_here
```

Optional overrides:

```
GROQ_MODEL=llama-3.1-8b-instant
GROQ_STRONG_MODEL=llama-3.3-70b-versatile
PORT=8050
```

### Running

```bash
python -m shrimps.app
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

---

## Project Structure

```
Cheeky-Shrimps-Encode-Hackathon/
├── shrimps/
│   ├── app.py                    # Dash app entry point
│   ├── state_manager.py          # All state transitions and LLM orchestration
│   ├── callback_handlers.py      # Dash callback wiring
│   ├── components.py             # UI component builders
│   ├── llm_client.py             # Groq API wrapper
│   ├── prompts.py                # Prompt builders and response parsers
│   ├── graph_layout_cytoscape.py # Cytoscape element builder + stylesheet
│   ├── graph_layout.py           # Force-directed position logic
│   └── config.py                 # Settings, theme, and style constants
├── .env                          # API keys (not committed)
├── shrimps_session.json          # Persisted quiz history and SRS schedule
├── requirements.txt
└── pyproject.toml
```

---

## Architecture Overview

```
Browser
  │
  ▼
Dash (callback_handlers.py)
  │
  ├── UI events (clicks, uploads, button presses)
  │
  ▼
State transitions (state_manager.py)
  │
  ├── LLM calls (llm_client.py → Groq API)
  │     └── Prompts built by prompts.py
  │
  ├── Graph layout (graph_layout.py → graph_layout_cytoscape.py)
  │
  └── Persistence (shrimps_session.json)
```

State is a plain JSON-serialisable dict stored in a `dcc.Store`. Every transition is a pure function — nothing is mutated in place. The UI is rebuilt from state on each callback.

---

## Configuration

All tuneable values live in `shrimps/config.py` under the `SETTINGS` dict.

| Key | Default | Description |
|-----|---------|-------------|
| `app.port` | `8050` | HTTP port |
| `llm.initial_branch_count` | `4` | Nodes generated for the root concept |
| `llm.expansion_branch_count` | `3` | Nodes generated per click expansion |
| `llm.recommendation_count` | `4` | Suggested next concepts shown |
| `llm.retry_seconds` | `1.0` | Delay between LLM retry attempts |
| `learning_map.spacing` | `5.0` | Base spacing between graph nodes |
| `learning_map.radius_limit` | `10.0` | Max graph radius before rescaling |
| `motion.poll_interval_ms` | `500` | Explanation reload timer interval |

The node count can also be changed at runtime using the slider on the start screen (range 2–8).

---

## Modules

### app.py

Entry point. Creates the Dash app, assembles the layout, registers all callbacks, and exposes a WSGI `server` object for deployment.

Key functions:

| Function | Description |
|----------|-------------|
| `create_dash_app()` | Instantiates and configures the Dash app |
| `compose_layout()` | Builds the full component tree from initial state |
| `create_application()` | Combines app creation, layout, and callback registration |
| `main()` | Starts the development server |

---

### state_manager.py

The core of the application. All business logic lives here as pure functions operating on a state dict.

#### State shape

```python
{
    "node_data": {
        "start": {"parent": None, "distance": 0.0, "label": "root term"},
        "concept_name": {
            "parent": "start",
            "distance": 0.6,
            "breadth": 0.8,
            ...
        }
    },
    "clicked_nodes_list": [...],
    "unclicked_nodes": [...],
    "explanation_paragraph": "...",
    "last_clicked": "start",
    "flashcards": {"concept": [{"title": "", "q": "", "a": ""}]},
    "practiced_nodes": [...],
    "caught_nodes": [...],
    "quiz_history": [
        {
            "node": "concept",
            "question": "...",
            "correct_answer": "...",
            "chosen": "...",
            "was_correct": True,
            "ts": 1234567890.0
        }
    ],
    "srs_schedule": {
        "concept": {"interval": 6, "ease": 2.5, "reps": 2, "due_ts": 1234567890.0}
    }
}
```

#### Key functions

| Function | Description |
|----------|-------------|
| `blank_state()` | Returns the default empty state |
| `new_concept_map(term, length_mode, node_count)` | Builds a fresh graph for a root term |
| `new_concept_map_from_text(document_text)` | Builds a graph from uploaded document text |
| `expand_node(state, node, node_count)` | Expands a clicked node with new child concepts |
| `refresh_explanation(state, length_mode)` | Regenerates the explanation text |
| `add_flashcards(state, node)` | Generates and stores flashcards for a node |
| `record_quiz_answer(state, node, ...)` | Logs a quiz answer and updates SRS schedule |
| `get_weakness_report(state)` | LLM analysis of wrong answers |
| `get_resource_recommendations(state)` | LLM-generated online resource suggestions |
| `get_srs_due_nodes(state)` | Returns nodes due for spaced repetition review |
| `get_node_quiz_stats(state)` | Per-node correct/wrong counts for graph colouring |
| `save_session(state)` | Persists quiz history and SRS to disk |
| `load_session()` | Loads persisted data from disk |
| `from_upload(contents)` | Deserialises state from a Dash upload payload |
| `to_download(state)` | Serialises state to JSON for file download |

#### StateManager class

A thin backward-compatible shim that wraps all module-level functions as static methods. Used by `callback_handlers.py`.

---

### callback_handlers.py

Registers all Dash callbacks onto the app. Organised into groups:

| Group | Description |
|-------|-------------|
| `_wire_reset` | Reset button — clears all state and wipes session |
| `_wire_interactions` | Node taps, text submit, file uploads, suggestion clicks |
| `_wire_controls` | Explanation toggle, reload, save/download |
| `_wire_animations` | Submit button flash |
| `_wire_display` | Topbar, info box, suggestions, overlay visibility |
| `_wire_flashcards` | Flashcard generation, navigation, quiz, modal |
| `_wire_quiz_agents` | Weakness report, resource recommendations, post-quiz summary |

All graph-modifying callbacks share a common 8-output signature (`_GRAPH_OUTPUTS`) to keep the pattern consistent.

---

### components.py

Pure UI builders — no business logic. Returns Dash component trees.

Key builders:

| Function | Description |
|----------|-------------|
| `build_state_stores(initial_state)` | All `dcc.Store` components |
| `build_timers()` | `dcc.Interval` components for async operations |
| `build_center_input_overlay()` | Search box, submit button, and node-count slider |
| `build_control_strip()` | Reset / Save / Load / Doc upload buttons |
| `build_weakness_panel()` | Weak Spots sidebar card with analyse and resources buttons |
| `build_flashcard_modal()` | Full flashcard + quiz modal |
| `build_node_toolbar()` | Per-node action bar (trim, generate, quiz, done) |
| `build_doc_toast()` | Floating "analysing document" notification |
| `build_main_layout(graph, sidebar)` | Top-level page assembly |

---

### llm_client.py

Thin wrapper around the Groq Python SDK.

```python
generate_text(prompt: str, strong: bool = False, max_tokens: int | None = None) -> str
```

- `strong=False` uses `llama-3.1-8b-instant` — fast, used for graph expansion and flashcards
- `strong=True` uses `llama-3.3-70b-versatile` — higher quality, used for explanations, weakness reports, and resource recommendations
- `max_tokens` defaults to `256` (fast model) or `1024` (strong model) if not specified

Models can be overridden via `GROQ_MODEL` and `GROQ_STRONG_MODEL` environment variables.

---

### prompts.py

All prompt construction and response parsing.

#### Prompt builders

| Function | Model | Description |
|----------|-------|-------------|
| `build_concept_graph_prompt(concept, count)` | fast | Initial graph nodes for a root term |
| `expand_concept_graph_prompt(concept, excluded, included, count)` | fast | Expansion nodes for a clicked node |
| `explain_concept_concise(concept, excluded, included)` | strong | Short personalised explanation |
| `explain_concept_detailed(concept, excluded, included)` | strong | Long personalised explanation |
| `suggest_next_concepts(included, excluded)` | fast | Next concept suggestions |
| `build_flashcard_prompt(concept, root_term)` | fast | 4 flashcards for a concept |
| `build_quiz_prompt(concept, root_term, cards)` | fast | Wrong answer distractors for quiz |
| `build_weakness_report_prompt(wrong_answers)` | strong | Diagnosis of knowledge gaps |
| `build_resource_recommendations_prompt(wrong_answers)` | strong | Online resource suggestions |
| `build_concept_graph_from_text_prompt(document_text)` | strong | Graph from uploaded document |

#### Parsers

| Function | Description |
|----------|-------------|
| `parse_terms(response, max_terms)` | Parses `concept,distance,breadth,...` CSV into a dict |
| `parse_flashcards(response)` | Parses `Title\|Q\|A\|\|...` into `[{title, q, a}]` |
| `parse_quiz_options(response, cards)` | Merges wrong options with correct answers |
| `parse_resource_recommendations(response)` | Parses `type\|query\|reason` lines |
| `parse_concept_graph_from_text(response)` | Extracts root concept and concept list from document response |

---

### graph_layout_cytoscape.py

Converts the `node_data` dict into Cytoscape.js elements with coral reef styling.

#### `build_cytoscape_elements(...)`

```python
build_cytoscape_elements(
    node_data,
    clicked_nodes_list,
    last_clicked="start",
    node_flash=None,
    practiced=None,
    caught=None,
    flashcards=None,
    selected_node=None,
    quiz_stats=None,
    srs_due=None,
) -> list[dict]
```

Returns a list of Cytoscape element dicts (nodes + edges). Node appearance is determined by its state:

| CSS class | Appearance | Meaning |
|-----------|------------|---------|
| `reef-root` | Orange glowing brain | Root concept |
| `reef-unvisited` | Pink anemone | Not yet clicked |
| `reef-visited` | Purple sponge | Clicked, expanded |
| `reef-active` | Orange coral branch | Most recently clicked |
| `reef-selected` | Cyan highlight | Currently selected in topbar |
| `reef-practiced` | Teal fish | Flashcards generated |
| `reef-caught` | Gold trophy | Flashcards completed |
| `quiz-strong` | Green border | ≥80% correct in quiz |
| `quiz-shaky` | Yellow dashed border | 40–80% correct |
| `quiz-weak` | Red dashed border | ≤40% correct |
| `srs-due` | White dotted border | Due for spaced repetition review |

---

### graph_layout.py

Force-directed layout engine. Computes 2D positions for nodes using attraction/repulsion physics.

Key methods on `GraphManager`:

| Method | Description |
|--------|-------------|
| `build_node_positions(node_data, focus_node)` | Initial polar coordinate placement |
| `apply_force_directed_layout(positions, node_data)` | Iterative force simulation |
| `rescale_positions_if_needed(positions)` | Normalises positions to fit the canvas |

---

### config.py

Central store for all settings, theme values, and CSS.

Key exports:

| Export | Type | Description |
|--------|------|-------------|
| `SETTINGS` | dict | All tuneable app settings |
| `GRAPH_CONFIG` | dict | Graph layout parameters (used by `graph_layout.py`) |
| `COMPONENT_SKIN` | dict | Button, input, and layout styles |
| `app_title()` | str | App display name |
| `llm_settings()` | dict | LLM branch counts and retry config |
| `palette()` | dict | Colour tokens |
| `ui_styles()` | dict | Full component style map |
| `help_markdown()` | str | Welcome guide shown on startup |
| `html_shell()` | str | Full HTML page template with inline CSS |

---

## Features

### Knowledge graph
Type any concept to generate an interactive graph of related ideas. Click any node to expand it with new child concepts. The number of nodes generated per click is configurable via the slider (2–8) on the start screen.

### Personalised explanations
After building a graph, get an explanation tailored to what you already know (clicked nodes) vs what you haven't explored yet. Toggle between concise and detailed modes.

### Flashcards
Select any node and generate flashcards. Flip between question and answer, navigate with prev/next, and mark cards as done when finished.

### Quiz
Take a multiple-choice quiz on any set of flashcards. Wrong answer options are misconception-based (not random) for more effective learning. Correct answers earn points; streaks give bonus points.

### Weakness tracking
The app logs every quiz answer. Click "Analyse my mistakes" to get an LLM diagnosis of your knowledge gaps with targeted remediation advice.

### Resource recommendations
Click "Find resources for my gaps" to get 4 curated online resources (YouTube, Khan Academy, Wikipedia, arXiv, Coursera, MIT OCW) matched to your specific weak areas.

### Spaced repetition (SRS)
Quiz performance updates an SM-2-inspired schedule per node. Nodes due for review appear with a white dotted border on the graph.

### Document upload
Upload a `.txt`, `.md`, or `.pdf` file to automatically extract the key concept and build a graph from the document content.

### Session persistence
Quiz history and SRS schedules are saved to `shrimps_session.json` and survive app restarts. The reset button wipes this file.

### Save / Load
Export the current graph state to a JSON file and reload it later.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Your Groq API key |
| `GROQ_MODEL` | No | `llama-3.1-8b-instant` | Fast model for graph/flashcard calls |
| `GROQ_STRONG_MODEL` | No | `llama-3.3-70b-versatile` | Strong model for explanations/analysis |
| `PORT` | No | `8050` | HTTP port to listen on |

---

## Running the App

**Development:**
```bash
python -m shrimps.app
```

**As an installed package:**
```bash
pip install -e .
cheeky-shrimps
```

**Production (gunicorn):**
```bash
gunicorn "shrimps.app:server" --bind 0.0.0.0:8050 --workers 2
```
