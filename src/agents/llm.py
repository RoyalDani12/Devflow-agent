
from groq import Groq

from src.config import get_required_setting

MODEL = "openai/gpt-oss-20b"


def _get_client() -> Groq:
    return Groq(api_key=get_required_setting("GROQ_API_KEY"))


def generate_response(
    prompt: str,
    system_prompt: str = "You are DevFlow AI, a helpful assistant for developers.",
    max_tokens: int = 1024,
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
