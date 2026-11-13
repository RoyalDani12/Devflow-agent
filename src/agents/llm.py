from groq import BadRequestError, Groq

from src.config import get_required_setting

PRIMARY_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODEL = "openai/gpt-oss-120b"
MODEL = PRIMARY_MODEL

DEVFLOW_SYSTEM_PROMPT = """You are DevFlow Agent, an elite AI assistant communicating directly with your creator and owner.
Respond with high technical intelligence, clear formatting, and engaging developer emojis.
STRICT RULES:
- Never use markdown tables (|---|---|) or ASCII grids; use clean bullet points.
- Never output clusters of asterisks (***).
- You do NOT have access to a web browser, search engine, or external tools.
- Absolutely NEVER emit tool calls, function calls, or JSON objects like browser.open or browser.search.
- Rely strictly on the text provided in the prompt and output plain text directly.
- Be direct, highly knowledgeable, and helpful.
"""


def _get_client() -> Groq:
    return Groq(api_key=get_required_setting("GROQ_API_KEY"))


def generate_response(
    prompt: str,
    system_prompt: str = DEVFLOW_SYSTEM_PROMPT,
    max_tokens: int = 4096,
    temperature: float = 0.2,
) -> str:
    """Generate a response using Groq, with automatic fallback if tool-call errors occur."""
    client = _get_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except BadRequestError as exc:
        err_str = str(exc).lower()
        if "tool" in err_str:
            # Fallback to secondary model if primary attempted an unauthorized tool call
            fallback_response = client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return fallback_response.choices[0].message.content or ""
        raise
