"""Configuration loader for the Enterprise Document Q&A system."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AzureAIFoundryConfig(BaseSettings):
    """Azure AI Foundry configuration."""
    
    endpoint: str = Field(..., alias="AZURE_AI_FOUNDRY_ENDPOINT")
    key: str = Field(..., alias="AZURE_AI_FOUNDRY_KEY")
    gpt_deployment_name: str = Field(..., alias="GPT_DEPLOYMENT_NAME")
    embedding_deployment_name: str = Field(..., alias="EMBEDDING_DEPLOYMENT_NAME")
    api_version: str = Field(default="2024-08-01-preview", alias="AZURE_OPENAI_API_VERSION")
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")


class AzureSearchConfig(BaseSettings):
    """Azure AI Search configuration."""
    
    endpoint: str = Field(..., alias="AZURE_SEARCH_ENDPOINT")
    key: str = Field(..., alias="AZURE_SEARCH_KEY")
    index_name: str = Field(..., alias="AZURE_SEARCH_INDEX_NAME")
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")


class DocumentProcessingConfig(BaseSettings):
    """Document processing configuration."""
    
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    max_retrieval_results: int = Field(default=5, alias="MAX_RETRIEVAL_RESULTS")
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")


class RAGConfig(BaseSettings):
    """RAG configuration."""
    
    temperature: float = Field(default=0.7, alias="TEMPERATURE")
    max_tokens: int = Field(default=1000, alias="MAX_TOKENS")
    system_prompt_path: Optional[str] = Field(default=None, alias="SYSTEM_PROMPT_PATH")
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")


class AppConfig(BaseSettings):
    """Application configuration."""
    
    app_name: str = Field(default="Enterprise Document Q&A", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    enable_telemetry: bool = Field(default=True, alias="ENABLE_TELEMETRY")
    
    # Advanced settings
    enable_semantic_ranking: bool = Field(default=True, alias="ENABLE_SEMANTIC_RANKING")
    enable_hybrid_search: bool = Field(default=True, alias="ENABLE_HYBRID_SEARCH")
    vector_similarity: str = Field(default="cosine", alias="VECTOR_SIMILARITY")
    query_type: str = Field(default="semantic", alias="QUERY_TYPE")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")


class Config:
    """Main configuration class that loads all settings."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config.yaml file. Defaults to ./config.yaml
        """
        self.config_path = config_path or Path("config.yaml")
        
        # Load environment-based configs
        self.ai_foundry = AzureAIFoundryConfig()
        self.search = AzureSearchConfig()
        self.document_processing = DocumentProcessingConfig()
        self.rag = RAGConfig()
        self.app = AppConfig()
        
        # Load YAML config
        self.yaml_config = self._load_yaml_config()
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value from YAML.
        
        Args:
            key: Dot-separated key path (e.g., "document_processing.chunking.strategy")
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.yaml_config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_prompt(self, prompt_name: str) -> str:
        """
        Get prompt template from config.
        
        Args:
            prompt_name: Name of the prompt (e.g., "system_prompt", "rag_prompt")
        
        Returns:
            Prompt template string
        """
        return self.get(f"prompts.{prompt_name}", "")
    
    def validate(self) -> bool:
        """
        Validate that all required configurations are present.
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        # Check Azure AI Foundry config
        if not self.ai_foundry.endpoint:
            raise ValueError("AZURE_AI_FOUNDRY_ENDPOINT is required")
        if not self.ai_foundry.key:
            raise ValueError("AZURE_AI_FOUNDRY_KEY is required")
        if not self.ai_foundry.gpt_deployment_name:
            raise ValueError("GPT_DEPLOYMENT_NAME is required")
        if not self.ai_foundry.embedding_deployment_name:
            raise ValueError("EMBEDDING_DEPLOYMENT_NAME is required")
        
        # Check Azure Search config
        if not self.search.endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT is required")
        if not self.search.key:
            raise ValueError("AZURE_SEARCH_KEY is required")
        if not self.search.index_name:
            raise ValueError("AZURE_SEARCH_INDEX_NAME is required")
        
        return True
    
    def __repr__(self) -> str:
        """String representation of config (without sensitive data)."""
        return (
            f"Config(\n"
            f"  AI Foundry Endpoint: {self.ai_foundry.endpoint}\n"
            f"  Search Endpoint: {self.search.endpoint}\n"
            f"  Index Name: {self.search.index_name}\n"
            f"  Environment: {self.app.environment}\n"
            f")"
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance (singleton).
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
        _config.validate()
    return _config


def reload_config() -> Config:
    """
    Reload configuration from files.
    
    Returns:
        New Config instance
    """
    global _config
    _config = Config()
    _config.validate()
    return _config


if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    print(config)
    print(f"\nSystem Prompt:\n{config.get_prompt('system_prompt')}")
