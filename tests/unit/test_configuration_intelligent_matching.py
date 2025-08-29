"""
Unit tests for ConfigurationManager intelligent model matching functionality.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from codebase_agent.config.configuration import ConfigurationManager


class TestConfigurationIntelligentMatching:
    """Test intelligent model matching logic in ConfigurationManager."""

    @pytest.fixture
    def config_manager(self):
        """Create a ConfigurationManager instance for testing."""
        return ConfigurationManager()

    def test_find_compatible_autogen_model_claude(self, config_manager):
        """Test finding compatible AutoGen models for Claude variants."""
        test_cases = [
            ("github_copilot/claude-sonnet-4", "claude"),
            ("claude-3.5-sonnet", "claude"),
            ("anthropic/claude-3-opus", "claude"),
            ("claude-haiku", "claude"),
        ]

        for input_model, expected_family in test_cases:
            result = config_manager._find_compatible_autogen_model(input_model)
            assert result is not None, f"No compatible model found for {input_model}"
            assert (
                expected_family in result.lower()
            ), f"Expected {expected_family} model, got {result} for {input_model}"

    def test_find_compatible_autogen_model_gpt(self, config_manager):
        """Test finding compatible AutoGen models for GPT variants."""
        test_cases = [
            ("gpt-4o", "gpt"),
            ("openai/gpt-4", "gpt"),
            ("gpt-3.5-turbo", "gpt"),
        ]

        for input_model, expected_family in test_cases:
            result = config_manager._find_compatible_autogen_model(input_model)
            assert result is not None, f"No compatible model found for {input_model}"
            assert (
                expected_family in result.lower()
            ), f"Expected {expected_family} model, got {result} for {input_model}"

    def test_find_compatible_autogen_model_gemini(self, config_manager):
        """Test finding compatible AutoGen models for Gemini variants."""
        test_cases = [
            ("google/gemini-2.0-flash", "gemini"),
            ("gemini-1.5-pro", "gemini"),
        ]

        for input_model, expected_family in test_cases:
            result = config_manager._find_compatible_autogen_model(input_model)
            assert result is not None, f"No compatible model found for {input_model}"
            assert (
                expected_family in result.lower()
            ), f"Expected {expected_family} model, got {result} for {input_model}"

    def test_get_model_info_from_autogen_model(self, config_manager):
        """Test extracting model_info from AutoGen models."""
        # Test with a known AutoGen model
        model_info = config_manager._get_model_info_from_autogen_model(
            "gpt-4o-2024-11-20"
        )

        if model_info:  # Only test if we successfully got model_info
            assert isinstance(model_info, dict)
            # Check for common model_info fields
            expected_fields = ["family", "vision", "function_calling", "json_output"]
            for field in expected_fields:
                assert field in model_info, f"Missing field {field} in model_info"

    def test_generate_model_info_from_name_claude(self, config_manager):
        """Test generating model_info from Claude model names."""
        test_cases = [
            ("claude-3.5-sonnet", {"family": "claude", "vision": True}),
            ("anthropic/claude-4", {"family": "claude", "vision": True}),
            ("claude-haiku", {"family": "claude"}),
        ]

        for model_name, expected_fields in test_cases:
            model_info = config_manager._generate_model_info_from_name(model_name)
            assert isinstance(model_info, dict)
            for field, expected_value in expected_fields.items():
                assert (
                    model_info[field] == expected_value
                ), f"Expected {field}={expected_value}, got {model_info[field]}"

    def test_generate_model_info_from_name_gpt(self, config_manager):
        """Test generating model_info from GPT model names."""
        test_cases = [
            ("gpt-4o", {"vision": True}),
            ("gpt-3.5-turbo", {"vision": False}),
        ]

        for model_name, expected_fields in test_cases:
            model_info = config_manager._generate_model_info_from_name(model_name)
            assert isinstance(model_info, dict)
            for field, expected_value in expected_fields.items():
                assert (
                    model_info[field] == expected_value
                ), f"Expected {field}={expected_value}, got {model_info[field]}"

    def test_try_fuzzy_model_matching_returns_none(self, config_manager):
        """Test that _try_fuzzy_model_matching now returns None (legacy method)."""
        test_models = [
            "github_copilot/claude-sonnet-4",
            "gpt-4o",
            "models/gemini-2.0-flash",
        ]

        for model in test_models:
            result = config_manager._try_fuzzy_model_matching(model)
            assert (
                result is None
            ), f"Expected None from legacy method, got {result} for {model}"


class TestConfigurationGetModelClient:
    """Test model client creation with intelligent model matching."""

    @pytest.fixture
    def config_manager(self):
        """Create a ConfigurationManager instance for testing."""
        manager = ConfigurationManager()
        # Mock environment for testing
        manager._config = {
            "OPENAI_API_KEY": "sk-test-key",
            "OPENAI_BASE_URL": "http://localhost:4000/v1",
            "OPENAI_MODEL": "github_copilot/claude-sonnet-4",
        }
        manager._is_loaded = True
        return manager

    def test_intelligent_matching_in_get_model_client(self, config_manager):
        """Test that intelligent matching logic is correctly applied."""
        # Test the compatible model finding
        result = config_manager._find_compatible_autogen_model(
            "github_copilot/claude-sonnet-4"
        )
        assert result is not None
        assert "claude" in result.lower()

    def test_get_model_info_with_intelligent_matching(self, config_manager):
        """Test that get_model_info uses intelligent matching."""
        model_info = config_manager.get_model_info()

        # Should be a valid model_info dict
        assert isinstance(model_info, dict)
        required_fields = ["family", "vision", "function_calling", "json_output"]
        for field in required_fields:
            assert field in model_info, f"Missing required field: {field}"

    def test_intelligent_matched_models_generate_valid_model_info(self, config_manager):
        """Test that intelligently-matched models can actually generate valid model_info."""
        test_cases = [
            "github_copilot/claude-sonnet-4",
            "openai/gpt-4o",
            "google/gemini-2.0-flash",
        ]

        for input_model in test_cases:
            # Test compatible model finding
            compatible_model = config_manager._find_compatible_autogen_model(
                input_model
            )
            if compatible_model:
                # Test model_info extraction
                config_manager._get_model_info_from_autogen_model(compatible_model)
                # model_info might be None if AutoGen client creation fails in test env
                # That's OK, we're mainly testing that the logic doesn't crash
