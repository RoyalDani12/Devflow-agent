import os

from dotenv import load_dotenv

load_dotenv()


def get_required_setting(name: str) -> str:
    """Return a required environment setting or raise a clear startup error."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is missing from the environment")
    return value
