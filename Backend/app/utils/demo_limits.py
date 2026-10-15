"""Local prompt limits; never call an LLM to count tokens.

Use the configured OpenAI model's tokenizer, or cl100k_base as a local estimate
for Gemini/unknown models. Provider-specific chat framing is reserved separately.
"""
from functools import lru_cache
import logging

import tiktoken

from app.core.config import config


@lru_cache(maxsize=4)
def tokenizer(model):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def encode(text):
    model = config.OPENAI_MODEL if config.AI_PROVIDER == "openai" else "gpt-4"
    return tokenizer(model).encode(text, disallowed_special=())


def truncate_text(text, max_tokens):
    tokens = encode(text)
    if len(tokens) <= max_tokens:
        return text
    model = config.OPENAI_MODEL if config.AI_PROVIDER == "openai" else "gpt-4"
    return tokenizer(model).decode(tokens[:max(0, max_tokens)], errors="ignore")


def limit_demo_messages(messages):
    """Keep instructions and truncate source text to fit the demo input budget."""
    # Conservative allowance for role labels and chat-message framing.
    budget = config.DEMO_MAX_INPUT_TOKENS - 16 - 12 * len(messages)
    budget -= sum(len(encode(m["content"])) for m in messages if m["role"] == "system")
    if budget <= 0:
        raise ValueError("DEMO_MAX_INPUT_TOKENS is too small for the extraction instructions.")

    limited = []
    for message in messages:
        copy = dict(message)
        if message["role"] != "system":
            copy["content"] = truncate_text(message["content"], budget)
            budget -= len(encode(copy["content"]))
        limited.append(copy)
    before = sum(len(encode(m["content"])) for m in messages)
    after = sum(len(encode(m["content"])) for m in limited)
    if after < before:
        logging.info("Demo prompt truncated: %s to %s content tokens", before, after)
    return limited
