
import re
  
def build_concept_graph_prompt(concept, count=4):
    return (
        f"I want to learn about {concept}. "
        f"List exactly {count} prerequisite or related concepts that help build understanding of {concept}. "
        f"For each concept, provide:\n"
        f"- a semantic distance from {concept} (between 0.1 and 1.0, step 0.1)\n"
        f"- a breadth score indicating how general the concept is (between 0.1 and 1.0, step 0.1)\n\n"
        f"Format your response strictly as a comma-separated sequence with no extra text:\n"
        f"concept1,distance1,breadth1,concept2,distance2,breadth2,...\n\n"
        f"Respond in English only.\n\n"
        f"Example output:\n"
        f"Linear Algebra,0.1,1.0,Vectors,0.3,0.8,4-D Coordinate System,0.5,0.9,Rotation Matrices,0.8,0.7"
    )


def expand_concept_graph_prompt(concept, excluded_concepts, included_concepts, count=3):
    excluded = excluded_concepts + included_concepts
    return (
        f"I am expanding a knowledge graph for the topic '{concept}'. "
        f"Suggest exactly {count} additional relevant concepts that help deepen understanding of this topic.\n\n"
        f"Do NOT include any of the following already used concepts:\n"
        f"{', '.join(excluded)}\n\n"
        f"For each concept, provide:\n"
        f"- a semantic distance from '{concept}' (0.1 to 1.0, increments of 0.1)\n"
        f"- a breadth score indicating generality (0.1 to 1.0, increments of 0.1)\n\n"
        f"Return ONLY a single comma-separated line in this exact format:\n"
        f"concept1,distance1,breadth1,concept2,distance2,breadth2,...\n\n"
        f"No explanations, no extra text, English only.\n\n"
        f"Example:\n"
        f"Linear Algebra,0.6,1.0,Vectors,0.7,0.8,Rotation Matrices,0.9,0.7"
    )


def explain_concept_concise(concept, excluded_concepts, included_concepts):
    return (
        f"Explain '{concept}' to me.\n\n"
        f"I already understand these concepts:\n"
        f"{', '.join(included_concepts)}\n\n"
        f"I am NOT familiar with:\n"
        f"{', '.join(excluded_concepts)}\n\n"
        f"Guidelines:\n"
        f"- Keep the explanation concise and focused\n"
        f"- Build on what I already know\n"
        f"- Avoid using or referencing concepts I do not know\n"
        f"- Do not restate known concepts unless necessary\n"
        f"- If helpful, use analogies based on concepts I understand\n\n"
        f"Start directly with the explanation. No preamble."
    )


def explain_concept_detailed(concept, excluded_concepts, included_concepts):
    return (
        f"Explain '{concept}' to me.\n\n"
        f"I already understand these concepts:\n"
        f"{', '.join(included_concepts)}\n\n"
        f"I am NOT familiar with:\n"
        f"{', '.join(excluded_concepts)}\n\n"
        f"Guidelines:\n"
        f"- Keep the explanation thorough and detailed\n"
        f"- Build on what I already know\n"
        f"- Avoid using or referencing concepts I do not know\n"
        f"- Do not restate known concepts unless necessary\n"
        f"- If helpful, use analogies based on concepts I understand\n\n"
        f"Start directly with the explanation. No preamble."
    )


def suggest_next_concepts(included_concepts, excluded_concepts):
    return (
        f"Suggest 6 new concepts I can learn next.\n\n"
        f"My current knowledge:\n"
        f"{', '.join(included_concepts)}\n\n"
        f"I am not familiar with:\n"
        f"{', '.join(excluded_concepts)}\n\n"
        f"Requirements:\n"
        f"- Concepts must build naturally on what I already know\n"
        f"- Do NOT include any concepts listed above\n"
        f"- Avoid concepts that are too similar or redundant with known ones\n"
        f"- Prefer concepts that introduce new directions or deeper understanding\n\n"
        f"Output format:\n"
        f"Return exactly 4 concepts as a single comma-separated list.\n"
        f"No explanations, no extra text.\n\n"
        f"Example:\n"
        f"Linear Algebra,Vectors,4-D Coordinate System,Rotation Matrices"
    )


def build_flashcard_prompt(concept, root_term):
    return (
        f"Create 5 flashcards about '{concept}' in the context of '{root_term}'. "
        f"Reply with ONLY the flashcards in this exact format, nothing else:\n"
        f"Title1|Question1|Answer1||Title2|Question2|Answer2||Title3|Question3|Answer3||Title4|Question4|Answer4\n"
        f"Rules: use || between cards, use | between title/question/answer, "
        f"no labels like Q: or A:, no numbering, no extra text before or after."
    )


def parse_flashcards(response):
    """Parse flashcard response into list of {title, q, a} dicts."""
    _label_re = re.compile(r'^[QqAa]\d*[:\.\)]\s*', re.UNICODE)

    def clean(text):
        return _label_re.sub("", text.strip()).strip().rstrip(",")

    text = response.strip()

    raw_cards = [c.strip() for c in text.split("||") if c.strip()]

    if len(raw_cards) <= 1:
        raw_cards = [line.strip() for line in text.splitlines() if line.strip() and "|" in line]

    if len(raw_cards) <= 1:
        raw_cards = [c.strip() for c in re.split(r'\n{2,}|---+', text) if c.strip()]

    cards = []
    for card in raw_cards:
        parts = [p.strip() for p in card.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 3:
            cards.append({"title": clean(parts[0]), "q": clean(parts[1]), "a": clean(parts[2])})
        elif len(parts) == 2:
            cards.append({"title": "", "q": clean(parts[0]), "a": clean(parts[1])})
        else:
            lines = [l.strip() for l in card.splitlines() if l.strip()]
            q, a, title = "", "", ""
            for line in lines:
                low = line.lower()
                if low.startswith("title"):
                    title = re.sub(r'^title\s*[:\-]\s*', '', line, flags=re.IGNORECASE)
                elif low.startswith("q") or low.startswith("question"):
                    q = re.sub(r'^(question|q)\s*\d*\s*[:\-]\s*', '', line, flags=re.IGNORECASE)
                elif low.startswith("a") or low.startswith("answer"):
                    a = re.sub(r'^(answer|a)\s*\d*\s*[:\-]\s*', '', line, flags=re.IGNORECASE)
            if q and a:
                cards.append({"title": title, "q": clean(q), "a": clean(a)})

    print(f"[parse_flashcards] parsed {len(cards)} cards")
    return cards


def build_quiz_prompt(concept, root_term, cards):
    """Generate conceptually adjacent wrong answers for each flashcard question."""
    questions = "\n".join([f"Q{i+1}: {c['q']} | ANSWER: {c['a']}" for i, c in enumerate(cards)])
    return (
        f"For each question below about '{concept}' (in the context of '{root_term}'), "
        f"generate 3 wrong answer options that represent COMMON MISCONCEPTIONS or "
        f"conceptually adjacent but incorrect ideas — not obviously wrong answers.\n"
        f"Format EXACTLY as: Q1|wrong1|wrong2|wrong3||Q2|wrong1|wrong2|wrong3 etc. "
        f"Nothing else.\n{questions}"
    )


def parse_quiz_options(response, cards):
    """Merge wrong options with correct answers into quiz question list."""
    quiz = []
    for i, block in enumerate(response.strip().split("||")):
        parts = block.strip().split("|")
        if len(parts) >= 4 and i < len(cards):
            wrongs = [p.strip() for p in parts[1:4]]
            correct = cards[i]["a"]
            options = wrongs + [correct]
            import random; random.shuffle(options)
            quiz.append({
                "q": cards[i]["q"],
                "options": options,
                "answer": correct,
            })
    return quiz


def build_weakness_report_prompt(wrong_answers: list[dict]) -> str:
    """Build a prompt asking the LLM to diagnose weak spots and suggest remediation."""
    lines = "\n".join(
        f"- Concept: {w['node']} | Question: {w['question']} | Correct: {w['correct_answer']} | User answered: {w['chosen']}"
        for w in wrong_answers
    )
    return (
        f"A student got the following quiz questions wrong:\n\n"
        f"{lines}\n\n"
        f"Based on these mistakes:\n"
        f"1. Identify the 1-2 core knowledge gaps these errors reveal.\n"
        f"2. Give a concise, targeted explanation (3-5 sentences) that directly addresses those gaps.\n"
        f"3. Suggest 1-2 specific things they should review or practise next.\n\n"
        f"Be direct and practical. No preamble."
    )


def build_resource_recommendations_prompt(wrong_answers: list[dict]) -> str:
    """Build a prompt asking the LLM to recommend specific online learning resources."""
    lines = "\n".join(
        f"- Concept: {w['node']} | Wrong answer given: {w['chosen']} | Correct: {w['correct_answer']}"
        for w in wrong_answers
    )
    return (
        f"A student is struggling with these concepts based on quiz mistakes:\n\n"
        f"{lines}\n\n"
        f"Recommend exactly 4 high-quality online resources to help them.\n"
        f"For each resource provide:\n"
        f"- type: one of: YouTube, Khan Academy, Wikipedia, arXiv, Coursera, MIT OpenCourseWare\n"
        f"- query: a specific search query or article title to look up on that platform\n"
        f"- reason: one sentence on why it addresses the gap\n\n"
        f"Format EXACTLY as (one resource per line, pipe-separated):\n"
        f"type|query|reason\n\n"
        f"No extra text, no numbering, no blank lines between entries."
    )


def parse_resource_recommendations(response: str) -> list[dict]:
    """Parse pipe-separated resource recommendations into a list of dicts."""
    resources = []
    for line in response.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            resources.append({"type": parts[0], "title": parts[1], "reason": parts[2]})
    return resources


def build_concept_graph_from_text_prompt(document_text: str) -> str:
    """Build a concept graph from pasted/uploaded document text."""
    excerpt = document_text[:3000]  # keep prompt manageable
    return (
        f"I have the following text from a document I want to study:\n\n"
        f"---\n{excerpt}\n---\n\n"
        f"Identify the single most important root concept in this text, "
        f"then list exactly 4 prerequisite or related concepts that help build understanding of it.\n\n"
        f"For each concept, provide:\n"
        f"- a semantic distance from the root (between 0.1 and 1.0, step 0.1)\n"
        f"- a breadth score indicating how general the concept is (between 0.1 and 1.0, step 0.1)\n\n"
        f"Format your response strictly as:\n"
        f"ROOT: <root concept name>\n"
        f"concept1,distance1,breadth1,concept2,distance2,breadth2,...\n\n"
        f"Respond in English only. No extra text."
    )


def parse_concept_graph_from_text(response: str) -> tuple[str, dict]:
    """Parse the root concept and related concepts from a document-based prompt response."""
    print(f"[parse_concept_graph_from_text] raw response:\n{response[:500]}")
    root = ""
    concepts_line = ""

    lines = [l.strip() for l in response.strip().splitlines() if l.strip()]

    # Extract ROOT line
    for line in lines:
        if line.upper().startswith("ROOT:"):
            root = line.split(":", 1)[1].strip()
            break

    # Find the concepts line — the one with the most commas and numeric values
    best_line = ""
    best_score = 0
    for line in lines:
        if line.upper().startswith("ROOT:"):
            continue
        # Score by number of numeric tokens (distance/breadth values)
        parts = [p.strip() for p in line.replace("\n", ",").split(",")]
        numeric_count = sum(1 for p in parts if _is_float(p))
        if numeric_count > best_score:
            best_score = numeric_count
            best_line = line

    # Also try joining all non-ROOT lines in case concepts span multiple lines
    non_root_text = " ".join(l for l in lines if not l.upper().startswith("ROOT:"))

    concepts = {}
    if best_score >= 2:
        concepts = parse_terms(best_line)
    if not concepts:
        concepts = parse_terms(non_root_text)

    # Fallback root from first line
    if not root and lines:
        root = lines[0]

    print(f"[parse_concept_graph_from_text] root={root!r}, concepts={list(concepts.keys())}")
    return root, concepts


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_terms(response_text, max_terms=4):
    import re
    pattern = re.compile(r'([\w\s\-&]+?)\s*,?\s*distance\s*=\s*([0-9.]+)\s*,\s*breadth\s*=\s*([0-9.]+)')
    results = {}
    print(response_text)
    matches = pattern.findall(response_text)
    if matches:
        for term, distance, breadth in matches[:max_terms]:
            results[term.strip()] = {
                "distance": float(distance),
                "breadth": float(breadth),
            }
        return results

    pieces = [
        value.strip()
        for value in response_text.replace("\n", ",").split(",")
        if value.strip()
    ]
    for i in range(0, min(len(pieces), max_terms * 3), 3):
        try:
            term = pieces[i]
            distance = float(pieces[i + 1])
            breadth = float(pieces[i + 2])
        except (IndexError, ValueError):
            print("Warning: Malformed values, could not parse all items cleanly.")
            break
        results[term] = {
            "distance": distance,
            "breadth": breadth,
        }
    return results
