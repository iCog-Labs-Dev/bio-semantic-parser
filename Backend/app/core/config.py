import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    PUBMED_API_KEY= os.getenv("PUBMED_API_KEY")

# Create a config instance
config = Config()
