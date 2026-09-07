from langchain_groq import ChatGroq

from app.config.settings import Settings


def get_llm():
    """Lazy initialization of LLM to allow for configuration changes."""
    return ChatGroq(
        model=Settings().groq_model,
        api_key=Settings().groq_api_key,
        timeout=15,
    )
