"""
AI Pipeline — LLM Instantiation and Fallback Logic.
"""

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import settings


def get_primary_llm(temperature: float = 0.0):
    """
    Get the primary LLM (Claude 3.5 Sonnet).
    """
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


def get_llm(temperature: float = 0.0, use_fallback: bool = False):
    """
    Get the LLM with fallback support.
    """
    # For MVP, we use the fallback model directly if requested (e.g. out of Anthropic credits),
    # but normally we could use Langchain's with_fallbacks().
    if use_fallback:
        return get_fallback_llm(temperature)

    primary = get_primary_llm(temperature)
    fallback = get_fallback_llm(temperature)
    return primary.with_fallbacks([fallback])
