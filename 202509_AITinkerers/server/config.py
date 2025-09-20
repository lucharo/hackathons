import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings and configuration."""
    
    def __init__(self):
        # CORS
        self.environment = os.getenv("ENVIRONMENT")
        self.cors_origins = self._get_cors_origins()
        self.cors_allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
        self.cors_allow_methods = self._get_list_from_env("CORS_ALLOW_METHODS", [])
        self.cors_allow_headers = self._get_list_from_env("CORS_ALLOW_HEADERS", [])
        
        # LLM Configuration
        self.default_llm_model = os.getenv("DEFAULT_LLM_MODEL")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        # self.default_max_tokens = int(os.getenv("DEFAULT_MAX_TOKENS", "8192")) if os.getenv("DEFAULT_MAX_TOKENS") else None
    
    def _get_cors_origins(self) -> list[str]:
        """Get CORS origins from environment variable or use defaults based on environment."""
        origins_env = os.getenv("CORS_ORIGINS")
        
        if origins_env:
            # Split by comma and strip whitespace
            return [origin.strip() for origin in origins_env.split(",")]
        
        else:
            return []
    
    def _get_list_from_env(self, env_var: str, default: list[str]) -> list[str]:
        """Get a list from environment variable, falling back to default."""
        env_value = os.getenv(env_var)
        if env_value:
            return [item.strip() for item in env_value.split(",")]
        return default
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

# Global settings instance
settings = Settings()
