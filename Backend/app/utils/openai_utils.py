import os
from dotenv import load_dotenv
from app.core.config import config
from app.utils.ai_provider import ai_generate
from app.utils.demo_limits import limit_demo_messages


def openai_generate(messages: list):
    if config.DEMO_MODE:
        messages = limit_demo_messages(messages)
    output_limit = config.DEMO_MAX_OUTPUT_TOKENS if config.DEMO_MODE else None
    if config.AI_PROVIDER == "gemini":
        return ai_generate(
            messages=messages,
            model=None,  # model name handled inside config
            temperature=config.GEMINI_TEMPERATURE,
            max_tokens=min(config.GEMINI_MAX_TOKENS, output_limit) if output_limit else config.GEMINI_MAX_TOKENS,
        )
    else:
        return ai_generate(
            messages=messages,
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=min(config.OPENAI_MAX_TOKENS, output_limit) if output_limit else config.OPENAI_MAX_TOKENS,
        )

