import os
from langchain_openai import ChatOpenAI
import sys
from pathlib import Path

# Make sure the shared llm_config package is importable in both local and container contexts
_CURRENT_FILE = Path(__file__).resolve()
for _candidate in (_CURRENT_FILE.parents[2], _CURRENT_FILE.parents[1]):
    if (_candidate / "llm_config").exists():
        sys.path.insert(0, str(_candidate))
        break

from llm_config.llm_config import get_model_config, llm_env, validate_model

# Disable LangSmith tracing to avoid rate limits
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""

def get_llm(model_name: str):
    # Validate model exists
    is_valid, error = validate_model(model_name)
    if not is_valid:
        raise ValueError(error)

    # Get model configuration
    model_config = get_model_config(model_name)
    resolved_model_id = model_config.model_id
    provider = model_config.provider.lower()

    # Validate API keys for provider
    keys_valid, key_error = llm_env.validate_provider_keys(provider)
    if not keys_valid:
        raise ValueError(f"{key_error}. Please configure the required API key.")

    # Get temperature from environment or use default
    temperature = llm_env.default_temperature

    # OpenAI Chat models
    if provider == "openai":
        return ChatOpenAI(
            model=resolved_model_id,
            openai_api_key=llm_env.openai_api_key,
            temperature=temperature
        )

    # Anthropic Claude models
    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=resolved_model_id,
                anthropic_api_key=llm_env.anthropic_api_key,
                temperature=temperature
            )
        except ImportError:
            raise ValueError(
                f"Claude models require 'langchain-anthropic' package. "
                f"Install with: pip install langchain-anthropic"
            )
    
    # Ollama models - local CPU-based inference
    elif provider == "ollama":
        ollama_host = os.getenv("LLM_OLLAMA_HOST", "http://ollama:11434")
        try:
            from langchain_ollama import OllamaLLM
            return OllamaLLM(
                model=resolved_model_id,
                base_url=ollama_host,
                temperature=temperature
            )
        except ImportError:
            raise ValueError(
                f"Ollama models require 'langchain-ollama' package. "
                f"Install with: pip install langchain-ollama"
            )

    else:
        raise ValueError(
            f"Unsupported provider: {provider} for model {model_name}. "
            f"Currently supported providers: openai, anthropic, ollama"
        )
