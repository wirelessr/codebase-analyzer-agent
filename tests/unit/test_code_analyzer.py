"""
Unit tests for Code Analyzer Agent.

Tests the core functionality of the updated implementation:
- Dual-phase execution (LLM decision + shell execution)
- JSON response parsing (integrated into main flow)
- Progressive analysis functionality
"""

from unittest.mock import Mock, patch

import pytest

from src.codebase_agent.agents.code_analyzer import CodeAnalyzer


@pytest.fixture
def analyzer():
    """Create a CodeAnalyzer instance for testing."""
    mock_shell_tool = Mock()
    mock_config = {"config_list": [{"model": "gpt-4"}]}

    with patch(
        "src.codebase_agent.agents.code_analyzer.AssistantAgent"
    ) as mock_agent_class:
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        analyzer = CodeAnalyzer(config=mock_config, shell_tool=mock_shell_tool)
        return analyzer


class TestCodeAnalyzer:
    """Test cases for CodeAnalyzer class."""

    def test_initialization(self, analyzer):
        """Test CodeAnalyzer initialization."""
        assert hasattr(analyzer, "config")
        assert hasattr(analyzer, "shell_tool")
        assert hasattr(analyzer, "_agent")

    def test_execute_shell_commands_success(self, analyzer):
        """Test successful shell command execution."""
        commands = ["ls -la", "pwd"]
        analyzer.shell_tool.execute_command = Mock(
            side_effect=[
                (
                    True,
                    "file1.py\nfile2.py",
                    "",
                ),  # Returns tuple (success, stdout, stderr)
                (True, "/test/project", ""),
            ]
        )

        results = analyzer._execute_shell_commands(commands)

        assert len(results) == 2
        assert results[0]["success"]
        assert results[0]["stdout"] == "file1.py\nfile2.py"
        assert results[1]["stdout"] == "/test/project"

    def test_execute_shell_commands_failure(self, analyzer):
        """Test shell command execution with failure."""
        commands = ["invalid_command"]
        analyzer.shell_tool.execute_command = Mock(
            side_effect=Exception("Test exception")
        )

        results = analyzer._execute_shell_commands(commands)

        assert len(results) == 1
        assert not results[0]["success"]
        assert results[0]["error"] == "Test exception"

    def test_assess_convergence_from_json_high_confidence(self, analyzer):
        """Test convergence assessment with high confidence JSON response."""
        llm_decision = {
            "need_shell_execution": False,
            "confidence_level": 9,
            "key_findings": ["Finding 1", "Finding 2"],
        }
        context = [
            {"shell_results": [{"success": True}]},
            {"shell_results": [{"success": True}]},
        ]

        convergence = analyzer._assess_convergence_from_json(llm_decision, context)

        assert convergence["confidence_threshold_met"]  # confidence >= 8
        assert convergence["question_answered"]  # need_shell_execution is False
        assert convergence["sufficient_code_coverage"]  # len(context) >= 2

    def test_assess_convergence_from_json_low_confidence(self, analyzer):
        """Test convergence assessment with low confidence JSON response."""
        llm_decision = {
            "need_shell_execution": True,
            "confidence_level": 5,
            "key_findings": ["Finding 1"],
        }
        context = [{"shell_results": []}]

        convergence = analyzer._assess_convergence_from_json(llm_decision, context)

        assert not convergence["confidence_threshold_met"]  # confidence < 8
        assert not convergence["question_answered"]  # need_shell_execution is True
        assert (
            not convergence["sufficient_code_coverage"]
        )  # len(context) < 2 and total_commands < 3

    def test_system_message_contains_knowledge_base_guidance(self, analyzer):
        """Test that system message includes collaborative knowledge base guidance."""
        system_message = analyzer._get_system_message()

        # Check for knowledge base keywords
        assert "COLLABORATIVE KNOWLEDGE BASE" in system_message
        assert "key_findings" in system_message
        assert "REVIEW" in system_message
        assert "ADD" in system_message
        assert "UPDATE" in system_message

    def test_system_message_contains_json_format(self, analyzer):
        """Test that system message specifies JSON response format."""
        system_message = analyzer._get_system_message()

        # Check for JSON format requirements
        assert "JSON" in system_message
        assert "need_shell_execution" in system_message
        assert "shell_commands" in system_message
        assert "confidence_level" in system_message

    def test_extract_response_text(self, analyzer):
        """Test response text extraction from AutoGen TaskResult."""
        # Mock TaskResult structure
        mock_task_result = Mock()
        mock_task_result.messages = [
            Mock(content="Message 1"),
            Mock(content="Message 2"),
        ]

        result = analyzer._extract_response_text(mock_task_result)

        # Should extract the last message content
        assert result == "Message 2"

    def test_should_terminate_true(self, analyzer):
        """Test termination condition when all criteria are met."""
        convergence = {
            "confidence_threshold_met": True,
            "question_answered": True,
            "sufficient_code_coverage": True,
        }

        assert analyzer._should_terminate(convergence)

    def test_should_terminate_false(self, analyzer):
        """Test termination condition when criteria are not met."""
        convergence = {
            "confidence_threshold_met": False,
            "question_answered": True,
            "sufficient_code_coverage": True,
        }

        assert not analyzer._should_terminate(convergence)

    def test_synthesize_final_response(self, analyzer):
        """Test final response synthesis."""
        query = "What is the project structure?"
        context = [{"iteration": 1}]
        shared_findings = ["Finding 1", "Finding 2"]
        convergence = {"confidence_threshold_met": True}

        result = analyzer._synthesize_final_response(
            query, context, shared_findings, convergence
        )

        assert "Finding 1" in result
        assert "Finding 2" in result
        assert query in result or "project structure" in result.lower()
