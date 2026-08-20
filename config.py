

import os
from dotenv import load_dotenv

load_dotenv()  

# ---- API KEYS ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ---- MODELS ----
GEMINI_MODEL = "gemini-3.6-flash"                   
GROQ_MODEL = "openai/gpt-oss-20b"                   
CRITIC_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"

# ---- SEARCH SETTINGS ----
MAX_SUB_QUESTIONS = 4         
RESULTS_PER_QUERY = 5         
MAX_CHARS_PER_PAGE = 4000     

# ---- OUTPUT ----
SAVE_REPORTS_TO = "reports"   
