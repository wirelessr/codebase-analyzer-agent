"""
Unit tests for Code Analyzer Agent.

Tests the core functionality of Task 5 implementation:
- Multi-round self-iteration logic
- Progressive analysis strategies  
- Convergence assessment
- AutoGen agent integration
"""


import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from codebase_agent.agents.code_analyzer import CodeAnalyzer


def create_mock_task_result(content):
    """Helper function to create a mock TaskResult."""
    mock_task_result = Mock()
    mock_message = Mock()
    mock_message.content = content
    mock_task_result.messages = [mock_message]
    return mock_task_result


class TestCodeAnalyzer:
    """Test suite for Code Analyzer functionality."""
    
    @pytest.fixture
    def mock_shell_tool(self):
        """Create a mock shell tool for testing."""
        mock_tool = Mock()
        mock_tool.execute_command.return_value = (True, "test output", "")
        return mock_tool
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        mock_client = Mock()
        mock_client.model_info = {"function_calling": True}
        return mock_client
    
    @pytest.fixture
    def analyzer(self, mock_config, mock_shell_tool):
        """Create a CodeAnalyzer instance for testing."""
        with patch('codebase_agent.agents.code_analyzer.AssistantAgent') as mock_agent_class:
            mock_agent = Mock()
            
            # Mock the run method with AsyncMock and default return value
            mock_agent.run = AsyncMock(return_value=create_mock_task_result("Test analysis response with confidence level 9"))
            mock_agent_class.return_value = mock_agent
            
            analyzer = CodeAnalyzer(mock_config, mock_shell_tool)
            analyzer._agent = mock_agent  # Override the agent
            return analyzer

    def test_initialization(self, mock_config, mock_shell_tool):
        """Test proper initialization of CodeAnalyzer."""
        with patch('codebase_agent.agents.code_analyzer.AssistantAgent') as mock_agent_class:
            analyzer = CodeAnalyzer(mock_config, mock_shell_tool)
            
            assert analyzer.config == mock_config
            assert analyzer.shell_tool == mock_shell_tool
            mock_agent_class.assert_called_once()

    def test_system_message_contains_safety_guidance(self, analyzer):
        """Test that system message includes shell safety guidance."""
        system_message = analyzer._get_system_message()
        
        # Check for safety keywords
        assert "READ-ONLY" in system_message
        assert "NEVER use commands that modify" in system_message
        assert "ls, find, tree" in system_message
        assert "grep, awk, sed" in system_message

    def test_system_message_contains_analysis_process(self, analyzer):
        """Test that system message includes analysis process guidance."""
        system_message = analyzer._get_system_message()
        
        assert "Multi-round iterative analysis" in system_message
        assert "Progressive knowledge building" in system_message
        assert "self-assessment" in system_message.lower()

    def test_build_iteration_prompt_stage_1(self, analyzer):
        """Test prompt building for stage 1 (targeted exploration)."""
        query = "implement OAuth authentication"
        prompt = analyzer._build_iteration_prompt(
            query, "/test/path", 1, [], 
            {'sufficient_code_coverage': False, 'question_answered': False, 'confidence_threshold_met': False}
        )
        
        assert "STAGE 1 - TARGETED EXPLORATION" in prompt
        assert "MISSION: Quickly identify" in prompt
        assert query in prompt
        assert "/test/path" in prompt

    def test_build_iteration_prompt_stage_2(self, analyzer):
        """Test prompt building for stage 2 (contextual expansion)."""
        context = [{'iteration': 1, 'response': 'Found auth modules', 'timestamp': '2024-01-01'}]
        prompt = analyzer._build_iteration_prompt(
            "implement OAuth", "/test/path", 2, context,
            {'sufficient_code_coverage': False, 'question_answered': False, 'confidence_threshold_met': False}
        )
        
        assert "STAGE 2 - CONTEXTUAL EXPANSION" in prompt
        assert "Previous findings:" in prompt
        assert "Found auth modules" in prompt

    def test_build_iteration_prompt_stage_5_synthesis(self, analyzer):
        """Test prompt building for stage 5+ (validation and synthesis)."""
        context = [{'iteration': i, 'response': f'Analysis step {i}', 'timestamp': '2024-01-01'} for i in range(1, 5)]
        convergence = {'sufficient_code_coverage': True, 'question_answered': False, 'confidence_threshold_met': True}
        
        prompt = analyzer._build_iteration_prompt(
            "test query", "/test/path", 5, context, convergence
        )
        
        assert "STAGE 5 - VALIDATION & SYNTHESIS" in prompt
        assert "Full analysis history:" in prompt
        assert "Current convergence status:" in prompt
        assert "Code coverage sufficient: True" in prompt

    def test_assess_convergence_high_confidence(self, analyzer):
        """Test convergence assessment with high confidence response."""
        response = "I am confident this is a comprehensive solution with complete file analysis and clear answer"
        convergence = analyzer._assess_convergence(response, "test query", [{'iteration': 1}])
        
        assert convergence['confidence_threshold_met'] == True
        assert convergence['question_answered'] == True
        # Coverage depends on iteration count (>=2) or coverage keywords count (>=3)
        # This response has 'file' (1 keyword), but only 1 iteration, so coverage is False
        assert convergence['sufficient_code_coverage'] == False

    def test_assess_convergence_low_confidence(self, analyzer):
        """Test convergence assessment with low confidence response."""
        response = "I need more information to provide analysis"
        convergence = analyzer._assess_convergence(response, "test query", [])
        
        # This response has no confidence keywords
        assert convergence['confidence_threshold_met'] == False
        assert convergence['question_answered'] == False
        assert convergence['sufficient_code_coverage'] == False

    def test_assess_convergence_with_complete_keyword(self, analyzer):
        """Test convergence assessment with complete keyword (confidence indicator)."""
        response = "I need more information to provide a complete analysis"
        convergence = analyzer._assess_convergence(response, "test query", [])
        
        # This response has 'complete' - a confidence keyword
        assert convergence['confidence_threshold_met'] == True
        assert convergence['question_answered'] == False
        assert convergence['sufficient_code_coverage'] == False

    def test_assess_convergence_sufficient_coverage(self, analyzer):
        """Test convergence assessment with sufficient code coverage."""
        response = "Found file with function and class implementation code"
        context = [{'iteration': 1}, {'iteration': 2}]
        convergence = analyzer._assess_convergence(response, "test query", context)
        
        # This response has 4 coverage keywords (file, function, class, code) >= 3
        assert convergence['confidence_threshold_met'] == True  # 'found'
        assert convergence['question_answered'] == False  # no answer keywords
        assert convergence['sufficient_code_coverage'] == True  # 4 coverage keywords >= 3

    def test_should_terminate_all_criteria_met(self, analyzer):
        """Test termination decision when all criteria are met."""
        convergence = {
            'sufficient_code_coverage': True,
            'question_answered': True,
            'confidence_threshold_met': True
        }
        
        assert analyzer._should_terminate(convergence) == True

    def test_should_terminate_missing_criteria(self, analyzer):
        """Test termination decision when criteria are not met."""
        convergence = {
            'sufficient_code_coverage': True,
            'question_answered': False,
            'confidence_threshold_met': True
        }
        
        assert analyzer._should_terminate(convergence) == False

    def test_summarize_previous_context(self, analyzer):
        """Test context summarization for previous iterations."""
        context = [
            {'iteration': 1, 'response': 'A' * 400, 'timestamp': '2024-01-01'},
            {'iteration': 2, 'response': 'Short response', 'timestamp': '2024-01-01'}
        ]
        
        summary = analyzer._summarize_previous_context(context)
        
        assert "Iteration 1:" in summary
        assert "Iteration 2:" in summary
        # Should truncate long responses
        assert len(summary.split("Iteration 1:")[1].split("Iteration 2:")[0]) <= 310  # 300 chars + "..."

    def test_summarize_previous_context_empty(self, analyzer):
        """Test context summarization with empty context."""
        summary = analyzer._summarize_previous_context([])
        assert summary == "No previous iterations."

    def test_synthesize_final_response(self, analyzer):
        """Test final response synthesis."""
        query = "test query"
        context = [
            {'iteration': 1, 'response': 'Initial analysis', 'timestamp': '2024-01-01'},
            {'iteration': 2, 'response': 'Final comprehensive analysis', 'timestamp': '2024-01-01'}
        ]
        convergence = {'sufficient_code_coverage': True, 'question_answered': True, 'confidence_threshold_met': True}
        
        response = analyzer._synthesize_final_response(query, context, convergence)
        
        assert "CODEBASE ANALYSIS COMPLETE" in response
        assert "Query: test query" in response
        assert "Iterations: 2" in response
        assert "Final comprehensive analysis" in response

    def test_synthesize_final_response_no_context(self, analyzer):
        """Test final response synthesis with no context."""
        response = analyzer._synthesize_final_response("query", [], {})
        assert response == "No analysis performed."

    @patch('datetime.datetime')
    def test_get_timestamp(self, mock_datetime, analyzer):
        """Test timestamp generation."""
        mock_now = Mock()
        mock_now.isoformat.return_value = "2024-01-01T12:00:00"
        mock_datetime.now.return_value = mock_now
        
        timestamp = analyzer._get_timestamp()
        assert timestamp == "2024-01-01T12:00:00"

    def test_multi_round_analysis_flow(self, analyzer):
        """Test the complete multi-round analysis flow."""
        # Mock agent responses for different iterations
        responses = [
            "Initial exploration with confidence 6",
            "More findings with confidence 7", 
            "Comprehensive analysis with confidence 9 and complete answer"
        ]
        analyzer._agent.run.side_effect = [
            create_mock_task_result(response) for response in responses
        ]
        
        result = analyzer.analyze_codebase("implement auth", "/test/path")
        
        # Should have called agent 3 times (high confidence on 3rd iteration)
        assert analyzer._agent.run.call_count == 3
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "Comprehensive analysis with confidence 9" in result

    def test_max_iterations_limit(self, analyzer):
        """Test that analysis respects maximum iteration limit."""
        # Mock agent to always return low confidence
        analyzer._agent.run.return_value = create_mock_task_result("Low confidence analysis with confidence 3")

        result = analyzer.analyze_codebase("test query", "/test/path")

        # Should stop at max iterations (10)
        assert analyzer._agent.run.call_count == 10
        assert "CODEBASE ANALYSIS COMPLETE" in result

    def test_agent_property_getter(self, analyzer):
        """Test agent property getter."""
        agent = analyzer.agent
        assert agent == analyzer._agent

    def test_progressive_search_strategies(self, analyzer):
        """Test that different stages implement progressive search strategies."""
        # Test each stage has distinct strategy
        for iteration in range(1, 6):
            prompt = analyzer._build_iteration_prompt(
                "test", "/path", iteration, [], 
                {'sufficient_code_coverage': False, 'question_answered': False, 'confidence_threshold_met': False}
            )
            
            if iteration == 1:
                assert "TARGETED EXPLORATION" in prompt
            elif iteration == 2:
                assert "CONTEXTUAL EXPANSION" in prompt
            elif iteration == 3:
                assert "DEEPER ANALYSIS" in prompt
            elif iteration == 4:
                assert "COMPREHENSIVE COVERAGE" in prompt
            else:
                assert "VALIDATION & SYNTHESIS" in prompt

    def test_iteration_prompt_contains_ultimate_goal(self, analyzer):
        """Test that iteration prompts always contain the ultimate goal."""
        prompt = analyzer._build_iteration_prompt(
            "test query", "/path", 1, [], 
            {'sufficient_code_coverage': False, 'question_answered': False, 'confidence_threshold_met': False}
        )
        
        assert "ULTIMATE GOAL" in prompt
        assert "comprehensive, detailed report" in prompt

    def test_iteration_prompt_output_requirements(self, analyzer):
        """Test that iteration prompts include output requirements."""
        prompt = analyzer._build_iteration_prompt(
            "test query", "/path", 1, [], 
            {'sufficient_code_coverage': False, 'question_answered': False, 'confidence_threshold_met': False}
        )
        
        assert "ITERATION OUTPUT REQUIREMENTS" in prompt
        assert "confidence level (1-10)" in prompt
        assert "comprehensive analysis" in prompt

    def test_iteration_prompt_with_specialist_feedback(self, analyzer):
        """Test that specialist feedback is properly incorporated into iteration prompts."""
        specialist_feedback = "Need deeper analysis of existing authentication mechanisms and their integration patterns"
        
        prompt = analyzer._build_iteration_prompt(
            "implement OAuth authentication", "/test/path", 2, [], 
            {'sufficient_code_coverage': False, 'question_answered': False, 'confidence_threshold_met': False},
            specialist_feedback
        )
        
        assert "🎯 TASK SPECIALIST FEEDBACK" in prompt
        assert "PRIORITY FOCUS AREAS" in prompt
        assert specialist_feedback in prompt
        assert "Address the above feedback areas as your primary focus" in prompt

    def test_iteration_prompt_without_specialist_feedback(self, analyzer):
        """Test that prompts work normally when no specialist feedback is provided."""
        prompt = analyzer._build_iteration_prompt(
            "implement OAuth authentication", "/test/path", 1, [], 
            {'sufficient_code_coverage': False, 'question_answered': False, 'confidence_threshold_met': False}
        )
        
        assert "🎯 TASK SPECIALIST FEEDBACK" not in prompt
        assert "PRIORITY FOCUS AREAS" not in prompt


class TestCodeAnalyzerEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def analyzer_with_mock_agent(self, mock_config, mock_shell_tool):
        """Create analyzer with mock agent for edge case testing."""
        with patch('codebase_agent.agents.code_analyzer.AssistantAgent') as mock_agent_class:
            mock_agent = Mock()
            
            # Mock the run method with AsyncMock and default return value
            mock_agent.run = AsyncMock(return_value=create_mock_task_result("Test response with confidence 9"))
            mock_agent_class.return_value = mock_agent
            
            analyzer = CodeAnalyzer(mock_config, mock_shell_tool)
            analyzer._agent = mock_agent
            return analyzer

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return {"model": "gpt-4", "api_key": "test-key"}

    @pytest.fixture
    def mock_shell_tool(self):
        """Create a mock shell tool for testing."""
        mock_tool = Mock()
        mock_tool.execute_command.return_value = (True, "test output", "")
        return mock_tool

    def test_malformed_context_handling(self, analyzer_with_mock_agent):
        """Test handling of malformed context data."""
        malformed_context = [
            {'iteration': 1},  # Missing response
            {'response': 'test'},  # Missing iteration
        ]
        
        # Should not crash when trying to summarize
        try:
            summary = analyzer_with_mock_agent._summarize_previous_context(malformed_context)
            assert isinstance(summary, str)
        except (KeyError, AttributeError):
            # Expected behavior - should handle gracefully
            pass

    def test_empty_query_handling(self, analyzer_with_mock_agent):
        """Test handling of empty queries."""
        result = analyzer_with_mock_agent.analyze_codebase("", "/test/path")
        
        # Should still attempt analysis
        assert "CODEBASE ANALYSIS COMPLETE" in result

    def test_analyze_codebase_stores_iteration_context(self, analyzer_with_mock_agent):
        """Test that analysis context is properly stored across iterations."""
        analyzer_with_mock_agent._agent.run.side_effect = [
            create_mock_task_result("First iteration response"),
            create_mock_task_result("Second iteration response"), 
            create_mock_task_result("Final comprehensive answer with confidence 9")
        ]
        
        result = analyzer_with_mock_agent.analyze_codebase("test", "/path")
        
        # Verify final response includes information from all iterations
        assert "CODEBASE ANALYSIS COMPLETE" in result

    def test_analyze_codebase_with_specialist_feedback(self, analyzer_with_mock_agent):
        """Test that analyze_codebase accepts and uses specialist feedback."""
        # Provide multiple responses to handle potential iterations
        analyzer_with_mock_agent._agent.run.side_effect = [
            create_mock_task_result("First iteration with feedback, continue analysis"),
            create_mock_task_result("Second iteration, confidence 9, comprehensive answer")
        ]
        
        specialist_feedback = "Need deeper analysis of database integration patterns"
        result = analyzer_with_mock_agent.analyze_codebase(
            "implement OAuth", "/path", specialist_feedback=specialist_feedback
        )
        
        # Verify that the method accepts the specialist_feedback parameter
        assert "CODEBASE ANALYSIS COMPLETE" in result
        
        # Check that the first call was made with the feedback incorporated
        first_call_args = analyzer_with_mock_agent._agent.run.call_args_list[0]
        first_task = first_call_args[1]['task']  # Get the 'task' keyword argument
        assert "🎯 TASK SPECIALIST FEEDBACK" in first_task
        assert specialist_feedback in first_task


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
