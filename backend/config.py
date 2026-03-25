import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # gemini | openai | anthropic
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Google Calendar OAuth
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

# Calendar scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_llm():
    """Return configured LLM based on environment."""
    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        return ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            google_api_key=GEMINI_API_KEY,
            temperature=0.2,
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in .env")
        return ChatOpenAI(
            model=MODEL_NAME,
            openai_api_key=OPENAI_API_KEY,
            temperature=0.2,
        )
    elif LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")
        return ChatAnthropic(
            model=MODEL_NAME,
            anthropic_api_key=ANTHROPIC_API_KEY,
            temperature=0.2,
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'gemini', 'openai', or 'anthropic'.")
