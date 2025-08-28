"""Configuration management for the AutoGen Codebase Understanding Agent.

This module provides secure and flexible configuration management supporting multiple
OpenAI-compatible API providers including OpenAI, OpenRouter, and LiteLLM.

Note: This implementation relies on AutoGen 0.7.4's internal model definitions
(_MODEL_TOKEN_LIMITS) for fuzzy model matching and token limit detection.
The AutoGen version is pinned to ensure consistent behavior.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM API settings."""
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 60


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigurationManager:
    """Manages environment configuration and LLM settings for AutoGen agents.
    
    Supports multiple OpenAI-compatible API providers and provides validation
    with clear error messages for missing or invalid configuration.
    """
    
    # Required environment variables
    REQUIRED_KEYS = {
        "OPENAI_API_KEY": "API key for OpenAI-compatible service",
        "OPENAI_BASE_URL": "Base URL for API endpoint", 
        "OPENAI_MODEL": "Model name to use for analysis"
    }
    
    # Optional environment variables with defaults
    OPTIONAL_KEYS = {
        "MODEL_TEMPERATURE": "0.1",
        "MAX_TOKENS": "4000",
        "REQUEST_TIMEOUT": "60",
        "AGENT_TIMEOUT": "300",
        "MAX_SHELL_OUTPUT_SIZE": "10000",
        "LOG_LEVEL": "INFO",
        "DEBUG": "false",
        "ALLOWED_WORKING_DIRECTORY": "",
        "MODEL_FAMILY": "openai",
        "MODEL_VISION": "false",
        "MODEL_FUNCTION_CALLING": "true",
        "MODEL_JSON_OUTPUT": "true",
        "MODEL_STRUCTURED_OUTPUT": "false",
    }
    
    # Default values for common API providers
    DEFAULT_BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1", 
        "litellm": "http://localhost:4000"
    }
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            project_root: Path to project root directory. If None, uses current directory.
        """
        self.project_root = project_root or Path.cwd()
        self.env_file = self.project_root / ".env"
        self._config: Dict[str, str] = {}
        self._is_loaded = False
        
    def load_environment(self) -> None:
        """Load environment variables from .env file and system environment.
        
        Raises:
            ConfigurationError: If .env file exists but cannot be loaded.
        """
        try:
            # Load from .env file if it exists
            if self.env_file.exists():
                success = load_dotenv(self.env_file)
                if not success:
                    logger.warning(f"Failed to load .env file from {self.env_file}")
                else:
                    logger.info(f"Loaded configuration from {self.env_file}")
            else:
                logger.warning(f"No .env file found at {self.env_file}. Using system environment only.")
                
            # Load all environment variables into our config
            self._config = dict(os.environ)
            self._is_loaded = True
            
            logger.debug(f"Configuration loaded with {len(self._config)} variables")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load environment configuration: {e}")
    
    def validate_configuration(self) -> List[str]:
        """Validate required configuration values.
        
        Returns:
            List of missing or invalid configuration keys.
        """
        if not self._is_loaded:
            self.load_environment()
            
        missing_keys = []
        
        # Check required keys
        for key, description in self.REQUIRED_KEYS.items():
            value = self._config.get(key)
            if not value or value.strip() == "":
                missing_keys.append(f"{key} ({description})")
                
        # Validate API key format
        api_key = self._config.get("OPENAI_API_KEY", "")
        if api_key and not self._is_valid_api_key_format(api_key):
            missing_keys.append("OPENAI_API_KEY (invalid format - should start with 'sk-' or 'sk-or-')")
            
        # Validate base URL format
        base_url = self._config.get("OPENAI_BASE_URL", "")
        if base_url and not self._is_valid_url_format(base_url):
            missing_keys.append("OPENAI_BASE_URL (invalid URL format)")
            
        # Validate numeric values
        for key in ["MODEL_TEMPERATURE", "MAX_TOKENS", "REQUEST_TIMEOUT", "AGENT_TIMEOUT", "MAX_SHELL_OUTPUT_SIZE"]:
            value = self._config.get(key)
            if value and not self._is_valid_numeric(value):
                missing_keys.append(f"{key} (must be a valid number)")
                
        return missing_keys
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration for AutoGen agents.
        
        Returns:
            LLMConfig object with validated settings.
            
        Raises:
            ConfigurationError: If configuration is invalid or missing.
        """
        validation_errors = self.validate_configuration()
        if validation_errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in validation_errors)
            raise ConfigurationError(error_msg)
            
        try:
            return LLMConfig(
                api_key=self._config["OPENAI_API_KEY"],
                base_url=self._config["OPENAI_BASE_URL"],
                model=self._config["OPENAI_MODEL"],
                temperature=float(self._config.get("MODEL_TEMPERATURE", "0.1")),
                max_tokens=int(self._config.get("MAX_TOKENS", "4000")),
                timeout=int(self._config.get("REQUEST_TIMEOUT", "60"))
            )
        except (ValueError, KeyError) as e:
            raise ConfigurationError(f"Failed to create LLM configuration: {e}")
    
    def get_autogen_config(self) -> Dict[str, Any]:
        """Get configuration dictionary for AutoGen agents.
        
        Returns:
            Dictionary compatible with AutoGen's config format.
        """
        llm_config = self.get_llm_config()
        
        return {
            "config_list": [
                {
                    "model": llm_config.model,
                    "api_key": llm_config.api_key,
                    "base_url": llm_config.base_url,
                    "api_type": "openai",
                }
            ],
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens,
            "timeout": llm_config.timeout,
        }
    
    def get_model_client(self):
        """Get ChatCompletionClient for new AutoGen API.
        
        Uses AutoGen's built-in model info for known models when possible,
        falls back to manual configuration for unknown models.
        
        Returns:
            OpenAIChatCompletionClient instance.
        """
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        llm_config = self.get_llm_config()
        
        # Use AutoGen's built-in max_tokens if available, otherwise use config
        max_tokens = self._get_autogen_max_tokens(llm_config.model) or llm_config.max_tokens
        
        # First try to create client without model_info to use AutoGen's built-in detection
        try:
            return OpenAIChatCompletionClient(
                model=llm_config.model,
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                max_tokens=max_tokens,
                temperature=llm_config.temperature,
            )
        except Exception as e:
            # If AutoGen doesn't recognize the model, try fuzzy matching
            if "model_info is required" in str(e):
                recognized_model = self._try_fuzzy_model_matching(llm_config.model)
                if recognized_model:
                    # Update max_tokens for the recognized model
                    max_tokens = self._get_autogen_max_tokens(recognized_model) or llm_config.max_tokens
                    try:
                        return OpenAIChatCompletionClient(
                            model=recognized_model,
                            api_key=llm_config.api_key,
                            base_url=llm_config.base_url,
                            max_tokens=max_tokens,
                            temperature=llm_config.temperature,
                        )
                    except:
                        pass  # Fall back to manual model_info
                
                # Fall back to manual model_info
                model_info = self.get_model_info()
                return OpenAIChatCompletionClient(
                    model=llm_config.model,
                    api_key=llm_config.api_key,
                    base_url=llm_config.base_url,
                    max_tokens=max_tokens,
                    temperature=llm_config.temperature,
                    model_info=model_info,
                )
            else:
                # Re-raise other errors
                raise
    
    def _try_fuzzy_model_matching(self, model_name: str) -> Optional[str]:
        """Try to match unknown model names to known AutoGen models.
        
        Args:
            model_name: The model name to match.
            
        Returns:
            Recognized model name or None if no match found.
        """
        # Get all known models from AutoGen instead of hardcoding
        try:
            from autogen_ext.models.openai import _model_info
            known_models = list(_model_info._MODEL_TOKEN_LIMITS.keys())
        except Exception:
            # Fallback to hardcoded list if AutoGen import fails
            known_models = [
                'gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 
                'gpt-3.5-turbo', 'gpt-3.5-turbo-16k',
                'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku',
                'claude-3-5-sonnet', 'claude-3-5-haiku',
                'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'
            ]
        
        model_lower = model_name.lower().strip()
        
        # Return None for empty or whitespace-only strings
        if not model_lower:
            return None
        
        # Remove common prefixes (iterate until no more prefixes can be removed)
        prefixes = ['models/', 'openai/', 'anthropic/', 'google/', 'gpt-', 'github_copilot/']
        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if model_lower.startswith(prefix):
                    model_lower = model_lower[len(prefix):]
                    changed = True
                    break
        
        # Return None if nothing left after prefix removal
        if not model_lower:
            return None
        
        # Try exact match first
        for known in known_models:
            if model_lower == known.lower():
                return known
        
        # Try partial matching with specific model names (e.g., claude-sonnet-4 -> claude-sonnet-4-20250514)
        for known in known_models:
            known_lower = known.lower()
            
            # Handle versioned models: exact model name with date suffix
            # e.g., claude-sonnet-4 -> claude-sonnet-4-20250514
            if known_lower.startswith(model_lower + '-') and model_lower.count('-') >= 2:
                return known
                
            # Handle case where model_lower is a substring at word boundaries
            # e.g., gpt-4 -> gpt-4-turbo-2024-04-09
            if model_lower in known_lower.split('-'):
                # Check if it's a meaningful match (not just single characters)
                if len(model_lower.replace('-', '')) > 2:
                    return known

        # Try partial matching with model parts
        for known in known_models:
            known_parts = known.lower().split('-')
            model_parts = model_lower.split('-')
            
            # Check if all model parts are in known model
            if all(part in known_parts for part in model_parts if part):
                return known
                
            # Check if model contains key parts of known model
            if len(known_parts) >= 2:
                key_parts = known_parts[:2]  # e.g., ['gpt', '4'] from 'gpt-4'
                if all(part in model_lower for part in key_parts):
                    return known
        
        # Special handling for some common cases (as fallback only)
        # Handle claude-opus variants -> claude-3-opus (find the actual opus model)
        if 'claude' in model_lower and 'opus' in model_lower:
            for known in known_models:
                if 'opus' in known.lower():
                    return known
        
        # Handle claude-sonnet variants -> claude-3-5-sonnet (only if no specific match found)
        if 'claude' in model_lower and 'sonnet' in model_lower:
            for known in known_models:
                if 'sonnet' in known.lower():
                    return known
        
        # Handle claude-haiku variants -> claude-3-5-haiku
        if 'claude' in model_lower and 'haiku' in model_lower:
            for known in known_models:
                if 'haiku' in known.lower():
                    return known
        
        return None
    
    def _get_autogen_max_tokens(self, model_name: str) -> Optional[int]:
        """Get max_tokens from AutoGen's built-in model information.
        
        Args:
            model_name: The model name to look up.
            
        Returns:
            max_tokens limit if found, None otherwise.
        """
        try:
            from autogen_ext.models.openai import _model_info
            return _model_info.get_token_limit(model_name)
        except Exception:
            # If AutoGen doesn't have the model or any error occurs,
            # return None to fall back to manual configuration
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information configuration for AutoGen API.
        
        This method is used as a fallback when AutoGen doesn't recognize 
        the model name and fuzzy matching fails.
        
        Returns:
            Dictionary with model capabilities and settings.
        """
        if not self._is_loaded:
            self.load_environment()
            
        return {
            "family": self._config.get("MODEL_FAMILY", "openai"),
            "vision": self._config.get("MODEL_VISION", "false").lower() == "true",
            "function_calling": self._config.get("MODEL_FUNCTION_CALLING", "true").lower() == "true",
            "json_output": self._config.get("MODEL_JSON_OUTPUT", "true").lower() == "true",
            "structured_output": self._config.get("MODEL_STRUCTURED_OUTPUT", "false").lower() == "true",
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent-specific configuration settings.
        
        Returns:
            Dictionary with agent behavior settings.
        """
        if not self._is_loaded:
            self.load_environment()
            
        return {
            "agent_timeout": int(self._config.get("AGENT_TIMEOUT", "300")),
            "max_shell_output_size": int(self._config.get("MAX_SHELL_OUTPUT_SIZE", "10000")),
            "debug": self._config.get("DEBUG", "false").lower() == "true",
            "allowed_working_directory": self._config.get("ALLOWED_WORKING_DIRECTORY", ""),
            "log_level": self._config.get("LOG_LEVEL", "INFO"),
        }
    
    def get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a specific configuration value.
        
        Args:
            key: Configuration key to retrieve.
            default: Default value if key is not found.
            
        Returns:
            Configuration value or default.
        """
        if not self._is_loaded:
            self.load_environment()
            
        return self._config.get(key, default)
    
    def create_env_file_if_missing(self) -> bool:
        """Create .env file from .env.example if it doesn't exist.
        
        Returns:
            True if .env file was created, False if it already exists.
        """
        if self.env_file.exists():
            return False
            
        env_example = self.project_root / ".env.example"
        if not env_example.exists():
            logger.warning("No .env.example file found to copy from")
            return False
            
        try:
            # Copy .env.example to .env
            with open(env_example, 'r') as src, open(self.env_file, 'w') as dst:
                dst.write(src.read())
            logger.info(f"Created .env file from .env.example at {self.env_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create .env file: {e}")
            return False
    
    def get_setup_instructions(self) -> str:
        """Get user-friendly setup instructions for missing configuration.
        
        Returns:
            Formatted string with setup instructions.
        """
        missing_keys = self.validate_configuration()
        if not missing_keys:
            return "✅ Configuration is valid and complete!"
            
        instructions = [
            "❌ Configuration setup required:",
            "",
        ]
        
        # Check if .env file exists
        if not self.env_file.exists():
            instructions.extend([
                f"1. Create .env file:",
                f"   cp .env.example .env",
                "",
                f"2. Edit .env file with your API configuration:",
            ])
        else:
            instructions.extend([
                f"1. Edit your .env file at {self.env_file}:",
            ])
            
        instructions.extend([
            "",
            "Required configuration:",
        ])
        
        for key in missing_keys:
            instructions.append(f"   - {key}")
            
        instructions.extend([
            "",
            "Common API provider examples:",
            "",
            "OpenAI:",
            "   OPENAI_API_KEY=sk-your_openai_key",
            "   OPENAI_BASE_URL=https://api.openai.com/v1",
            "   OPENAI_MODEL=gpt-4",
            "   MODEL_FAMILY=openai",
            "   MODEL_FUNCTION_CALLING=true",
            "",
            "OpenRouter:",
            "   OPENAI_API_KEY=sk-or-your_openrouter_key", 
            "   OPENAI_BASE_URL=https://openrouter.ai/api/v1",
            "   OPENAI_MODEL=openai/gpt-4",
            "   MODEL_FAMILY=openai",
            "",
            "LiteLLM Proxy:",
            "   OPENAI_API_KEY=your_api_key",
            "   OPENAI_BASE_URL=http://localhost:4000",
            "   OPENAI_MODEL=gpt-4",
            "   MODEL_FAMILY=openai",
            "",
            "Optional model capabilities (defaults shown):",
            "   MODEL_VISION=false",
            "   MODEL_FUNCTION_CALLING=true", 
            "   MODEL_JSON_OUTPUT=true",
            "   MODEL_STRUCTURED_OUTPUT=false",
        ])
        
        return "\n".join(instructions)
    
    def _is_valid_api_key_format(self, api_key: str) -> bool:
        """Check if API key has a valid format.
        
        Args:
            api_key: API key to validate.
            
        Returns:
            True if format appears valid.
        """
        if not api_key:
            return False
            
        # Common API key prefixes
        valid_prefixes = ["sk-", "sk-or-", "sk-ant-", "Bearer ", "sk-litellm-"]
        return any(api_key.startswith(prefix) for prefix in valid_prefixes)
    
    def _is_valid_url_format(self, url: str) -> bool:
        """Check if URL has a valid format.
        
        Args:
            url: URL to validate.
            
        Returns:
            True if format appears valid.
        """
        if not url:
            return False
            
        return url.startswith(("http://", "https://"))
    
    def _is_valid_numeric(self, value: str) -> bool:
        """Check if value can be converted to a number.
        
        Args:
            value: Value to check.
            
        Returns:
            True if value is numeric.
        """
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
