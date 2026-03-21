
import re
  
def build_concept_graph_prompt(concept):
    return (
        f"I want to learn about {concept}. "
        f"List exactly 4 prerequisite or related concepts that help build understanding of {concept}. "
        f"For each concept, provide:\n"
        f"- a semantic distance from {concept} (between 0.1 and 1.0, step 0.1)\n"
        f"- a breadth score indicating how general the concept is (between 0.1 and 1.0, step 0.1)\n\n"
        f"Format your response strictly as a comma-separated sequence with no extra text:\n"
        f"concept1,distance1,breadth1,concept2,distance2,breadth2,...\n\n"
        f"Respond in English only.\n\n"
        f"Example output:\n"
        f"Linear Algebra,0.1,1.0,Vectors,0.3,0.8,4-D Coordinate System,0.5,0.9,Rotation Matrices,0.8,0.7"
    )


def expand_concept_graph_prompt(concept, excluded_concepts, included_concepts):
    excluded = excluded_concepts + included_concepts
    return (
        f"I am expanding a knowledge graph for the topic '{concept}'. "
        f"Suggest exactly 3 additional relevant concepts that help deepen understanding of this topic.\n\n"
        f"Do NOT include any of the following already used concepts:\n"
        f"{', '.join(excluded)}\n\n"
        f"For each concept, provide:\n"
        f"- a semantic distance from '{concept}' (0.1 to 1.0, increments of 0.1)\n"
        f"- a breadth score indicating generality (0.1 to 1.0, increments of 0.1)\n\n"
        f"Return ONLY a single comma-separated line in this exact format:\n"
        f"concept1,distance1,breadth1,concept2,distance2,breadth2,concept3,distance3,breadth3\n\n"
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
        f"Suggest 4 new concepts I can learn next.\n\n"
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
        f"Create 4 flashcards about '{concept}' in the context of '{root_term}'. "
        f"Reply with ONLY the flashcards in this exact format, nothing else:\n"
        f"Title1|Question1|Answer1||Title2|Question2|Answer2||Title3|Question3|Answer3||Title4|Question4|Answer4\n"
        f"Rules: use || between cards, use | between title/question/answer, "
        f"no labels like Q: or A:, no numbering, no extra text before or after."
    )


def parse_flashcards(response):
    """Parse flashcard response into list of {title, q, a} dicts."""
    _label_re = re.compile(r'^[QqAa]\d*[:\.\)]\s*', re.UNICODE)

    def clean(text):
        return _label_re.sub("", text.strip()).strip()

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
    """Generate multiple-choice options for each flashcard question."""
    questions = "\n".join([f"Q{i+1}: {c['q']} | ANSWER: {c['a']}" for i, c in enumerate(cards)])
    return (
        f"For each question below about '{concept}' (in the context of '{root_term}'), "
        f"generate 3 plausible but wrong answer options. "
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


def parse_terms(response_text, max_terms=4):
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
