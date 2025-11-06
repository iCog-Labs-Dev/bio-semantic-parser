import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from google.generativeai import GenerativeModel, configure
from app.core.config import config  


def openai_generate(messages: list):
    provider = config.LLM_PROVIDER  

    if provider == "openai":
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        completion = client.chat.completions.create(
            messages=messages,
            model=config.OPENAI_MODEL,
            temperature=config.OPENAI_TEMPERATURE,
            max_tokens=config.OPENAI_MAX_TOKENS,
        )
        return completion

    elif provider == "gemini":
        configure(api_key=config.GEMINI_API_KEY)

        prompt_parts = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            prompt_parts.append(f"{role.capitalize()}: {content}")
        full_prompt = "\n".join(prompt_parts)

        model = GenerativeModel(config.GEMINI_MODEL)
        response = model.generate_content( 
            full_prompt,
            generation_config={
                "temperature": config.GEMINI_TEMPERATURE,
                "max_output_tokens": config.GEMINI_MAX_TOKENS,
            }
        )

        raw = response.text.strip()

        # 🛠 Attempt to extract valid JSON if Gemini returned natural language or formatted JSON
        try:
            # If it's a code block like ```json\n{...}\n```, extract the inner JSON
            if raw.startswith("```"):
                raw = raw.strip("`")
                if "\n" in raw:
                    raw = raw.split("\n", 1)[1]  # remove the language tag like "json\n"

            json.loads(raw)
        except Exception:
            raw = '{}' 

        # Wrap Gemini response in OpenAI-like format
        class FakeMessage:
            def __init__(self, content):
                self.content = content

        class FakeChoice:
            def __init__(self, content):
                self.message = FakeMessage(content)

        class FakeGeminiResponse:
            def __init__(self, content):
                self.choices = [FakeChoice(content)]

        return FakeGeminiResponse(raw)

    else:
        raise ValueError("Unsupported LLM provider.")
