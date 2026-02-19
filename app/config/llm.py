from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import Settings

def get_llm():
    """Lazy initialization of LLM to allow for configuration changes."""
    return ChatGoogleGenerativeAI(model=Settings().gemini_model_name)