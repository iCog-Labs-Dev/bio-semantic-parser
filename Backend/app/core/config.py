import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    NCBI_API_KEY = os.getenv("NCBI_API_KEY") or None
    GROQ_API_KEY = os.getenv("API_KEY")
    MEDCAT_URL = os.getenv("MEDCAT_URL", "http://localhost:5000/api/process")

    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_TEMPERATURE = 0.0
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.0"))
    GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "4096"))

    # Opt in for bounded, partial extraction during demonstrations.
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"true", "1", "yes"}
    DEMO_METADATA_SAMPLES = max(1, int(os.getenv("DEMO_METADATA_SAMPLES", "2")))
    DEMO_ABSTRACT_CHUNKS = max(1, int(os.getenv("DEMO_ABSTRACT_CHUNKS", "2")))
    DEMO_MAX_INPUT_TOKENS = max(1, int(os.getenv("DEMO_MAX_INPUT_TOKENS", "2000")))
    DEMO_MAX_OUTPUT_TOKENS = max(1, int(os.getenv("DEMO_MAX_OUTPUT_TOKENS", "512")))
# Create a config instance
config = Config()
