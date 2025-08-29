"""
Unit tests for Agent Manager.

Tests the orchestration logic, review cycles, and agent coordination.
"""

from unittest.mock import Mock, patch

import pytest

from codebase_agent.agents.manager import AgentManager
from codebase_agent.config.configuration import ConfigurationManager


class TestAgentManager:
    """Test cases for AgentManager class."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock configuration manager."""
        config_manager = Mock(spec=ConfigurationManager)
        config_manager.get_model_client.return_value = {
            "model": "gpt-4",
            "api_key": "test-key",
            "base_url": "https://api.openai.com/v1",
        }
        return config_manager

    @pytest.fixture
    def agent_manager(self, mock_config_manager):
        """Create an AgentManager instance with mocked dependencies."""
        return AgentManager(mock_config_manager)

    def test_initialization(self, mock_config_manager):
        """Test AgentManager initialization."""
        manager = AgentManager(mock_config_manager)

        assert manager.config_manager == mock_config_manager
        assert manager.max_specialist_reviews == 3
        assert manager.code_analyzer is None
        assert manager.task_specialist is None

    @patch("codebase_agent.agents.manager.ShellTool")
    @patch("codebase_agent.agents.manager.CodeAnalyzer")
    @patch("codebase_agent.agents.manager.TaskSpecialist")
    def test_initialize_agents_success(
        self,
        mock_task_specialist_class,
        mock_code_analyzer_class,
        mock_shell_tool_class,
        agent_manager,
    ):
        """Test successful agent initialization."""
        # Setup mocks
        mock_code_analyzer = Mock()
        mock_task_specialist = Mock()
        mock_shell_tool = Mock()
        mock_code_analyzer_class.return_value = mock_code_analyzer
        mock_task_specialist_class.return_value = mock_task_specialist
        mock_shell_tool_class.return_value = mock_shell_tool

        # Initialize agents
        agent_manager.initialize_agents()

        # Verify initialization
        assert agent_manager.code_analyzer == mock_code_analyzer
        assert agent_manager.task_specialist == mock_task_specialist

        # Verify agents were created with correct config
        expected_model_client = agent_manager.config_manager.get_model_client()
        mock_shell_tool_class.assert_called_once_with(".")
        mock_code_analyzer_class.assert_called_once_with(
            expected_model_client, mock_shell_tool
        )
        mock_task_specialist_class.assert_called_once_with(expected_model_client)

    @patch("codebase_agent.agents.manager.ShellTool")
    @patch("codebase_agent.agents.manager.CodeAnalyzer")
    def test_initialize_agents_failure(
        self, mock_code_analyzer_class, mock_shell_tool_class, agent_manager
    ):
        """Test agent initialization failure."""
        # Make CodeAnalyzer initialization fail
        mock_code_analyzer_class.side_effect = Exception("LLM connection failed")

        # Should raise exception
        with pytest.raises(Exception, match="LLM connection failed"):
            agent_manager.initialize_agents()

    def test_get_agent_not_initialized(self, agent_manager):
        """Test get_agent when agents are not initialized."""
        with pytest.raises(RuntimeError, match="Agents not initialized"):
            agent_manager.get_agent("code_analyzer")

    def test_get_agent_invalid_name(self, agent_manager):
        """Test get_agent with invalid agent name."""
        # Mock initialized agents
        agent_manager.code_analyzer = Mock()
        agent_manager.task_specialist = Mock()

        with pytest.raises(ValueError, match="Unknown agent name: invalid"):
            agent_manager.get_agent("invalid")

    def test_get_agent_success(self, agent_manager):
        """Test successful agent retrieval."""
        # Mock initialized agents
        mock_code_analyzer = Mock()
        mock_task_specialist = Mock()
        agent_manager.code_analyzer = mock_code_analyzer
        agent_manager.task_specialist = mock_task_specialist

        # Test retrieval
        assert agent_manager.get_agent("code_analyzer") == mock_code_analyzer
        assert agent_manager.get_agent("task_specialist") == mock_task_specialist

    def test_process_query_not_initialized(self, agent_manager):
        """Test process_query_with_review_cycle when agents are not initialized."""
        with pytest.raises(RuntimeError, match="Agents not initialized"):
            agent_manager.process_query_with_review_cycle("test query", "/test/path")

    def test_process_query_accepted_first_review(self, agent_manager):
        """Test query processing when analysis is accepted on first review."""
        # Mock initialized agents
        mock_code_analyzer = Mock()
        mock_task_specialist = Mock()
        agent_manager.code_analyzer = mock_code_analyzer
        agent_manager.task_specialist = mock_task_specialist

        # Setup mock responses
        analysis_result = "Detailed analysis of the codebase..."
        review_result = (
            True,
            "Good analysis coverage",
            0.85,
        )  # (is_complete, feedback, confidence)

        mock_code_analyzer.analyze_codebase.return_value = analysis_result
        mock_task_specialist.review_analysis.return_value = review_result

        # Execute
        result = agent_manager.process_query_with_review_cycle(
            "test query", "/test/path"
        )

        # Verify
        mock_code_analyzer.analyze_codebase.assert_called_once_with(
            "test query", "/test/path", None
        )
        mock_task_specialist.review_analysis.assert_called_once_with(
            analysis_result, "test query", 1
        )

        assert "Detailed analysis of the codebase..." in result
        assert "Good analysis coverage" in result

    def test_process_query_rejected_then_accepted(self, agent_manager):
        """Test query processing with one rejection followed by acceptance."""
        # Mock initialized agents
        mock_code_analyzer = Mock()
        mock_task_specialist = Mock()
        agent_manager.code_analyzer = mock_code_analyzer
        agent_manager.task_specialist = mock_task_specialist

        # Setup mock responses for two iterations
        analysis_results = ["Initial analysis...", "Improved analysis..."]
        review_results = [
            (False, "Need more details on authentication", 0.4),  # Rejected
            (True, "Much better coverage", 0.8),  # Accepted
        ]

        mock_code_analyzer.analyze_codebase.side_effect = analysis_results
        mock_task_specialist.review_analysis.side_effect = review_results

        # Execute
        result = agent_manager.process_query_with_review_cycle(
            "test query", "/test/path"
        )

        # Verify two analysis calls
        assert mock_code_analyzer.analyze_codebase.call_count == 2
        assert mock_task_specialist.review_analysis.call_count == 2

        # Check that second call included feedback
        second_call = mock_code_analyzer.analyze_codebase.call_args_list[1]
        assert second_call[0] == (
            "test query",
            "/test/path",
            "Need more details on authentication",
        )

        assert "Improved analysis..." in result
        assert "Much better coverage" in result

    def test_process_query_max_reviews_reached(self, agent_manager):
        """Test query processing when max reviews are reached."""
        # Mock initialized agents
        mock_code_analyzer = Mock()
        mock_task_specialist = Mock()
        agent_manager.code_analyzer = mock_code_analyzer
        agent_manager.task_specialist = mock_task_specialist

        # Setup mock responses - all rejected
        analysis_result = "Analysis result..."
        review_result = (False, "Still not good enough", 0.3)  # Always rejected

        mock_code_analyzer.analyze_codebase.return_value = analysis_result
        mock_task_specialist.review_analysis.return_value = review_result

        # Execute
        result = agent_manager.process_query_with_review_cycle(
            "test query", "/test/path"
        )

        # Verify max reviews were attempted
        assert mock_code_analyzer.analyze_codebase.call_count == 3
        assert mock_task_specialist.review_analysis.call_count == 3

        # Should include force acceptance note
        assert "maximum number of review cycles" in result

    def test_synthesize_final_response_accepted(self, agent_manager):
        """Test final response synthesis for accepted analysis."""
        analysis_result = "Comprehensive analysis..."
        feedback_message = "Excellent coverage of all aspects"
        original_query = "implement feature X"

        result = agent_manager._synthesize_final_response(
            analysis_result, True, feedback_message, original_query
        )

        assert "implement feature X" in result
        assert "Comprehensive analysis..." in result
        assert "Excellent coverage of all aspects" in result
        assert "maximum number of review cycles" not in result

    def test_synthesize_final_response_forced(self, agent_manager):
        """Test final response synthesis for forced acceptance."""
        analysis_result = "Analysis result..."
        feedback_message = "Still missing some details"
        original_query = "implement feature Y"

        result = agent_manager._synthesize_final_response(
            analysis_result, False, feedback_message, original_query
        )

        assert "implement feature Y" in result
        assert "Analysis result..." in result
        assert "maximum number of review cycles" in result
        assert "Still missing some details" in result

    @patch("codebase_agent.agents.manager.ShellTool")
    @patch("codebase_agent.agents.manager.CodeAnalyzer")
    @patch("codebase_agent.agents.manager.TaskSpecialist")
    def test_full_review_cycle_mocked(
        self,
        mock_task_specialist_class,
        mock_code_analyzer_class,
        mock_shell_tool_class,
        agent_manager,
    ):
        """Test full review cycle with mocked agent classes."""
        # Setup mock agent instances
        mock_code_analyzer = Mock()
        mock_task_specialist = Mock()
        mock_shell_tool = Mock()

        mock_code_analyzer_class.return_value = mock_code_analyzer
        mock_task_specialist_class.return_value = mock_task_specialist
        mock_shell_tool_class.return_value = mock_shell_tool

        # Setup realistic conversation responses
        analysis_responses = [
            "Initial analysis result",
            "Enhanced analysis after feedback",
        ]

        review_responses = [
            (False, "Need more details", 0.4),
            (True, "Much better", 0.85),
        ]

        # Configure mock responses
        mock_code_analyzer.analyze_codebase.side_effect = analysis_responses
        mock_task_specialist.review_analysis.side_effect = review_responses

        # Initialize and execute
        agent_manager.initialize_agents()
        result = agent_manager.process_query_with_review_cycle(
            "test query", "/test/path"
        )

        # Verify the process worked
        assert "Enhanced analysis after feedback" in result
        assert mock_code_analyzer.analyze_codebase.call_count == 2
        assert mock_task_specialist.review_analysis.call_count == 2
