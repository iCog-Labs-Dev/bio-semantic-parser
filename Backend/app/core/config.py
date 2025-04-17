import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    NCBI_API_KEY= os.getenv("NCBI_API_KEY")

# Create a config instance
config = Config()
