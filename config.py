"""
Configuration for the AI Research System.
Keys are loaded from a .env file in this folder (create one — see .env.example).
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in the current working directory

# ---- API KEYS ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ---- MODELS ----
GEMINI_MODEL = "gemini-3.6-flash"                       # long context, synthesis
GROQ_MODEL = "openai/gpt-oss-20b"                       # fast planning / routing
CRITIC_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free" # reasoning / critique, via OpenRouter

# ---- SEARCH SETTINGS ----
MAX_SUB_QUESTIONS = 4          # how many sub-questions the planner can create
RESULTS_PER_QUERY = 5          # DuckDuckGo results pulled per sub-question
MAX_CHARS_PER_PAGE = 4000      # trim fetched page content to keep tokens sane

# ---- OUTPUT ----
SAVE_REPORTS_TO = "reports"    # folder where markdown reports get saved