"""OpenAI client wrapper with Structured Outputs / JSON Schema support."""
import json

from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client (lazy init)."""
    global _client
    if _client is None:
        kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        _client = AsyncOpenAI(**kwargs)
    return _client


async def structured_completion(
    system_prompt: str,
    user_message: str,
    json_schema: dict,
    model: str | None = None,
    temperature: float = 0.3,
) -> dict:
    """Call OpenAI with Structured Outputs (response_format = json_schema)."""
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=model or settings.OPENAI_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "structured_response",
                "strict": True,
                "schema": json_schema,
            },
        },
        timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
    )
    return json.loads(response.choices[0].message.content)


async def simple_chat(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """For sales copy generation where strict JSON is not needed."""
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=model or settings.OPENAI_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
    )
    return response.choices[0].message.content or ""
