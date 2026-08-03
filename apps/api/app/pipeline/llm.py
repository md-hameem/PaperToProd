"""
AI Pipeline — LLM Instantiation and Fallback Logic.
"""

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import settings


def get_primary_llm(
    temperature: float = 0.0, byo_api_key: str | None = None, byo_provider: str | None = None
):
    """
    Get the primary LLM (Claude 3.5 Sonnet) or a BYO model if specified.
    """
    if byo_api_key and byo_provider == "openai":
        return ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            api_key=SecretStr(byo_api_key),
        )
    elif byo_api_key and byo_provider == "anthropic":
        return ChatAnthropic(
            model_name="claude-3-5-sonnet-20240620",
            temperature=temperature,
            timeout=None,
            stop=None,
            api_key=SecretStr(byo_api_key),
        )

    api_key_str = (
        settings.anthropic_api_key.get_secret_value()
        if hasattr(settings.anthropic_api_key, "get_secret_value")
        else settings.anthropic_api_key
    )
    return ChatAnthropic(
        model_name="claude-3-5-sonnet-20240620",
        temperature=temperature,
        timeout=None,
        stop=None,
        api_key=SecretStr(api_key_str) if isinstance(api_key_str, str) else api_key_str,
    )


def get_fallback_llm(temperature: float = 0.0):
    """
    Get the fallback LLM (GPT-4o).
    """
    api_key_str = (
        settings.openai_api_key.get_secret_value()
        if hasattr(settings.openai_api_key, "get_secret_value")
        else settings.openai_api_key
    )
    return ChatOpenAI(
        model="gpt-4o",
        temperature=temperature,
        api_key=SecretStr(api_key_str) if isinstance(api_key_str, str) else api_key_str,
    )


def get_llm(
    temperature: float = 0.0,
    use_fallback: bool = False,
    byo_api_key: str | None = None,
    byo_provider: str | None = None,
):
    """
    Get the LLM with fallback support.
    """
    # For MVP, we use the fallback model directly if requested (e.g. out of Anthropic credits),
    # but normally we could use Langchain's with_fallbacks().
    if use_fallback:
        return get_fallback_llm(temperature)

    # If a BYO key is provided, we just use it directly (no system fallback to our own keys)
    if byo_api_key:
        return get_primary_llm(temperature, byo_api_key=byo_api_key, byo_provider=byo_provider)

    primary = get_primary_llm(temperature)
    fallback = get_fallback_llm(temperature)
    return primary.with_fallbacks([fallback])
