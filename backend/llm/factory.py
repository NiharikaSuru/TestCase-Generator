import os

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq


def get_llm(temperature: float = 0):
    """Return the configured chat model based on LLM_PROVIDER."""
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    
    # Debug logging
    print(f"=== LLM Configuration ===")
    print(f"LLM_PROVIDER (raw): '{os.getenv('LLM_PROVIDER')}'")
    print(f"LLM_PROVIDER (processed): '{provider}'")
    print(f"Available env vars: {list(os.environ.keys())}")
    print(f"========================")

    if provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return ChatOpenAI(
            model=model, 
            temperature=temperature,
            request_timeout=120,  # 2 minute timeout
            max_retries=0  # We handle retries manually with our retry helper
        )

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(
            model=model, 
            temperature=temperature, 
            base_url=base_url,
            timeout=120  # 2 minute timeout
        )

    if provider == "groq":
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(
            model=model, 
            temperature=temperature,
            timeout=120,  # 2 minute timeout
            max_retries=0,  # We handle retries manually with our retry helper
            # Groq free tier has rate limits, optimize token usage
            max_tokens=3000  # Limit output tokens to stay within rate limits
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER='{provider}'. Use one of: openai, ollama, groq."
    )
