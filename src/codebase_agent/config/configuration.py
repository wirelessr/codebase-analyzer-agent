"""Configuration management for the AutoGen Codebase Understanding Agent.

This module provides secure and flexible configuration management supporting multiple
OpenAI-compatible API providers including OpenAI, OpenRouter, and LiteLLM.

Note: This implementation relies on AutoGen 0.7.4's internal model definitions
(_MODEL_TOKEN_LIMITS) for fuzzy model matching and token limit detection.
The AutoGen version is pinned to ensure consistent behavior.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

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
        "OPENAI_MODEL": "Model name to use for analysis",
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
        "litellm": "http://localhost:4000",
    }

    def __init__(self, project_root: Path | None = None):
        """Initialize configuration manager.

        Args:
            project_root: Path to project root directory. If None, uses current directory.
        """
        self.project_root = project_root or Path.cwd()
        self.env_file = self.project_root / ".env"
        self._config: dict[str, str] = {}
        self._is_loaded = False
        self.logger = logging.getLogger(__name__)

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
                logger.warning(
                    f"No .env file found at {self.env_file}. Using system environment only."
                )

            # Load all environment variables into our config
            self._config = dict(os.environ)
            self._is_loaded = True

            logger.debug(f"Configuration loaded with {len(self._config)} variables")

        except Exception as e:
            raise ConfigurationError(f"Failed to load environment configuration: {e}")

    def validate_configuration(self) -> list[str]:
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
            missing_keys.append(
                "OPENAI_API_KEY (invalid format - should start with 'sk-' or 'sk-or-')"
            )

        # Validate base URL format
        base_url = self._config.get("OPENAI_BASE_URL", "")
        if base_url and not self._is_valid_url_format(base_url):
            missing_keys.append("OPENAI_BASE_URL (invalid URL format)")

        # Validate numeric values
        for key in [
            "MODEL_TEMPERATURE",
            "MAX_TOKENS",
            "REQUEST_TIMEOUT",
            "AGENT_TIMEOUT",
            "MAX_SHELL_OUTPUT_SIZE",
        ]:
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
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in validation_errors
            )
            raise ConfigurationError(error_msg)

        try:
            return LLMConfig(
                api_key=self._config["OPENAI_API_KEY"],
                base_url=self._config["OPENAI_BASE_URL"],
                model=self._config["OPENAI_MODEL"],
                temperature=float(self._config.get("MODEL_TEMPERATURE", "0.1")),
                max_tokens=int(self._config.get("MAX_TOKENS", "4000")),
                timeout=int(self._config.get("REQUEST_TIMEOUT", "60")),
            )
        except (ValueError, KeyError) as e:
            raise ConfigurationError(f"Failed to create LLM configuration: {e}")

    def get_autogen_config(self) -> dict[str, Any]:
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

        Always uses the original model name for API authentication, but intelligently
        matches model_info from AutoGen's built-in model definitions when possible.

        Returns:
            OpenAIChatCompletionClient instance.
        """
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        llm_config = self.get_llm_config()

        # Use AutoGen's built-in max_tokens if available, otherwise use config
        max_tokens = (
            self._get_autogen_max_tokens(llm_config.model) or llm_config.max_tokens
        )

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
            # If AutoGen doesn't recognize the model, try to find matching model_info
            if "model_info is required" in str(e):
                self.logger.info(
                    f"Model '{llm_config.model}' not in AutoGen's built-in list. Finding compatible model_info..."
                )

                # Find a compatible AutoGen model to copy its model_info
                compatible_model = self._find_compatible_autogen_model(llm_config.model)
                if compatible_model:
                    # Get the model_info from the compatible AutoGen model
                    model_info = self._get_model_info_from_autogen_model(
                        compatible_model
                    )
                    if model_info:
                        self.logger.info(
                            f"✅ Using model_info from AutoGen model '{compatible_model}' for '{llm_config.model}'"
                        )
                        self.logger.debug(f"Model info: {model_info}")

                        return OpenAIChatCompletionClient(
                            model=llm_config.model,  # Keep original model name for API auth
                            api_key=llm_config.api_key,
                            base_url=llm_config.base_url,
                            max_tokens=max_tokens,
                            temperature=llm_config.temperature,
                            model_info=model_info,  # Use compatible model_info
                        )

                # If no compatible model found, use intelligent defaults
                self.logger.warning(
                    f"No compatible AutoGen model found for '{llm_config.model}'. Using intelligent defaults."
                )
                model_info = self._generate_model_info_from_name(llm_config.model)

                return OpenAIChatCompletionClient(
                    model=llm_config.model,  # Keep original model name
                    api_key=llm_config.api_key,
                    base_url=llm_config.base_url,
                    max_tokens=max_tokens,
                    temperature=llm_config.temperature,
                    model_info=model_info,
                )
            else:
                # Re-raise other errors
                raise

    def _find_compatible_autogen_model(self, model_name: str) -> str | None:
        """Find a compatible AutoGen model to copy model_info from.

        This method finds an AutoGen model that has similar characteristics to
        the user's model, so we can copy its model_info while keeping the original
        model name for API authentication.

        Args:
            model_name: The user's model name

        Returns:
            Compatible AutoGen model name or None
        """
        if not model_name or not model_name.strip():
            return None

        # Get all known AutoGen models
        try:
            from autogen_ext.models.openai import _model_info

            autogen_models = list(_model_info._MODEL_TOKEN_LIMITS.keys())
        except Exception:
            self.logger.warning("Could not access AutoGen model database")
            return None

        model_lower = model_name.lower().strip()

        # Remove common prefixes to get the core model name
        prefixes_to_remove = [
            "models/",
            "openai/",
            "anthropic/",
            "google/",
            "meta/",
            "github_copilot/",
            "azure/",
            "huggingface/",
            "together/",
            "replicate/",
            "anyscale/",
        ]

        cleaned_model = model_lower
        for prefix in prefixes_to_remove:
            if cleaned_model.startswith(prefix):
                cleaned_model = cleaned_model[len(prefix) :]
                break

        # Strategy 1: Find models from the same family
        compatible_models = []

        # Claude family
        if any(keyword in cleaned_model for keyword in ["claude"]):
            claude_models = [m for m in autogen_models if "claude" in m.lower()]
            if claude_models:
                # Prefer newer Claude versions for better capabilities
                if "sonnet-4" in cleaned_model or "claude-4" in cleaned_model:
                    # Look for Claude 4 models first
                    claude_4_models = [
                        m for m in claude_models if "sonnet-4" in m or "opus-4" in m
                    ]
                    if claude_4_models:
                        compatible_models.extend(
                            claude_4_models[:1]
                        )  # Take the first Claude 4 model
                    else:
                        # Fallback to latest Claude 3.5
                        claude_35_models = [m for m in claude_models if "3-5" in m]
                        if claude_35_models:
                            compatible_models.extend(claude_35_models[:1])
                elif "3.5" in cleaned_model or "3-5" in cleaned_model:
                    claude_35_models = [m for m in claude_models if "3-5" in m]
                    if claude_35_models:
                        compatible_models.extend(claude_35_models[:1])
                elif "3" in cleaned_model:
                    claude_3_models = [
                        m for m in claude_models if "3-" in m and "3-5" not in m
                    ]
                    if claude_3_models:
                        compatible_models.extend(claude_3_models[:1])
                else:
                    # Generic Claude - use latest available
                    compatible_models.extend(claude_models[:1])

        # GPT family
        elif any(keyword in cleaned_model for keyword in ["gpt", "openai"]):
            gpt_models = [m for m in autogen_models if "gpt" in m.lower()]
            if gpt_models:
                if "gpt-5" in cleaned_model:
                    gpt_5_models = [m for m in gpt_models if "gpt-5" in m]
                    compatible_models.extend(gpt_5_models[:1])
                elif "gpt-4" in cleaned_model:
                    gpt_4_models = [m for m in gpt_models if "gpt-4" in m]
                    # Prefer GPT-4o or turbo variants
                    gpt_4o_models = [m for m in gpt_4_models if "o" in m]
                    if gpt_4o_models:
                        compatible_models.extend(gpt_4o_models[:1])
                    else:
                        compatible_models.extend(gpt_4_models[:1])
                elif "gpt-3.5" in cleaned_model:
                    gpt_35_models = [m for m in gpt_models if "gpt-3.5" in m]
                    compatible_models.extend(gpt_35_models[:1])
                else:
                    # Generic GPT - use latest GPT-4
                    gpt_4_models = [m for m in gpt_models if "gpt-4" in m]
                    compatible_models.extend(gpt_4_models[:1])

        # Gemini family
        elif any(keyword in cleaned_model for keyword in ["gemini", "google"]):
            gemini_models = [m for m in autogen_models if "gemini" in m.lower()]
            if gemini_models:
                if "2.0" in cleaned_model:
                    gemini_2_models = [m for m in gemini_models if "2.0" in m]
                    compatible_models.extend(gemini_2_models[:1])
                elif "1.5" in cleaned_model:
                    gemini_15_models = [m for m in gemini_models if "1.5" in m]
                    compatible_models.extend(gemini_15_models[:1])
                else:
                    compatible_models.extend(gemini_models[:1])

        # Llama family
        elif any(keyword in cleaned_model for keyword in ["llama", "meta"]):
            llama_models = [m for m in autogen_models if "llama" in m.lower()]
            if llama_models:
                compatible_models.extend(llama_models[:1])

        # Strategy 2: If no family match, use a reasonable default
        if not compatible_models:
            # Default to a popular, well-supported model
            default_options = [
                "gpt-4o-2024-11-20",
                "claude-3-5-sonnet-20241022",
                "gpt-4-turbo-2024-04-09",
                "gemini-2.0-flash",
            ]
            for default_model in default_options:
                if default_model in autogen_models:
                    compatible_models.append(default_model)
                    break

        return compatible_models[0] if compatible_models else None

    def _get_model_info_from_autogen_model(
        self, autogen_model: str
    ) -> dict[str, Any] | None:
        """Get model_info from an AutoGen model by creating a temporary client.

        Args:
            autogen_model: The AutoGen model name to get info from

        Returns:
            Model info dictionary or None if failed
        """
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient

            # Create a temporary client to extract model_info
            temp_client = OpenAIChatCompletionClient(
                model=autogen_model,
                api_key="dummy",  # We won't make actual API calls
                base_url="http://dummy",
            )

            # Extract model_info from the client
            if hasattr(temp_client, "model_info"):
                return dict(temp_client.model_info)
            else:
                return None

        except Exception as e:
            self.logger.debug(
                f"Could not extract model_info from '{autogen_model}': {e}"
            )
            return None

    def _generate_model_info_from_name(self, model_name: str) -> dict[str, Any]:
        """Generate reasonable model_info based on model name patterns.

        This is a fallback when no compatible AutoGen model is found.

        Args:
            model_name: The model name to analyze

        Returns:
            Dictionary with inferred model capabilities
        """
        model_lower = model_name.lower()

        # Conservative defaults
        model_info = {
            "family": "openai",
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }

        # Adjust based on model name patterns
        if "claude" in model_lower:
            model_info.update(
                {
                    "family": "claude",
                    "vision": any(
                        v in model_lower for v in ["4", "3.5", "3-5"]
                    ),  # Claude 3.5+ has vision
                    "function_calling": True,
                    "structured_output": any(
                        v in model_lower for v in ["4", "3.5", "3-5"]
                    ),
                }
            )
        elif "gpt" in model_lower:
            model_info.update(
                {
                    "family": "gpt-4" if "gpt-4" in model_lower else "openai",
                    "vision": "gpt-4" in model_lower or "gpt-5" in model_lower,
                    "structured_output": any(
                        v in model_lower for v in ["gpt-4", "gpt-5"]
                    ),
                }
            )
        elif "gemini" in model_lower:
            model_info.update(
                {
                    "family": "gemini",
                    "vision": any(v in model_lower for v in ["1.5", "2.0"]),
                    "structured_output": "2.0" in model_lower,
                }
            )

        return model_info

    def _try_fuzzy_model_matching(self, model_name: str) -> str | None:
        """Legacy method - now returns None since we don't change model names.

        Args:
            model_name: The model name to match.

        Returns:
            None (we no longer change model names)
        """
        return None

    def _get_autogen_max_tokens(self, model_name: str) -> int | None:
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

    def get_model_info(self) -> dict[str, Any]:
        """Get model information configuration for AutoGen API.

        This method now tries to use compatible AutoGen model_info when possible,
        falling back to name-based inference as a last resort.

        Returns:
            Dictionary with model capabilities and settings.
        """
        if not self._is_loaded:
            self.load_environment()

        model_name = self._config.get("OPENAI_MODEL", "")
        if not model_name:
            return {
                "family": "openai",
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": False,
            }

        # Try to find a compatible AutoGen model and use its model_info
        compatible_model = self._find_compatible_autogen_model(model_name)
        if compatible_model:
            model_info = self._get_model_info_from_autogen_model(compatible_model)
            if model_info:
                self.logger.info(
                    f"Using model_info from compatible AutoGen model '{compatible_model}' for '{model_name}'"
                )
                return model_info

        # Fallback to name-based inference
        self.logger.info(f"Using name-based model_info inference for '{model_name}'")
        return self._generate_model_info_from_name(model_name)

    def get_agent_config(self) -> dict[str, Any]:
        """Get agent-specific configuration settings.

        Returns:
            Dictionary with agent behavior settings.
        """
        if not self._is_loaded:
            self.load_environment()

        return {
            "agent_timeout": int(self._config.get("AGENT_TIMEOUT", "300")),
            "max_shell_output_size": int(
                self._config.get("MAX_SHELL_OUTPUT_SIZE", "10000")
            ),
            "debug": self._config.get("DEBUG", "false").lower() == "true",
            "allowed_working_directory": self._config.get(
                "ALLOWED_WORKING_DIRECTORY", ""
            ),
            "log_level": self._config.get("LOG_LEVEL", "INFO"),
        }

    def get_config_value(self, key: str, default: str | None = None) -> str | None:
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
            with open(env_example) as src, open(self.env_file, "w") as dst:
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
            instructions.extend(
                [
                    "1. Create .env file:",
                    "   cp .env.example .env",
                    "",
                    "2. Edit .env file with your API configuration:",
                ]
            )
        else:
            instructions.extend(
                [
                    f"1. Edit your .env file at {self.env_file}:",
                ]
            )

        instructions.extend(
            [
                "",
                "Required configuration:",
            ]
        )

        for key in missing_keys:
            instructions.append(f"   - {key}")

        instructions.extend(
            [
                "",
                "Common API provider examples:",
                "",
                "OpenAI (recommended models):",
                "   OPENAI_API_KEY=sk-your_openai_key",
                "   OPENAI_BASE_URL=https://api.openai.com/v1",
                "   OPENAI_MODEL=gpt-4o-2024-11-20",
                "",
                "OpenRouter (use exact AutoGen model names):",
                "   OPENAI_API_KEY=sk-or-your_openrouter_key",
                "   OPENAI_BASE_URL=https://openrouter.ai/api/v1",
                "   OPENAI_MODEL=gpt-4o-2024-11-20",
                "",
                "Anthropic via OpenRouter:",
                "   OPENAI_API_KEY=sk-or-your_openrouter_key",
                "   OPENAI_BASE_URL=https://openrouter.ai/api/v1",
                "   OPENAI_MODEL=claude-3-5-sonnet-20241022",
                "",
                "GitHub Copilot (via LiteLLM):",
                "   OPENAI_API_KEY=your_github_token",
                "   OPENAI_BASE_URL=http://localhost:4000/v1",
                "   OPENAI_MODEL=github_copilot/claude-sonnet-4",
                "",
                "🎯 IMPORTANT: Use AutoGen's supported model names for best results!",
                "   The system will try to match your model name to AutoGen's built-in models.",
                "   Supported models include: gpt-4o-*, claude-*-*, gemini-*-*, o1-*, etc.",
                "",
                "❌ Manual model configuration is no longer needed:",
                "   MODEL_FAMILY, MODEL_VISION, etc. are automatically determined from model names.",
            ]
        )

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
