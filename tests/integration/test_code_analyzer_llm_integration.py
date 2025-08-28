"""
Integration tests for Code Analyzer Agent LLM and Prompt Effectiveness.

Tests the actual LLM integration and prompt effectiveness:
- Real LLM calls with actual AutoGen agents  
- Prompt validation and response quality
- Multi-round analysis convergence
- End-to-end analysis workflow
- Specialist feedback integration
"""

import pytest
import tempfile
import os
from unittest.mock import Mock
from codebase_agent.agents.code_analyzer import CodeAnalyzer


class TestCodeAnalyzerLLMIntegration:
    """Integration tests for Code Analyzer LLM and prompt effectiveness."""

    @pytest.fixture
    def shell_tool(self, temp_codebase):
        """Create a real shell tool for testing."""
        from codebase_agent.tools.shell_tool import ShellTool
        return ShellTool(temp_codebase)

    @pytest.fixture
    def config(self):
        """Create real LLM configuration for testing."""
        try:
            from codebase_agent.config.configuration import ConfigurationManager
            config_manager = ConfigurationManager()
            config_manager.load_environment()
            return config_manager.get_model_client()
        except Exception as e:
            pytest.skip(f"Could not configure LLM: {e}")

    @pytest.fixture
    def analyzer(self, config, shell_tool):
        """Create a real CodeAnalyzer instance with LLM integration."""
        return CodeAnalyzer(config, shell_tool)

    @pytest.fixture
    def temp_codebase(self):
        """Create a temporary codebase for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python project structure
            os.makedirs(os.path.join(temp_dir, "src"))
            os.makedirs(os.path.join(temp_dir, "tests"))
            
            # Create some Python files
            with open(os.path.join(temp_dir, "src", "main.py"), "w") as f:
                f.write("""
def main():
    print("Hello, world!")
    return 0

if __name__ == "__main__":
    main()
""")
            
            with open(os.path.join(temp_dir, "tests", "test_main.py"), "w") as f:
                f.write("""
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        result = main()
        self.assertEqual(result, 0)
""")
            
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write("""
# Test Project

This is a simple test project for code analysis.

## Features
- Basic Python application
- Unit tests
- Simple structure
""")
            
            yield temp_dir

    def test_basic_analysis_prompt_effectiveness(self, analyzer, temp_codebase):
        """Test basic codebase analysis prompt with real LLM."""
        query = "分析這個Python專案的結構和主要功能"
        
        result = analyzer.analyze_codebase(query, temp_codebase)
        
        # Verify the analysis contains expected elements
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert len(result) > 100  # Should be a substantial analysis
        
        # Check for key analysis elements
        assert any(keyword in result.lower() for keyword in ["python", "main.py", "test"])

    def test_analysis_convergence_prompt(self, analyzer, temp_codebase):
        """Test that analysis prompts lead to convergence."""
        query = "完整分析這個專案的架構設計"
        
        result = analyzer.analyze_codebase(query, temp_codebase)
        
        # Verify analysis completion
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "Iterations:" in result
        
        # Extract iteration count
        lines = result.split('\n')
        iteration_line = next((line for line in lines if "Iterations:" in line), None)
        assert iteration_line is not None
        
        # Should converge in reasonable number of iterations (not hit max limit)
        iteration_count = int(iteration_line.split("Iterations:")[1].strip().split()[0])
        assert 1 <= iteration_count <= 10

    def test_prompt_chinese_language_support(self, analyzer, temp_codebase):
        """Test that prompts work effectively in Chinese."""
        query = "評估這個專案的程式碼品質和改進建議"
        
        result = analyzer.analyze_codebase(query, temp_codebase)
        
        # Verify the LLM understood the Chinese query
        assert "CODEBASE ANALYSIS COMPLETE" in result
        
        # Should mention quality-related concepts in response
        quality_keywords = ["quality", "improvement", "recommendation", "品質", "改進", "建議"]
        assert any(keyword in result.lower() for keyword in quality_keywords)

    def test_specialist_feedback_prompt_integration(self, analyzer, temp_codebase):
        """Test that specialist feedback is properly integrated into prompts."""
        query = "分析專案架構"
        feedback = "請特別關注程式碼的可維護性和擴展性設計"
        
        result = analyzer.analyze_codebase(query, temp_codebase, specialist_feedback=feedback)
        
        # Verify feedback was incorporated
        assert "CODEBASE ANALYSIS COMPLETE" in result
        
        # Should reflect the specialist feedback focus
        feedback_keywords = ["maintainability", "extensibility", "可維護", "擴展"]
        assert any(keyword in result.lower() for keyword in feedback_keywords)

    def test_multi_round_prompt_consistency(self, analyzer, temp_codebase):
        """Test that multi-round prompts maintain consistency."""
        query = "深入分析這個專案的設計模式和最佳實踐"
        
        result = analyzer.analyze_codebase(query, temp_codebase)
        
        # Verify the analysis went through multiple rounds
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "Iterations:" in result
        
        # Should contain consistent technical analysis
        technical_keywords = ["design", "pattern", "best practice", "設計", "模式", "最佳實踐"]
        assert any(keyword in result.lower() for keyword in technical_keywords)


# Manual test runner for development
if __name__ == "__main__":
    # This allows manual testing during development
    # Remove the @pytest.mark.skip decorators to run with real LLM
    print("Code Analyzer LLM Integration Tests")
    print("Remove @pytest.mark.skip decorators to run with real LLM")
    pytest.main([__file__, "-v", "-s"])
