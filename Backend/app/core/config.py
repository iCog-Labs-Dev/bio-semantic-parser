import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  

    NCBI_API_KEY= os.getenv("NCBI_API_KEY")
    GROQ_API_KEY = os.getenv("API_KEY")
    MEDCAT_URL = os.getenv("MEDCAT_URL","http://localhost:5000")
    
    # gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = "models/gemini-2.0-flash-lite"
    GEMINI_TEMPERATURE = 0.0
    GEMINI_MAX_TOKENS =  4096
    
    # openai
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4"
    OPENAI_TEMPERATURE = 0.0
    OPENAI_MAX_TOKENS = 4096

# Create a config instance
config = Config()
