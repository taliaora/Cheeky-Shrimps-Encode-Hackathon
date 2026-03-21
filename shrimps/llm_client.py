import os
from dotenv import load_dotenv
from groq import Groq
from shrimps.prompts import expand_concept_graph_prompt, parse_terms

load_dotenv()

DEFAULT_MODEL = "llama-3.1-8b-instant"
MODEL_NAME = os.getenv("GROQ_MODEL", DEFAULT_MODEL)
API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=API_KEY)


def generate_text(prompt: str) -> str:
    """Send a single-turn prompt to the Groq chat API and return the model output.

    Args:
        prompt: Input text to send to the model.

    Returns:
        The generated response text, or a readable error message if the request fails.
    """
    try:
        completion = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        text = completion.choices[0].message.content or ""
        print(f"[Groq] received {len(text)} characters")
        print(text[:200])
        return text
    except Exception as exc:
        return f"Request failed: {exc}"


def main() -> None:
    topic = "fermions"
    unknown_concepts = ["3D", "4D"]
    known_concepts = ["vectors", "rotation matrices"]
    prompt = expand_concept_graph_prompt(topic, unknown_concepts, known_concepts)
    output = generate_text(prompt)
    print(f"Groq response: {output}")
    extracted_terms = parse_terms(output)
    print(f"Parsed terms: {extracted_terms}")


if __name__ == "__main__":
    main()
