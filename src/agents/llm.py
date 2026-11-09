
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

MODEL = "openai/gpt-oss-20b"


def generate_response(
    prompt: str,
    system_prompt: str = "You are DevFlow AI, a helpful assistant for developers.",
    max_tokens: int = 1024,
) -> str:
    """Generate a response using Groq."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )

    return response.choices[0].message.content or ""
