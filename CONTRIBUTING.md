# Contributing

Thanks for your interest in contributing to Cheeky Shrimps.

---

## Getting set up

```bash
git clone https://github.com/your-org/Cheeky-Shrimps-Encode-Hackathon
cd Cheeky-Shrimps-Encode-Hackathon

conda create -n cheeky-shrimps python=3.11
conda activate cheeky-shrimps

pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
```

Run the app:

```bash
python -m shrimps.app
```

---

## Project conventions

**State is immutable.** All functions in `state_manager.py` accept a state dict and return a new one — never mutate in place. Use `copy.deepcopy` before modifying.

**Prompts live in `prompts.py`.** If you're changing what the LLM is asked, the prompt builder and its parser both go in `prompts.py`.

**UI components are pure builders.** `components.py` functions return Dash component trees with no side effects. Business logic belongs in `state_manager.py`.

**Callbacks are thin.** `callback_handlers.py` should only read inputs, call state manager functions, and return outputs. Keep logic out of callbacks.

**Model routing.** Use `generate_text(prompt, strong=False)` for fast structured calls (graph expansion, flashcards, quiz options). Use `strong=True` for quality-sensitive calls (explanations, weakness reports, resource recommendations).

---

## Making changes

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test manually by running the app and exercising the affected feature
4. Commit with a clear message: `git commit -m "add: description of change"`
5. Open a pull request against `main`

---

## Adding a new LLM agent

1. Add a prompt builder function to `prompts.py` (and a parser if the response needs structured output)
2. Add an orchestration function to `state_manager.py` that calls `_call_for_text()`
3. Add a button/trigger to `components.py`
4. Wire the callback in `callback_handlers.py`
5. Update `docs/index.md`

---

## Reporting bugs

Open a GitHub issue with:
- What you did
- What you expected
- What actually happened
- Any terminal output or error messages
