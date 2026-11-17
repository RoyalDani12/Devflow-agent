import logging
import time
from groq import APIError, BadRequestError, Groq, RateLimitError

from src.config import get_required_setting

logger = logging.getLogger("DevFlowLLM")

PRIMARY_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODEL = "openai/gpt-oss-120b"
RESERVE_MODEL = "qwen/qwen3.8-27b"
MODEL_CANDIDATES = [PRIMARY_MODEL, RESERVE_MODEL, FALLBACK_MODEL]
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
    """Generate response with automatic multi-model rotation on rate limits or errors."""
    client = _get_client()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    last_error = None
    for model in MODEL_CANDIDATES:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""
            if content.strip():
                return content
            logger.info("Model %s returned empty text, trying next...", model)
        except RateLimitError as exc:
            logger.warning("Rate limit hit on %s. Rotating to next model...", model)
            last_error = exc
            time.sleep(1)
        except BadRequestError as exc:
            logger.warning("Bad request on %s: %s. Rotating...", model, exc)
            last_error = exc
        except APIError as exc:
            logger.warning("API error on %s: %s. Rotating...", model, exc)
            last_error = exc

    if last_error:
        logger.info("Waiting 4s before final attempt on reserve model...")
        time.sleep(4)
        try:
            res = client.chat.completions.create(
                model=RESERVE_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return res.choices[0].message.content or ""
        except Exception:
            raise last_error

    return ""
