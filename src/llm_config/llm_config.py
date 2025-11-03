
from dataclasses import dataclass
from typing import Dict, List, Optional
import os


@dataclass(frozen=True)
class ModelConfig:
    """Metadata describing a supported LLM."""

    model_id: str
    display_name: str
    description: str
    provider: str  # e.g. "openai", "anthropic"

    def __hash__(self):
        return hash(self.model_id)


# ============================================================================
# SINGLE SOURCE OF TRUTH FOR ALL SUPPORTED MODELS
# ============================================================================

MODEL_REGISTRY: Dict[str, ModelConfig] = {
    # --- OpenAI Models ---
    "gpt-4": ModelConfig(
        model_id="gpt-4",
        display_name="GPT-4",
        description="Most capable GPT-4 model for complex analysis and reasoning tasks",
        provider="openai",
    ),
    "gpt-4o": ModelConfig(
        model_id="gpt-4o",
        display_name="GPT-4o",
        description="Flagship multimodal OpenAI model with improved speed, cost, and vision support",
        provider="openai",
    ),
    "gpt-4o-mini": ModelConfig(
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        description="Lightweight GPT-4o variant optimized for cost-effective, high-volume workloads",
        provider="openai",
    ),
    "gpt-3.5-turbo": ModelConfig(
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5-Turbo",
        description="Fast and cost-effective model for general tasks and conversations",
        provider="openai",
    ),

    # --- Anthropic Models ---
    # "claude-3-5-haiku-20241022": ModelConfig(
    #     model_id="claude-3-5-haiku-20241022",
    #     display_name="Claude 3.5 Haiku",
    #     description="Latest Claude 3.5 Haiku with improved latency and translation capabilities",
    #     provider="anthropic",
    # ),
    # "claude-3-haiku-20240307": ModelConfig(
    #     model_id="claude-3-haiku-20240307",
    #     display_name="Claude 3 Haiku",
    #     description="Fast Claude model optimized for quick responses and efficiency",
    #     provider="anthropic",
    # ),
    # "claude-3-opus-20240229": ModelConfig(
    #     model_id="claude-3-opus-20240229",
    #     display_name="Claude 3 Opus",
    #     description="Anthropic's most capable Claude model for rigorous reasoning and complex drafting",
    #     provider="anthropic",
    # ),

    # --- Ollama Local Models (CPU-optimized, Minimal Memory Footprint) ---
    "llama3.2:1b": ModelConfig(
        model_id="llama3.2:1b",
        display_name="Llama 3.2 1B (Local)",
        description="Meta's smallest Llama model - Ultra-lightweight, CPU-optimized (1GB RAM, 1.3GB disk)",
        provider="ollama",
    ),
}


# ============================================================================
# CONVENIENCE MAPPINGS
# ============================================================================


# Display name (exact case) -> Model ID (for Streamlit compatibility)
MODEL_KEY_MAP: Dict[str, str] = {
    cfg.display_name: cfg.model_id
    for cfg in MODEL_REGISTRY.values()
}

# Model ID -> Description (for Streamlit compatibility)
MODEL_DESCRIPTIONS: Dict[str, str] = {
    cfg.model_id: cfg.description
    for cfg in MODEL_REGISTRY.values()
}

# Model ID -> Display Name
MODEL_ID_TO_DISPLAY: Dict[str, str] = {
    cfg.model_id: cfg.display_name
    for cfg in MODEL_REGISTRY.values()
}

# Display name (lowercase) -> Model ID (for case-insensitive lookups)
MODEL_DISPLAY_MAP: Dict[str, str] = {
    cfg.display_name.lower(): cfg.model_id
    for cfg in MODEL_REGISTRY.values()
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_model_config(model_name: Optional[str]) -> Optional[ModelConfig]:
    """
    Resolve a model by either its canonical ID (e.g. 'gpt-4o') or display name.

    Args:
        model_name: Model identifier (can be model_id or display_name, case-insensitive)

    Returns:
        ModelConfig if found, None otherwise

    Examples:
        >>> get_model_config("gpt-4")  # By ID
        ModelConfig(model_id="gpt-4", ...)

        >>> get_model_config("GPT-4")  # By display name
        ModelConfig(model_id="gpt-4", ...)

        >>> get_model_config("Claude 3 Opus")  # By display name
        ModelConfig(model_id="claude-3-opus-20240229", ...)
    """
    if not model_name:
        return None

    key = model_name.strip()

    # Try exact match on model ID
    if key in MODEL_REGISTRY:
        return MODEL_REGISTRY[key]

    # Try case-insensitive display name match
    lowered = key.lower()
    if lowered in MODEL_DISPLAY_MAP:
        canonical_id = MODEL_DISPLAY_MAP[lowered]
        return MODEL_REGISTRY[canonical_id]

    return None


def validate_model(model_name: Optional[str]) -> tuple[bool, str]:
    """
    Validate if a model is supported.

    Args:
        model_name: Model identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, "")
        If invalid: (False, "error message")
    """
    if not model_name:
        return False, "Model name is required"

    config = get_model_config(model_name)
    if not config:
        supported = ", ".join(MODEL_REGISTRY.keys())
        return False, f"Unsupported model: '{model_name}'. Supported models: {supported}"

    return True, ""


def get_models_by_provider(provider: str) -> List[ModelConfig]:
    """
    Return all models belonging to a specific provider.

    Args:
        provider: Provider name (e.g., "openai", "anthropic")

    Returns:
        List of ModelConfig objects for that provider
    """
    provider_l = provider.lower()
    return [
        cfg for cfg in MODEL_REGISTRY.values()
        if cfg.provider.lower() == provider_l
    ]


def list_supported_models() -> List[ModelConfig]:
    """Return all supported models."""
    return list(MODEL_REGISTRY.values())


def get_openai_models() -> List[ModelConfig]:
    """Return all OpenAI models."""
    return get_models_by_provider("openai")


def get_anthropic_models() -> List[ModelConfig]:
    """Return all Anthropic models."""
    return get_models_by_provider("anthropic")


def get_model_display_name(model_id: str) -> str:
    """Get display name for a model ID, returns model_id if not found."""
    return MODEL_ID_TO_DISPLAY.get(model_id, model_id)


# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

class LLMEnvironment:
    """Centralized environment configuration for LLM services."""

    def __init__(self):
        # Standardized API key names (without underscores for consistency)
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # LangChain settings
        self.langchain_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false")
        self.langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT", "")
        self.langchain_api_key = os.getenv("LANGCHAIN_API_KEY", "")

        # Model defaults
        self.default_temperature = float(os.getenv("LLM_DEFAULT_TEMPERATURE", "0.7"))
        self.default_max_tokens = int(os.getenv("LLM_DEFAULT_MAX_TOKENS", "2000"))

    def validate_provider_keys(self, provider: str) -> tuple[bool, str]:
        """
        Validate that API keys are configured for a provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic", "ollama")

        Returns:
            Tuple of (is_valid, error_message)
        """
        provider_l = provider.lower()

        if provider_l == "openai":
            if not self.openai_api_key:
                return False, "OPENAI_API_KEY environment variable is not set"
        elif provider_l == "anthropic":
            if not self.anthropic_api_key:
                return False, "ANTHROPIC_API_KEY environment variable is not set"
        elif provider_l == "ollama":
            # Ollama runs locally and doesn't require API keys
            return True, ""
        else:
            return False, f"Unknown provider: {provider}"

        return True, ""

    def validate_model(self, model_name: str) -> tuple[bool, str]:
        """
        Validate model and its required API keys.

        Args:
            model_name: Model identifier

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First validate model exists
        is_valid, error = validate_model(model_name)
        if not is_valid:
            return is_valid, error

        # Then validate API keys
        config = get_model_config(model_name)
        return self.validate_provider_keys(config.provider)


# Export singleton
llm_env = LLMEnvironment()


# ============================================================================
# MIGRATION HELPERS (for backward compatibility)
# ============================================================================

def get_model_configs_dict() -> Dict[str, Dict[str, str]]:
    """
    Return model configurations in the old format for backward compatibility.

    Returns:
        Dict mapping display_name to config dict
    """
    return {
        cfg.display_name: {
            "model_id": cfg.model_id,
            "display_name": cfg.display_name,
            "description": cfg.description,
            "provider": cfg.provider
        }
        for cfg in MODEL_REGISTRY.values()
    }


# Expose old format for backward compatibility
MODEL_CONFIGS = get_model_configs_dict()
