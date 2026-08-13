import os
from dotenv import load_dotenv

load_dotenv()

# LLM provider keys - set these in a .env file (see .env.example) or your shell environment.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Optional - raises GitHub's unauthenticated rate limit from 60/hr to 5000/hr.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Concurrency caps
MAX_CONCURRENT_REQUESTS = 20
MAX_CONCURRENT_LLM_CALLS = 5

# LLM endpoints
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# Chunking - keeps LLM payloads well under typical 413 limits while preserving
# semantic density (chunk on paragraph boundaries, not mid-sentence).
MAX_CHARS_PER_CHUNK = 6000

# Freshness window for news/jobs (Phase II requirement)
FRESHNESS_HOURS = 24

# Retry / backoff
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2
