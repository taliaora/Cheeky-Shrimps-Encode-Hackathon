# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.0] — 2026-03-21

### Added
- Interactive knowledge graph built from a root concept using Groq LLM
- Force-directed graph layout with coral reef visual theme
- Personalised explanations adapting to known vs unknown concepts
- Short and detailed explanation modes
- Flashcard generation and flip-card UI for any graph node
- Multiple-choice quiz with misconception-based wrong answers
- Quiz scoring with streak bonuses
- Weakness tracking agent — logs wrong answers and generates LLM diagnosis
- Resource recommender agent — suggests YouTube, Khan Academy, Wikipedia, arXiv, Coursera, MIT OCW resources for weak areas
- Spaced repetition (SM-2-inspired) scheduling with due-node highlighting on graph
- Graph quiz-performance colouring (green/yellow/red borders)
- Document upload — build a graph from `.txt`, `.md`, or `.pdf` files
- PDF text extraction via `pypdf`
- Session persistence — quiz history and SRS schedule saved to `shrimps_session.json`
- Multi-model routing — fast model for graph/flashcard calls, strong model for explanations and analysis
- Configurable node count per click via slider (2–8 nodes)
- "Analysing document" toast notification during file processing
- Deferred suggestion loading so graph renders immediately
- Reduced `max_tokens` per call type for faster LLM responses
- Reset button clears all state including persisted session
- Save / Load graph state as JSON
- Full documentation in `docs/index.md`
- `pyproject.toml`, `requirements.txt`, `.gitignore`, `.env.example`, `Dockerfile`
