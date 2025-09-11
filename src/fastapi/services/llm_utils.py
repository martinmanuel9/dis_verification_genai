import os
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
import requests
# from langchain_anthropic import ChatAnthropic

# Disable LangSmith tracing to avoid rate limits
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_ENDPOINT"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""

def get_llm(model_name: str):
    """
    Unified LLM loader for OpenAI and Ollama models.
    """
    model_name = (model_name or "").strip()
    model_l = model_name.lower()
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    ollama_host = os.getenv("LLM_OLLAMA_HOST", "http://ollama:11434")
    
    # OpenAI Chat models (support any "gpt-*" as pass-through)
    if model_l.startswith("gpt") or model_l in ["gpt-oss"]:
        # Allow an override model name for GPT-OSS via env
        if model_l == "gpt-oss":
            model_name = os.getenv("OAI_OSS_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model_name, openai_api_key=openai_api_key, temperature=0.7)
    
    # # Anthropic Claude models (requires langchain-anthropic package)
    # elif model_name in ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]:
    #     try:
    #         anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    #         if not anthropic_api_key:
    #             raise ValueError(f"ANTHROPIC_API_KEY required for Claude models")
    #         from langchain_anthropic import ChatAnthropic
    #         return ChatAnthropic(model=model_name, anthropic_api_key=anthropic_api_key, temperature=0.7)
    #     except ImportError:
    #         raise ValueError(f"Claude models require 'langchain-anthropic' package. Install with: pip install langchain-anthropic")
    
    # Ollama models - handle both simple names and versioned names
    elif model_l.startswith("llama"):
        # Resolve to installed tag (single canonical LLaMA default)
        target = _resolve_ollama_model(model_name=model_name, base_url=ollama_host)
        return OllamaLLM(model=target, base_url=ollama_host, temperature=0.7)
    
    # elif model_name in ["mistral"]:
    #     return OllamaLLM(model="mistral", base_url=ollama_host, temperature=0.7)
    
    # elif model_name in ["gemma"]:
    #     return OllamaLLM(model="gemma", base_url=ollama_host, temperature=0.7)
    
    else:
        # Generic fallback: try serving via Ollama first (common for OSS models like mistral, qwen, gemma)
        try:
            return OllamaLLM(model=model_name, base_url=ollama_host, temperature=0.7)
        except Exception:
            # If that fails, and looks like gpt, try OpenAI (may still fail without key)
            if model_l.startswith("gpt"):
                return ChatOpenAI(model=model_name, openai_api_key=openai_api_key, temperature=0.7)
            raise ValueError(f"Unsupported model: {model_name}")


def _resolve_ollama_model(model_name: str, base_url: str) -> str:
    """Resolve requested Ollama model to an installed tag, with sensible defaults.

    - Maps generic aliases (llama → llama3)
    - Uses env overrides LLAMA31_TAG / LLAMA2_TAG when applicable
    - Attempts to match an installed tag from /api/tags; prefers lighter variants
    """
    name_raw = (model_name or "").strip()
    name_l = name_raw.lower()

    # Basic alias mapping (single default target for 'llama')
    alias_default = {
        "llama": os.getenv("LLAMA_DEFAULT_TAG", os.getenv("LLAMA31_TAG", "llama3.1:8b")),
        "llama3": os.getenv("LLAMA31_TAG", "llama3.1:8b"),
        "llama3.1": os.getenv("LLAMA31_TAG", "llama3.1:8b"),
    }
    candidate = alias_default.get(name_l, name_raw)

    # Try to read available tags from Ollama
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        if resp.ok:
            data = resp.json() or {}
            models = [m.get("name", "") for m in data.get("models", [])]
            models_l = [m.lower() for m in models]

            def pick(prefixes):
                for p in prefixes:
                    # Prefer 8b, then 7b, then others for 3.1/2
                    if p.endswith("3.1"):
                        prefs = [":8b", ":70b", ""]
                    elif p.endswith("2"):
                        prefs = [":7b", ":13b", ""]
                    else:
                        prefs = [""]
                    for suf in prefs:
                        tag = f"{p}{suf}".lower()
                        for i, m in enumerate(models_l):
                            if m == tag:
                                return models[i]
                            if m.startswith(tag):
                                return models[i]
                return None

            if name_l in ("llama", "llama3", "llama3.1"):
                match = pick(["llama3.1", "llama3"]) or pick(["llama3"])  
                if match:
                    return match

            # If requested candidate is present, return as-is
            if candidate.lower() in models_l:
                return candidate
    except Exception:
        pass

    # Fallback to candidate; caller should ensure tag exists (start script pulls OLLAMA_MODELS)
    return candidate
