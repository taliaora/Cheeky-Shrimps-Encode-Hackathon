# 🦐 Cheeky Shrimps

An AI-powered interactive learning app that builds personalised knowledge graphs, generates flashcards and quizzes, tracks your weak spots, and recommends online resources — all driven by a Groq LLM backend.

Built at the Encode Hackathon 2026.

<img width="2248" height="1300" alt="image" src="https://github.com/user-attachments/assets/28126c0c-1e34-46b7-8194-61776ad11385" />


---

## Features

- **Knowledge graph** — type any concept and get an interactive web of related ideas. Click nodes to expand them.
- **Personalised explanations** — explanations adapt to what you already know vs what you haven't explored.
- **Flashcards** — generate and flip through cards for any node in the graph.
- **Quiz** — multiple-choice questions with misconception-based wrong answers for more effective learning.
- **Weakness tracking** — the app logs every wrong answer and uses an LLM to diagnose your knowledge gaps.
- **Resource recommendations** — get curated links to YouTube, Khan Academy, Wikipedia, arXiv, Coursera, and MIT OCW matched to your weak areas.
- **Spaced repetition (SRS)** — SM-2-inspired scheduling highlights nodes due for review on the graph.
- **Document upload** — upload a `.txt`, `.md`, or `.pdf` to build a graph from your own study material.
- **Session persistence** — quiz history and SRS schedules survive app restarts.

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-org/Cheeky-Shrimps-Encode-Hackathon
cd Cheeky-Shrimps-Encode-Hackathon

conda create -n cheeky-shrimps python=3.11
conda activate cheeky-shrimps

pip install -r requirements.txt
```

### 2. Set up your API key

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Get a free key at [console.groq.com](https://console.groq.com/).

### 3. Run

```bash
python -m shrimps.app
```

Open [http://localhost:8050](http://localhost:8050).

---

## Docker

```bash
docker build -t cheeky-shrimps .
docker run -p 8050:8050 --env-file .env cheeky-shrimps
```

---

## Project Structure

```
shrimps/
├── app.py                    # Entry point
├── state_manager.py          # State transitions and LLM orchestration
├── callback_handlers.py      # Dash callback wiring
├── components.py             # UI component builders
├── llm_client.py             # Groq API wrapper
├── prompts.py                # Prompt builders and response parsers
├── graph_layout_cytoscape.py # Cytoscape element builder + stylesheet
├── graph_layout.py           # Force-directed layout engine
└── config.py                 # Settings, theme, and style constants
```

Full documentation is in [`docs/index.md`](docs/index.md).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI framework | [Dash](https://dash.plotly.com/) + [dash-cytoscape](https://dash.plotly.com/cytoscape) |
| LLM backend | [Groq](https://groq.com/) (`llama-3.1-8b-instant` / `llama-3.3-70b-versatile`) |
| PDF parsing | [pypdf](https://pypdf.readthedocs.io/) |
| Styling | Custom CSS, coral reef theme |

---

## License

MIT — see [LICENSE](LICENSE).
