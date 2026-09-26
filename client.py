"""Shared Gemini client factory.

Both AI modules pull their client from here so we only create one
genai.Client instance for the lifetime of the app.
"""

from google import genai

from ..config import settings

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client

    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)

    return _client
