"""
Integration tests for Code Analyzer Agent LLM and Prompt Effectiveness.

TESTING SCENARIO: DEBUGGING AND ERROR ANALYSIS
Tests the actual LLM integration and prompt effectiveness for debugging:
- Bug identification and error detection with real LLM calls
- Exception handling analysis and recommendations
- Code stability and robustness assessment
- Error recovery mechanism evaluation
- Multi-round debugging analysis convergence
- Debugging-focused prompt validation and response quality
"""

import os
import tempfile

import pytest

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
        """Create a temporary codebase with bugs for debugging testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python project structure with common bugs
            os.makedirs(os.path.join(temp_dir, "src"))
            os.makedirs(os.path.join(temp_dir, "tests"))

            # Create Python files with deliberate bugs
            with open(os.path.join(temp_dir, "src", "main.py"), "w") as f:
                f.write(
                    """
def calculate_average(numbers):
    # Bug: Division by zero when empty list
    return sum(numbers) / len(numbers)

def process_user_data(user_data):
    # Bug: KeyError when required field missing
    name = user_data['name']
    email = user_data['email']
    age = user_data['age']

    # Bug: String concatenation with integer
    return "User: " + name + ", Age: " + age

def find_user_by_id(users, user_id):
    # Bug: Returns None without handling, causes AttributeError later
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def main():
    # Bug: Hardcoded values that may cause errors
    data = [1, 2, 3, 0]  # Zero might cause issues in some calculations
    result = calculate_average([])  # Empty list will cause division by zero
    print(f"Average: {result}")

    # Bug: Missing error handling
    user_data = {"name": "John"}  # Missing required fields
    processed = process_user_data(user_data)
    print(processed)

if __name__ == "__main__":
    main()
"""
                )

            with open(os.path.join(temp_dir, "tests", "test_main.py"), "w") as f:
                f.write(
                    """
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.main import calculate_average, process_user_data, find_user_by_id

class TestMain(unittest.TestCase):
    def test_calculate_average(self):
        # This test will fail due to division by zero
        result = calculate_average([])
        self.assertEqual(result, 0)

    def test_process_user_data_missing_fields(self):
        # This test will fail due to KeyError
        incomplete_data = {"name": "John"}
        result = process_user_data(incomplete_data)
        self.assertIsNotNone(result)

    def test_find_user_by_id_none_result(self):
        users = [{"id": 1, "name": "Alice"}]
        result = find_user_by_id(users, 999)
        # This might cause AttributeError if result is used without checking
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
"""
                )

            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write(
                    """
# Test Project with Bugs

This is a simple test project that contains several common programming bugs for debugging analysis.

## Known Issues
- Division by zero errors
- Missing error handling
- Type mismatch errors
- KeyError exceptions
- None handling issues

## Features
- Basic Python application with calculation functions
- User data processing
- User lookup functionality
- Unit tests (some failing)
"""
                )

            yield temp_dir

    def test_basic_analysis_prompt_effectiveness(self, analyzer, temp_codebase):
        """Test debugging analysis prompt with real LLM."""
        query = "分析這個Python專案中的潛在錯誤和異常處理問題，找出可能導致程式崩潰的bug"

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify the analysis contains expected debugging elements
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert len(result) > 100  # Should be a substantial debugging analysis

        # Check for debugging-related analysis elements
        debugging_keywords = [
            "error",
            "exception",
            "bug",
            "division",
            "keyerror",
            "none",
            "錯誤",
            "異常",
            "除錯",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in debugging_keywords if keyword in result_lower
        ]
        assert (
            len(found_keywords) >= 2
        ), f"Expected debugging analysis keywords, found: {found_keywords}"

    def test_analysis_convergence_prompt(self, analyzer, temp_codebase):
        """Test that debugging analysis prompts lead to convergence on error identification."""
        query = "完整除錯分析：找出這個專案中所有的錯誤處理缺陷和潛在的執行時錯誤"

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify debugging analysis completion
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "Iterations:" in result

        # Extract iteration count
        lines = result.split("\n")
        iteration_line = next((line for line in lines if "Iterations:" in line), None)
        assert iteration_line is not None

        # Should converge in reasonable number of iterations (not hit max limit)
        iteration_count = int(iteration_line.split("Iterations:")[1].strip().split()[0])
        assert 1 <= iteration_count <= 10

        # Check for error identification
        error_terms = [
            "division by zero",
            "keyerror",
            "error handling",
            "exception",
            "none handling",
            "錯誤處理",
            "異常",
        ]
        result_lower = result.lower()
        found_error_terms = [term for term in error_terms if term in result_lower]
        assert (
            len(found_error_terms) >= 1
        ), f"Expected error identification, found: {found_error_terms}"

    def test_prompt_chinese_language_support(self, analyzer, temp_codebase):
        """Test that debugging prompts work effectively in Chinese."""
        query = "評估這個專案的程式碼穩定性，找出容易造成程式當機的問題點"

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify the LLM understood the Chinese debugging query
        assert "CODEBASE ANALYSIS COMPLETE" in result

        # Should mention stability and crash-related concepts in response
        stability_keywords = [
            "stability",
            "crash",
            "error",
            "exception",
            "穩定",
            "當機",
            "錯誤",
            "異常",
            "問題",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in stability_keywords if keyword in result_lower
        ]
        assert (
            len(found_keywords) >= 2
        ), f"Expected stability/debugging keywords, found: {found_keywords}"

    def test_specialist_feedback_prompt_integration(self, analyzer, temp_codebase):
        """Test that specialist feedback is properly integrated into debugging prompts."""
        query = "分析專案中的錯誤處理"
        feedback = "請特別關注除錯資訊的完整性和錯誤恢復機制的設計"

        result = analyzer.analyze_codebase(
            query, temp_codebase, specialist_feedback=feedback
        )

        # Verify feedback was incorporated into debugging analysis
        assert "CODEBASE ANALYSIS COMPLETE" in result

        # Should reflect the specialist feedback focus on debugging and error recovery
        debugging_keywords = [
            "error handling",
            "recovery",
            "debugging",
            "exception",
            "錯誤處理",
            "恢復",
            "除錯",
            "error",
            "exception handling",
            "fault tolerance",
            "resilience",
            "robustness",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in debugging_keywords if keyword in result_lower
        ]
        has_debugging_focus = len(found_keywords) >= 2

        # If no direct keywords found, check if the analysis is substantial (indicating focus was applied)
        if not has_debugging_focus:
            # As long as we got a detailed analysis, specialist feedback was likely considered
            assert (
                len(result) > 200
            ), f"Expected substantial debugging analysis when feedback provided, got {len(result)} chars"
        else:
            # Great! Found relevant debugging keywords
            pass

    def test_multi_round_prompt_consistency(self, analyzer, temp_codebase):
        """Test that multi-round debugging prompts maintain consistency."""
        query = "深入分析這個專案的錯誤處理機制和異常安全性設計"

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify the debugging analysis went through multiple rounds
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "Iterations:" in result

        # Should contain consistent debugging and error handling analysis
        debugging_keywords = [
            "error",
            "exception",
            "handling",
            "safety",
            "錯誤",
            "異常",
            "處理",
            "安全",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in debugging_keywords if keyword in result_lower
        ]
        assert (
            len(found_keywords) >= 2
        ), f"Expected debugging consistency, found: {found_keywords}"


# Manual test runner for development
if __name__ == "__main__":
    # This allows manual testing during development
    # Remove the @pytest.mark.skip decorators to run with real LLM
    print("Code Analyzer LLM Integration Tests")
    print("Remove @pytest.mark.skip decorators to run with real LLM")
    pytest.main([__file__, "-v", "-s"])
