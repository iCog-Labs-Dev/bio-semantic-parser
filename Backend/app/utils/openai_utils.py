import os
from dotenv import load_dotenv
from app.core.config import config
from app.utils.ai_provider import ai_generate


def openai_generate(messages: list):

    if config.AI_PROVIDER == "gemini":
        return ai_generate(
            messages=messages,
            model=None,  # model name handled inside config
            temperature=config.GEMINI_TEMPERATURE,
            max_tokens=config.GEMINI_MAX_TOKENS,
        )
    else:
        return ai_generate(
            messages=messages,
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=config.OPENAI_MAX_TOKENS,
        )

