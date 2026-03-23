import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
DB_PATH = "data/company.db"

# v2: user can set any folder path here
# Examples:
#   DOCS_FOLDER = r"C:\Users\Suhimugan\Documents"
#   DOCS_FOLDER = r"D:\Work\Projects"
DOCS_FOLDER = os.getenv("DOCS_FOLDER", "data/docs")

# File types the agent can read
SUPPORTED_EXTENSIONS = (".txt", ".md", ".pdf", ".docx")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found. Check your .env file.")