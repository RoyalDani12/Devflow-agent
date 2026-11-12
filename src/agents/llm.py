from groq import Groq

from src.config import get_required_setting

MODEL = "openai/gpt-oss-20b"

DEVFLOW_SYSTEM_PROMPT = """You are DevFlow Agent, an elite AI assistant communicating directly with your creator and owner.
Respond with high technical intelligence, clear formatting, and engaging developer emojis.
STRICT RULES:
- Never use markdown tables (|---|---|) or ASCII grids; use clean bullet points.
- Never output clusters of asterisks (***).
- Be direct, highly knowledgeable, and helpful.
"""


def _get_client() -> Groq:
    return Groq(api_key=get_required_setting("GROQ_API_KEY"))


def generate_response(
    prompt: str,
    system_prompt: str = DEVFLOW_SYSTEM_PROMPT,
    max_tokens: int = 4096,
) -> str:
    """Generate a response using Groq."""
    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content or ""
