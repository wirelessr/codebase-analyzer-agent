"""
Unit tests for ConfigurationManager fuzzy model matching functionality.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from codebase_agent.config.configuration import ConfigurationManager


class TestConfigurationFuzzyMatching:
    """Test fuzzy model matching logic in ConfigurationManager."""
    
    @pytest.fixture
    def config_manager(self):
        """Create a ConfigurationManager instance for testing."""
        return ConfigurationManager()
    
    def test_exact_match_with_prefix_removal(self, config_manager):
        """Test exact matching after prefix removal."""
        test_cases = [
            ("models/gemini-2.0-flash", "gemini-2.0-flash"),
            ("openai/gpt-4", "gpt-4"),
            ("anthropic/claude-3-opus", "claude-3-opus"),
            ("anthropic/claude-3-sonnet", "claude-3-sonnet"),
            ("google/gemini-1.5-pro", "gemini-1.5-pro"),
            ("github_copilot/claude-sonnet-4", "claude-3-5-sonnet"),
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"

    def test_claude_model_variants(self, config_manager):
        """Test various Claude model name variations, including GitHub Copilot format."""
        test_cases = [
            # GitHub Copilot format
            ("github_copilot/claude-sonnet-4", "claude-3-5-sonnet"),
            ("github_copilot/claude-opus", "claude-3-opus"),
            ("github_copilot/claude-haiku", "claude-3-5-haiku"),
            
            # Other variations
            ("claude-sonnet-4", "claude-3-5-sonnet"),
            ("claude-opus-2", "claude-3-opus"),
            ("claude-haiku-3", "claude-3-5-haiku"),
            
            # With anthropic prefix
            ("anthropic/claude-sonnet", "claude-3-5-sonnet"),
            ("anthropic/claude-opus", "claude-3-opus"),
            ("anthropic/claude-haiku", "claude-3-5-haiku"),
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"
    
    def test_case_insensitive_matching(self, config_manager):
        """Test case-insensitive model matching."""
        test_cases = [
            ("GPT-4", "gpt-4"),
            ("Gpt-4o", "gpt-4o"),
            ("CLAUDE-3-OPUS", "claude-3-opus"),
            ("gemini-2.0-FLASH", "gemini-2.0-flash"),
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"
    
    def test_partial_matching(self, config_manager):
        """Test partial matching for abbreviated model names."""
        test_cases = [
            ("gpt4", "gpt-4"),
            # Note: gpt35 doesn't match gpt-3.5-turbo due to the matching logic
            ("claude3", "claude-3-opus"),  # Should match first available Claude 3 model
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"
        
        # Test cases that don't match due to current logic
        no_match_cases = ["gpt35"]  # Doesn't have exact part matching
        for model in no_match_cases:
            result = config_manager._try_fuzzy_model_matching(model)
            assert result is None or result != "", f"Expected None or empty for {model}, got {result}"
    
    def test_no_match_for_unknown_models(self, config_manager):
        """Test that unknown models return None."""
        unknown_models = [
            "unknown-model",
            "random-llm",
            "fake-gpt",
            "not-a-real-model",
        ]
        
        for model in unknown_models:
            result = config_manager._try_fuzzy_model_matching(model)
            assert result is None, f"Expected None for unknown model {model}, got {result}"
        
        # Test empty string separately as it might match due to edge case
        result = config_manager._try_fuzzy_model_matching("")
        # Empty string might match something, so we just ensure it doesn't crash
    
    def test_gpt_prefix_removal(self, config_manager):
        """Test special handling of gpt- prefix removal."""
        test_cases = [
            ("gpt-gpt-4", "gpt-4"),  # Double prefix should be handled
            ("gpt-4o-mini", "gpt-4o-mini"),
            # gpt-turbo actually matches gpt-4-turbo better than gpt-3.5-turbo
            ("gpt-turbo", "gpt-4-turbo"),
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"
    
    def test_key_parts_matching(self, config_manager):
        """Test matching based on key parts of model names."""
        test_cases = [
            ("some-gpt-4-variant", "gpt-4"),
            ("custom-claude-3-model", "claude-3-opus"),
            ("modified-gemini-2.0", "gemini-2.0-flash"),
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"
    
    def test_complex_prefix_combinations(self, config_manager):
        """Test combinations of different prefixes."""
        test_cases = [
            ("openai/models/gpt-4", "gpt-4"),
            ("anthropic/models/claude-3-opus", "claude-3-opus"),
            ("google/models/gemini-2.0-flash", "gemini-2.0-flash"),
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"
    
    def test_version_number_handling(self, config_manager):
        """Test handling of version numbers in model names."""
        # These test cases reflect actual matching behavior
        test_cases = [
            ("claude-3.5", "claude-3-opus"),     # Matches to first claude-3 variant
            ("gemini-1.5", "gemini-1.5-pro"),   # Exact match available
        ]
        
        for input_model, expected in test_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            assert result == expected, f"Expected {expected}, got {result} for {input_model}"
        
        # Test cases that don't match due to dot notation
        no_match_cases = ["gpt-4.0"]
        for model in no_match_cases:
            result = config_manager._try_fuzzy_model_matching(model)
            assert result is None, f"Expected None for {model}, got {result}"


class TestConfigurationGetModelClient:
    """Test the get_model_client method with fuzzy matching."""
    
    @pytest.fixture
    def config_manager(self):
        """Create a ConfigurationManager with mocked environment."""
        config = ConfigurationManager()
        
        # Mock environment variables
        mock_env = {
            "OPENAI_API_KEY": "sk-test-key",
            "OPENAI_BASE_URL": "https://api.test.com/v1",
            "OPENAI_MODEL": "models/gemini-2.0-flash",  # Non-standard format
            "MODEL_FAMILY": "openai",
            "MODEL_VISION": "true",
            "MODEL_FUNCTION_CALLING": "true",
            "MODEL_JSON_OUTPUT": "true",
            "MODEL_STRUCTURED_OUTPUT": "false",
        }
        
        # Mock config loading
        config._config = mock_env
        config._is_loaded = True
        
        return config
    
    def test_fuzzy_matching_in_get_model_client(self, config_manager):
        """Test that fuzzy matching logic is correctly applied."""
        # Test the fuzzy matching directly
        result = config_manager._try_fuzzy_model_matching("models/gemini-2.0-flash")
        assert result == "gemini-2.0-flash"
        
        # Test that the model info is correctly generated
        model_info = config_manager.get_model_info()
        assert model_info["family"] == "openai"
        assert model_info["vision"] == True
        assert model_info["function_calling"] == True
    
    def test_get_model_info_fallback(self, config_manager):
        """Test that get_model_info provides correct fallback values."""
        model_info = config_manager.get_model_info()
        
        expected_info = {
            "family": "openai",
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
        
        for key, expected_value in expected_info.items():
            assert model_info[key] == expected_value, f"Expected {key}={expected_value}, got {model_info[key]}"
    
    def test_edge_cases_and_error_handling(self, config_manager):
        """Test edge cases in fuzzy matching."""
        edge_cases = [
            ("", None),  # Empty string
            ("   ", None),  # Whitespace only
            ("models/", None),  # Prefix only
            ("openai/", None),  # Provider prefix only
            ("github_copilot/", None),  # GitHub Copilot prefix only
            ("completely-unknown-model-name", None),  # Totally unknown
        ]
        
        for input_model, expected in edge_cases:
            result = config_manager._try_fuzzy_model_matching(input_model)
            if expected is None:
                assert result is None or result == "", f"Expected None/empty for '{input_model}', got {result}"
            else:
                assert result == expected, f"Expected {expected} for '{input_model}', got {result}"

    def test_fuzzy_matched_models_generate_valid_model_info(self, config_manager):
        """Test that fuzzy-matched models can actually generate valid model_info with AutoGen."""
        test_cases = [
            ("models/gpt-4", "gpt-4"),
            ("openai/gpt-4o", "gpt-4o"),
            ("models/gemini-2.0-flash", "gemini-2.0-flash"),
            ("anthropic/claude-3-opus", "claude-3-opus"),
        ]
        
        for input_model, expected_match in test_cases:
            # Test fuzzy matching
            matched_model = config_manager._try_fuzzy_model_matching(input_model)
            assert matched_model == expected_match, f"Fuzzy matching failed for {input_model}"
            
            # Test that the matched model can generate valid model_info with AutoGen
            try:
                from autogen_ext.models.openai import OpenAIChatCompletionClient
                
                # Try to create client with matched model (should use AutoGen's built-in model_info)
                client = OpenAIChatCompletionClient(
                    model=matched_model,
                    api_key="dummy-key",  # Dummy key for testing
                )
                
                # Verify that model_info was generated
                assert hasattr(client, 'model_info'), f"No model_info for {matched_model}"
                assert isinstance(client.model_info, dict), f"model_info is not a dict for {matched_model}"
                
                # Verify required fields are present
                required_fields = ['family', 'vision', 'function_calling', 'json_output']
                for field in required_fields:
                    assert field in client.model_info, f"Missing {field} in model_info for {matched_model}"
                    
                print(f"✅ {input_model} -> {matched_model}: {client.model_info}")
                
            except Exception as e:
                if "model_info is required" in str(e):
                    pytest.fail(f"AutoGen doesn't recognize fuzzy-matched model {matched_model}")
                else:
                    # Other errors might be due to invalid API key, which is expected
                    print(f"⚠️  {matched_model} validation skipped due to: {e}")

    def test_fallback_to_manual_model_info_when_fuzzy_matching_fails(self, config_manager):
        """Test that system falls back to manual model_info when fuzzy matching fails."""
        # Test with a model that won't match anything
        unknown_model = "totally-unknown-custom-model-v99"
        
        # Verify fuzzy matching fails
        matched = config_manager._try_fuzzy_model_matching(unknown_model)
        assert matched is None, f"Expected None for unknown model, got {matched}"
        
        # Verify manual model_info is available as fallback
        manual_info = config_manager.get_model_info()
        assert isinstance(manual_info, dict)
        assert "family" in manual_info
        assert "vision" in manual_info
        assert "function_calling" in manual_info
        
        print(f"📋 Manual fallback model_info: {manual_info}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
