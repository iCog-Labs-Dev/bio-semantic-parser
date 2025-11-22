import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    NCBI_API_KEY= os.getenv("NCBI_API_KEY")
    GROQ_API_KEY = os.getenv("API_KEY")
    MEDCAT_URL = os.getenv("MEDCAT_URL","http://localhost:5000")

    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4"
    OPENAI_TEMPERATURE = 0.0
    OPENAI_MAX_TOKENS = 4096

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.0"))
    GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "4096"))
# Create a config instance
config = Config()
