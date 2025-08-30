"""
Unit tests for Code Analyzer Agent.

Tests the core functionality of the updated implementation:
- Dual-phase execution (LLM decision + shell execution)
- JSON response parsing (integrated into main flow)
- Progressive analysis functionality
- Self-interaction and multi-round iteration
- Knowledge base accumulation across iterations
"""

from unittest.mock import Mock, patch

import pytest

from codebase_agent.agents.code_analyzer import CodeAnalyzer


@pytest.fixture
def analyzer():
    """Create a CodeAnalyzer instance for testing."""
    mock_shell_tool = Mock()
    mock_config = {"config_list": [{"model": "gpt-4"}]}

    with patch(
        "codebase_agent.agents.code_analyzer.AssistantAgent"
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
        assert not convergence[
            "sufficient_code_coverage"
        ]  # len(context) < 2 and total_commands < 3

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
        """Test response text extraction from AutoGen TaskResult using utility function."""
        from codebase_agent.utils.autogen_utils import (
            extract_text_from_autogen_response,
        )

        # Mock TaskResult structure
        mock_task_result = Mock()
        mock_task_result.messages = [
            Mock(content="Message 1"),
            Mock(content="Message 2"),
        ]

        result = extract_text_from_autogen_response(mock_task_result)

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

    @patch("codebase_agent.agents.code_analyzer.CodeAnalyzer._execute_shell_commands")
    def test_analyze_codebase_single_iteration_converges(
        self, mock_shell_exec, analyzer
    ):
        """Test analyze_codebase converges in single iteration with high confidence."""

        # Mock the agent's run method directly to avoid asyncio issues
        async def mock_agent_run(task):
            mock_result = Mock()
            mock_result.messages = [
                Mock(
                    content="""{
                "need_shell_execution": false,
                "shell_commands": [],
                "key_findings": ["Python project found", "Main module identified"],
                "current_analysis": "This is a Python project with main module",
                "confidence_level": 9,
                "next_focus_areas": "Analysis complete"
            }"""
                )
            ]
            return mock_result

        analyzer._agent.run = mock_agent_run

        # Mock shell execution (shouldn't be called since need_shell_execution is false)
        mock_shell_exec.return_value = []

        # Mock asyncio.run to properly handle the coroutine
        with patch("asyncio.run") as mock_async_run:

            def run_mock(coro):
                import asyncio

                # Create a new event loop for testing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            mock_async_run.side_effect = run_mock

            result = analyzer.analyze_codebase(
                "What files are in this project?", "/test/path"
            )

        # Verify result contains key findings
        assert "Python project found" in result
        assert "Main module identified" in result
        assert "CODEBASE ANALYSIS COMPLETE" in result

    @patch("codebase_agent.agents.code_analyzer.CodeAnalyzer._execute_shell_commands")
    def test_analyze_codebase_multiple_iterations(self, mock_shell_exec, analyzer):
        """Test analyze_codebase performs multiple iterations with low confidence."""
        # Mock agent responses for multiple iterations
        call_count = [0]
        responses = [
            # First iteration - low confidence
            """{
                "need_shell_execution": true,
                "shell_commands": ["ls -la"],
                "key_findings": ["Initial exploration"],
                "current_analysis": "Found some files, need to explore more",
                "confidence_level": 4,
                "next_focus_areas": "Explore Python files"
            }""",
            # Second iteration - high confidence
            """{
                "need_shell_execution": false,
                "shell_commands": [],
                "key_findings": ["Initial exploration", "Project structure understood"],
                "current_analysis": "Complete analysis of project structure",
                "confidence_level": 9,
                "next_focus_areas": "Final analysis complete"
            }""",
        ]

        async def mock_agent_run(task):
            mock_result = Mock()
            mock_result.messages = [Mock(content=responses[call_count[0]])]
            call_count[0] += 1
            return mock_result

        analyzer._agent.run = mock_agent_run

        # Mock shell execution returns (only for first iteration)
        mock_shell_exec.return_value = [
            {
                "command": "ls -la",
                "success": True,
                "stdout": "file1.py\nfile2.py",
                "stderr": "",
                "error": None,
            }
        ]

        # Mock asyncio.run to properly handle the coroutine
        with patch("asyncio.run") as mock_async_run:

            def run_mock(coro):
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            mock_async_run.side_effect = run_mock

            result = analyzer.analyze_codebase(
                "What files are in this project?", "/test/path"
            )

        # Verify final result contains accumulated findings
        assert "Initial exploration" in result
        assert "Project structure understood" in result
        assert "Iterations: 2" in result

    @patch("codebase_agent.agents.code_analyzer.CodeAnalyzer._execute_shell_commands")
    def test_analyze_codebase_with_specialist_feedback(self, mock_shell_exec, analyzer):
        """Test analyze_codebase incorporates specialist feedback."""

        async def mock_agent_run(task):
            mock_result = Mock()
            mock_result.messages = [
                Mock(
                    content="""{
                "need_shell_execution": true,
                "shell_commands": ["grep -r 'class' ."],
                "key_findings": ["Classes found based on feedback"],
                "current_analysis": "Found classes as requested by specialist",
                "confidence_level": 8,
                "next_focus_areas": "Complete"
            }"""
                )
            ]
            return mock_result

        analyzer._agent.run = mock_agent_run

        mock_shell_exec.return_value = [
            {
                "command": "grep -r 'class' .",
                "success": True,
                "stdout": "class TestClass:",
                "stderr": "",
                "error": None,
            }
        ]

        specialist_feedback = "Focus on finding Python classes in the codebase"

        # Mock asyncio.run to properly handle the coroutine
        with patch("asyncio.run") as mock_async_run:

            def run_mock(coro):
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            mock_async_run.side_effect = run_mock

            result = analyzer.analyze_codebase(
                "What is the structure?",
                "/test/path",
                specialist_feedback=specialist_feedback,
            )

        # Verify the analysis contains the expected result
        assert "Classes found based on feedback" in result

    @patch("codebase_agent.agents.code_analyzer.CodeAnalyzer._execute_shell_commands")
    def test_analyze_codebase_json_parsing_error_fallback(
        self, mock_shell_exec, analyzer
    ):
        """Test analyze_codebase handles JSON parsing errors gracefully."""

        # Mock response with invalid JSON
        async def mock_agent_run(task):
            mock_result = Mock()
            mock_result.messages = [
                Mock(content="This is not valid JSON response from the LLM")
            ]
            return mock_result

        analyzer._agent.run = mock_agent_run
        mock_shell_exec.return_value = []

        # Mock asyncio.run to properly handle the coroutine
        with patch("asyncio.run") as mock_async_run:

            def run_mock(coro):
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(coro)
                finally:
                    loop.close()

            mock_async_run.side_effect = run_mock

            result = analyzer.analyze_codebase(
                "What files are in this project?", "/test/path"
            )

        # Should not crash and should provide some fallback analysis
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "No analysis performed" not in result

    @patch("codebase_agent.agents.code_analyzer.CodeAnalyzer._execute_shell_commands")
    def test_analyze_codebase_max_iterations_limit(self, mock_shell_exec, analyzer):
        """Test analyze_codebase respects max iterations limit."""

        # Mock response that always needs more exploration (low confidence)
        async def mock_agent_run(task):
            mock_result = Mock()
            mock_result.messages = [
                Mock(
                    content="""{
                "need_shell_execution": true,
                "shell_commands": ["ls"],
                "key_findings": ["Still exploring"],
                "current_analysis": "Need more exploration",
                "confidence_level": 3,
                "next_focus_areas": "Continue exploring"
            }"""
                )
            ]
            return mock_result

        analyzer._agent.run = mock_agent_run

        mock_shell_exec.return_value = [
            {
                "command": "ls",
                "success": True,
                "stdout": "file.py",
                "stderr": "",
                "error": None,
            }
        ]

        # Mock asyncio.run to properly handle the coroutine
        with patch("asyncio.run") as mock_async_run:
            call_count = [0]

            def run_mock(coro):
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(coro)
                    call_count[0] += 1
                    return result
                finally:
                    loop.close()

            mock_async_run.side_effect = run_mock

            result = analyzer.analyze_codebase("Complex analysis", "/test/path")

        # Should stop at max iterations (10) + 1 for final synthesis
        assert call_count[0] == 11
        assert "Iterations: 10" in result

    def test_build_iteration_prompt_includes_context(self, analyzer):
        """Test _build_iteration_prompt includes all necessary context."""
        query = "Test query"
        codebase_path = "/test/path"
        iteration = 2
        context = [{"iteration": 1, "llm_decision": {"confidence_level": 5}}]
        shell_history = [
            {
                "iteration": 1,
                "results": [{"command": "ls", "success": True, "stdout": "file.py"}],
            }
        ]
        shared_findings = ["Finding 1", "Finding 2"]
        convergence = {
            "sufficient_code_coverage": True,
            "question_answered": False,
            "confidence_threshold_met": True,
        }
        specialist_feedback = "Focus on classes"

        prompt = analyzer._build_iteration_prompt(
            query,
            codebase_path,
            iteration,
            context,
            shell_history,
            shared_findings,
            convergence,
            specialist_feedback,
        )

        # Verify prompt includes all context
        assert query in prompt
        assert codebase_path in prompt
        assert "ITERATION 2" in prompt
        assert "Finding 1" in prompt
        assert "Finding 2" in prompt
        assert "Focus on classes" in prompt
        assert "Code coverage sufficient: True" in prompt  # Fixed format
        assert "Previous confidence: 5" in prompt

    def test_extract_json_from_response_markdown_format(self, analyzer):
        """Test JSON extraction from markdown code blocks."""
        response_with_markdown = """
        Here is my analysis:

        ```json
        {
            "need_shell_execution": true,
            "confidence_level": 8
        }
        ```

        That's my response.
        """

        result = analyzer._extract_json_from_response(response_with_markdown)

        assert '"need_shell_execution": true' in result
        assert '"confidence_level": 8' in result

    def test_extract_json_from_response_plain_json(self, analyzer):
        """Test JSON extraction from plain JSON response."""
        plain_json = '{"need_shell_execution": false, "confidence_level": 9}'

        result = analyzer._extract_json_from_response(plain_json)

        assert result == plain_json

    def test_knowledge_base_accumulation_across_iterations(self, analyzer):
        """Test that key findings accumulate across iterations in the knowledge base."""
        # This tests the collaborative knowledge base feature
        llm_decision_1 = {
            "key_findings": ["Finding A", "Finding B"],
            "confidence_level": 5,
            "need_shell_execution": False,
        }

        llm_decision_2 = {
            "key_findings": ["Finding A", "Finding B", "Finding C"],
            "confidence_level": 8,
            "need_shell_execution": False,
        }

        context = [
            {"iteration": 1, "llm_decision": llm_decision_1},
            {"iteration": 2, "llm_decision": llm_decision_2},
        ]

        # Test final synthesis includes accumulated findings
        result = analyzer._synthesize_final_response(
            "test query", context, llm_decision_2["key_findings"], {}
        )

        assert "Finding A" in result
        assert "Finding B" in result
        assert "Finding C" in result
        assert "Knowledge base size: 3 findings" in result
