"""Unit tests for configuration management."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from codebase_agent.config.configuration import (
    ConfigurationManager,
    ConfigurationError,
    LLMConfig
)


class TestConfigurationManager:
    """Test suite for ConfigurationManager."""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def env_example_content(self):
        """Sample .env.example content."""
        return """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# Agent Configuration
AGENT_TIMEOUT=300
MAX_SHELL_OUTPUT_SIZE=10000
LOG_LEVEL=INFO
"""
    
    @pytest.fixture
    def valid_env_content(self):
        """Valid .env content for testing."""
        return """OPENAI_API_KEY=sk-test123456789
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
MODEL_TEMPERATURE=0.1
MAX_TOKENS=4000
REQUEST_TIMEOUT=60
"""
    
    def test_init_default_project_root(self):
        """Test initialization with default project root."""
        config_manager = ConfigurationManager()
        assert config_manager.project_root == Path.cwd()
        assert config_manager.env_file == Path.cwd() / ".env"
        assert not config_manager._is_loaded
    
    def test_init_custom_project_root(self, temp_project_root):
        """Test initialization with custom project root."""
        config_manager = ConfigurationManager(temp_project_root)
        assert config_manager.project_root == temp_project_root
        assert config_manager.env_file == temp_project_root / ".env"
    
    def test_load_environment_with_env_file(self, temp_project_root, valid_env_content):
        """Test loading environment from .env file."""
        # Create .env file
        env_file = temp_project_root / ".env"
        env_file.write_text(valid_env_content)
        
        # Clear any existing environment variables to ensure clean test
        env_vars_to_clear = ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", 
                            "MODEL_TEMPERATURE", "MAX_TOKENS", "REQUEST_TIMEOUT"]
        with patch.dict(os.environ, {}, clear=False):
            # Remove specific environment variables
            for var in env_vars_to_clear:
                os.environ.pop(var, None)
            
            config_manager = ConfigurationManager(temp_project_root)
            config_manager.load_environment()
            
            assert config_manager._is_loaded
            assert config_manager._config["OPENAI_API_KEY"] == "sk-test123456789"
            assert config_manager._config["OPENAI_BASE_URL"] == "https://api.openai.com/v1"
            assert config_manager._config["OPENAI_MODEL"] == "gpt-4"
    
    def test_load_environment_without_env_file(self, temp_project_root):
        """Test loading environment without .env file."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-env123456789",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-3.5-turbo"
        }, clear=True):
            config_manager = ConfigurationManager(temp_project_root)
            config_manager.load_environment()
            
            assert config_manager._is_loaded
            assert config_manager._config["OPENAI_API_KEY"] == "sk-env123456789"
            assert config_manager._config["OPENAI_MODEL"] == "gpt-3.5-turbo"
    
    def test_load_environment_file_load_failure(self, temp_project_root):
        """Test handling of .env file load failure."""
        # Create an empty .env file that should load successfully
        env_file = temp_project_root / ".env"
        env_file.write_text("")
        
        config_manager = ConfigurationManager(temp_project_root)
        # This should not raise an exception even if dotenv loading fails
        config_manager.load_environment()
        assert config_manager._is_loaded
    
    def test_validate_configuration_missing_required_keys(self, temp_project_root):
        """Test validation with missing required keys."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {}, clear=True):
            missing_keys = config_manager.validate_configuration()
            
            assert len(missing_keys) == 3  # All required keys missing
            assert any("OPENAI_API_KEY" in key for key in missing_keys)
            assert any("OPENAI_BASE_URL" in key for key in missing_keys)
            assert any("OPENAI_MODEL" in key for key in missing_keys)
    
    def test_validate_configuration_invalid_api_key_format(self, temp_project_root):
        """Test validation with invalid API key format."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "invalid-key",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4"
        }, clear=True):
            missing_keys = config_manager.validate_configuration()
            
            assert len(missing_keys) == 1
            assert "invalid format" in missing_keys[0]
    
    def test_validate_configuration_invalid_url_format(self, temp_project_root):
        """Test validation with invalid URL format."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test123456789",
            "OPENAI_BASE_URL": "not-a-valid-url",
            "OPENAI_MODEL": "gpt-4"
        }, clear=True):
            missing_keys = config_manager.validate_configuration()
            
            assert len(missing_keys) == 1
            assert "invalid URL format" in missing_keys[0]
    
    def test_validate_configuration_invalid_numeric_values(self, temp_project_root):
        """Test validation with invalid numeric values."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test123456789",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4",
            "MODEL_TEMPERATURE": "not-a-number",
            "MAX_TOKENS": "invalid"
        }, clear=True):
            missing_keys = config_manager.validate_configuration()
            
            assert len(missing_keys) == 2
            assert any("MODEL_TEMPERATURE" in key for key in missing_keys)
            assert any("MAX_TOKENS" in key for key in missing_keys)
    
    def test_validate_configuration_valid(self, temp_project_root):
        """Test validation with valid configuration."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test123456789",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4",
            "MODEL_TEMPERATURE": "0.1",
            "MAX_TOKENS": "4000"
        }, clear=True):
            missing_keys = config_manager.validate_configuration()
            
            assert len(missing_keys) == 0
    
    def test_get_llm_config_valid(self, temp_project_root):
        """Test getting LLM config with valid configuration."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test123456789",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4",
            "MODEL_TEMPERATURE": "0.2",
            "MAX_TOKENS": "2000",
            "REQUEST_TIMEOUT": "30"
        }, clear=True):
            llm_config = config_manager.get_llm_config()
            
            assert isinstance(llm_config, LLMConfig)
            assert llm_config.api_key == "sk-test123456789"
            assert llm_config.base_url == "https://api.openai.com/v1"
            assert llm_config.model == "gpt-4"
            assert llm_config.temperature == 0.2
            assert llm_config.max_tokens == 2000
            assert llm_config.timeout == 30
    
    def test_get_llm_config_defaults(self, temp_project_root):
        """Test getting LLM config with default values."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test123456789",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4"
        }, clear=True):
            llm_config = config_manager.get_llm_config()
            
            assert llm_config.temperature == 0.1  # default
            assert llm_config.max_tokens == 4000  # default
            assert llm_config.timeout == 60  # default
    
    def test_get_llm_config_invalid_configuration(self, temp_project_root):
        """Test getting LLM config with invalid configuration."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.get_llm_config()
            
            assert "Configuration validation failed" in str(exc_info.value)
    
    def test_get_autogen_config(self, temp_project_root):
        """Test getting AutoGen configuration dictionary."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test123456789",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4",
            "MODEL_TEMPERATURE": "0.2"
        }, clear=True):
            autogen_config = config_manager.get_autogen_config()
            
            assert "config_list" in autogen_config
            assert len(autogen_config["config_list"]) == 1
            
            config_item = autogen_config["config_list"][0]
            assert config_item["model"] == "gpt-4"
            assert config_item["api_key"] == "sk-test123456789"
            assert config_item["base_url"] == "https://api.openai.com/v1"
            assert config_item["api_type"] == "openai"
            
            assert autogen_config["temperature"] == 0.2
            assert autogen_config["max_tokens"] == 4000
            assert autogen_config["timeout"] == 60
    
    def test_get_agent_config(self, temp_project_root):
        """Test getting agent configuration."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "AGENT_TIMEOUT": "600",
            "MAX_SHELL_OUTPUT_SIZE": "20000",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        }, clear=True):
            agent_config = config_manager.get_agent_config()
            
            assert agent_config["agent_timeout"] == 600
            assert agent_config["max_shell_output_size"] == 20000
            assert agent_config["debug"] is True
            assert agent_config["log_level"] == "DEBUG"
    
    def test_get_agent_config_defaults(self, temp_project_root):
        """Test getting agent configuration with defaults."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {}, clear=True):
            agent_config = config_manager.get_agent_config()
            
            assert agent_config["agent_timeout"] == 300
            assert agent_config["max_shell_output_size"] == 10000
            assert agent_config["debug"] is False
            assert agent_config["log_level"] == "INFO"
    
    def test_get_config_value(self, temp_project_root):
        """Test getting specific configuration values."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "TEST_KEY": "test_value"
        }, clear=True):
            value = config_manager.get_config_value("TEST_KEY")
            assert value == "test_value"
            
            default_value = config_manager.get_config_value("MISSING_KEY", "default")
            assert default_value == "default"
            
            missing_value = config_manager.get_config_value("MISSING_KEY")
            assert missing_value is None
    
    def test_create_env_file_if_missing_success(self, temp_project_root, env_example_content):
        """Test creating .env file from .env.example."""
        # Create .env.example file
        env_example = temp_project_root / ".env.example"
        env_example.write_text(env_example_content)
        
        config_manager = ConfigurationManager(temp_project_root)
        result = config_manager.create_env_file_if_missing()
        
        assert result is True
        assert config_manager.env_file.exists()
        assert config_manager.env_file.read_text() == env_example_content
    
    def test_create_env_file_if_missing_already_exists(self, temp_project_root):
        """Test creating .env file when it already exists."""
        # Create existing .env file
        env_file = temp_project_root / ".env"
        env_file.write_text("EXISTING=value")
        
        config_manager = ConfigurationManager(temp_project_root)
        result = config_manager.create_env_file_if_missing()
        
        assert result is False
        assert env_file.read_text() == "EXISTING=value"
    
    def test_create_env_file_if_missing_no_example(self, temp_project_root):
        """Test creating .env file when .env.example doesn't exist."""
        config_manager = ConfigurationManager(temp_project_root)
        result = config_manager.create_env_file_if_missing()
        
        assert result is False
        assert not config_manager.env_file.exists()
    
    def test_get_setup_instructions_valid_config(self, temp_project_root):
        """Test setup instructions with valid configuration."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test123456789",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_MODEL": "gpt-4"
        }, clear=True):
            instructions = config_manager.get_setup_instructions()
            
            assert "✅ Configuration is valid and complete!" in instructions
    
    def test_get_setup_instructions_missing_config(self, temp_project_root):
        """Test setup instructions with missing configuration."""
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {}, clear=True):
            instructions = config_manager.get_setup_instructions()
            
            assert "❌ Configuration setup required:" in instructions
            assert "Create .env file:" in instructions
            assert "OPENAI_API_KEY" in instructions
            assert "OpenAI (recommended models):" in instructions
            assert "OpenRouter (use exact AutoGen model names):" in instructions
            assert "GitHub Copilot (via LiteLLM):" in instructions
    
    def test_get_setup_instructions_existing_env_file(self, temp_project_root):
        """Test setup instructions when .env file exists."""
        # Create existing .env file
        env_file = temp_project_root / ".env"
        env_file.write_text("INCOMPLETE=config")
        
        config_manager = ConfigurationManager(temp_project_root)
        
        with patch.dict(os.environ, {}, clear=True):
            instructions = config_manager.get_setup_instructions()
            
            assert "Edit your .env file" in instructions
            assert "Create .env file:" not in instructions
    
    def test_api_key_format_validation(self):
        """Test API key format validation."""
        config_manager = ConfigurationManager()
        
        # Valid formats
        assert config_manager._is_valid_api_key_format("sk-test123456789")
        assert config_manager._is_valid_api_key_format("sk-or-test123456789")
        assert config_manager._is_valid_api_key_format("sk-ant-test123456789")
        assert config_manager._is_valid_api_key_format("Bearer token123456789")
        assert config_manager._is_valid_api_key_format("sk-litellm-test123456789")
        
        # Invalid formats
        assert not config_manager._is_valid_api_key_format("")
        assert not config_manager._is_valid_api_key_format("invalid")
        assert not config_manager._is_valid_api_key_format("short")
        assert not config_manager._is_valid_api_key_format("abc-test123456789")
    
    def test_url_format_validation(self):
        """Test URL format validation."""
        config_manager = ConfigurationManager()
        
        # Valid formats
        assert config_manager._is_valid_url_format("https://api.openai.com/v1")
        assert config_manager._is_valid_url_format("http://localhost:4000")
        assert config_manager._is_valid_url_format("https://openrouter.ai/api/v1")
        
        # Invalid formats
        assert not config_manager._is_valid_url_format("")
        assert not config_manager._is_valid_url_format("not-a-url")
        assert not config_manager._is_valid_url_format("ftp://example.com")
        assert not config_manager._is_valid_url_format("api.openai.com")
    
    def test_numeric_validation(self):
        """Test numeric value validation."""
        config_manager = ConfigurationManager()
        
        # Valid numbers
        assert config_manager._is_valid_numeric("0")
        assert config_manager._is_valid_numeric("123")
        assert config_manager._is_valid_numeric("0.1")
        assert config_manager._is_valid_numeric("3.14159")
        assert config_manager._is_valid_numeric("-1")
        
        # Invalid numbers
        assert not config_manager._is_valid_numeric("")
        assert not config_manager._is_valid_numeric("abc")
        assert not config_manager._is_valid_numeric("1.2.3")
        assert not config_manager._is_valid_numeric("12a")


class TestLLMConfig:
    """Test suite for LLMConfig dataclass."""
    
    def test_llm_config_creation(self):
        """Test creating LLMConfig with all parameters."""
        config = LLMConfig(
            api_key="sk-test123456789",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.2,
            max_tokens=2000,
            timeout=30
        )
        
        assert config.api_key == "sk-test123456789"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4"
        assert config.temperature == 0.2
        assert config.max_tokens == 2000
        assert config.timeout == 30
    
    def test_llm_config_defaults(self):
        """Test LLMConfig with default values."""
        config = LLMConfig(
            api_key="sk-test123456789",
            base_url="https://api.openai.com/v1",
            model="gpt-4"
        )
        
        assert config.temperature == 0.1
        assert config.max_tokens == 4000
        assert config.timeout == 60


class TestConfigurationError:
    """Test suite for ConfigurationError exception."""
    
    def test_configuration_error_creation(self):
        """Test creating ConfigurationError."""
        error = ConfigurationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
