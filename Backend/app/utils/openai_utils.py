import os
from dotenv import load_dotenv
from openai import OpenAI
from core.config import config


def openai_generate(messages: list):
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    completion = client.chat.completions.create(
        messages=messages,
        model=config.OPENAI_MODEL,
        temperature=config.OPENAI_TEMPERATURE,
        max_tokens=config.OPENAI_MAX_TOKENS,
    )
    return completion

