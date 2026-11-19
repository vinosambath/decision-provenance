from __future__ import annotations

from openai import OpenAI

from app.config import get_settings

_client: OpenAI | None = None


def _client_instance() -> OpenAI:
    global _client
    if _client is None:
        api_key = get_settings().openai_api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set — required to generate the synthetic corpus")
        _client = OpenAI(api_key=api_key)
    return _client


def complete(system: str, user: str) -> str:
    settings = get_settings()
    response = _client_instance().chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=1.0,
    )
    return (response.choices[0].message.content or "").strip()
