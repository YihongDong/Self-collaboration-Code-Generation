import os
from dataclasses import dataclass, field

# Read model config from environment (set in .env)
_DEFAULT_MODEL = os.environ.get("MODEL", "moonshotai/kimi-k2.5")
_DEFAULT_BASE_URL = os.environ.get("BASE_URL", "https://openrouter.ai/api/v1")
_DEFAULT_API_KEY_ENV = os.environ.get("API_KEY_ENV", "OPENROUTER_API_KEY")


@dataclass
class ModelConfig:
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0
    top_p: float = 0.95

    def __post_init__(self):
        if not self.model:
            self.model = _DEFAULT_MODEL
        if not self.base_url:
            self.base_url = _DEFAULT_BASE_URL
        if not self.api_key_env:
            self.api_key_env = _DEFAULT_API_KEY_ENV


ANALYST_CONFIG = ModelConfig(max_tokens=8192)
CODER_CONFIG = ModelConfig(max_tokens=8192)
TESTER_CONFIG = ModelConfig(max_tokens=8192)


def openai_config(model="gpt-3.5-turbo-0301", max_tokens=512, temperature=0.0, top_p=0.95):
    """Create a ModelConfig compatible with the original OpenAI mode."""
    return ModelConfig(
        model=model,
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
    )
