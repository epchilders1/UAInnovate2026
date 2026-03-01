import os
import secrets
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / '.env')

class Config:
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MODEL = "gpt-4o-mini"
