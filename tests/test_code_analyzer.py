"""
Unit tests for Code Analyzer agent.

Tests the initialization, configuration, and basic logic components of the
Code Analyzer agent without LLM dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.codebase_agent.agents.code_analyzer import CodeAnalyzer


class TestCodeAnalyzer:
    """Test suite for CodeAnalyzer class."""
    
    @pytest.fixture
    def mock_shell_tool(self):
        """Create a mock shell tool for testing."""
        mock_tool = Mock()
        mock_tool.execute_command.return_value = (True, "test output", "")
        mock_tool.working_directory = "/test/path"
        return mock_tool
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {
            "model": "gpt-4",
            "api_key": "test_key",
            "temperature": 0.1
        }
    
    @pytest.fixture
    def code_analyzer(self, sample_config, mock_shell_tool):
        """Create CodeAnalyzer instance for testing."""
        with patch('src.codebase_agent.agents.code_analyzer.AssistantAgent'):
            analyzer = CodeAnalyzer(sample_config, mock_shell_tool)
            return analyzer
    
    def test_initialization(self, sample_config, mock_shell_tool):
        """Test CodeAnalyzer initialization."""
        with patch('src.codebase_agent.agents.code_analyzer.AssistantAgent') as mock_agent:
            analyzer = CodeAnalyzer(sample_config, mock_shell_tool)
            
            assert analyzer.config == sample_config
            assert analyzer.shell_tool == mock_shell_tool
            assert analyzer.current_iteration == 0
            assert analyzer.knowledge_base == []
            assert analyzer.confidence_level == 0.0
            assert analyzer.max_iterations == 5
            assert analyzer.confidence_threshold == 0.8
            
            # Verify AutoGen agent was created
            mock_agent.assert_called_once()
    
    def test_system_message_content(self, code_analyzer):
        """Test that system message contains required safety guidance."""
        system_message = code_analyzer._get_system_message()
        
        # Check for safety guidance
        assert "READ-ONLY commands" in system_message
        assert "ls, find, tree" in system_message
        assert "cat, head, tail" in system_message
        assert "grep, awk, sed" in system_message
        assert "NEVER use commands that modify files" in system_message
        
        # Check for analysis process guidance
        assert "Multi-round iterative analysis" in system_message
        assert "self-assessment" in system_message.lower()
        assert "Confidence level" in system_message
    
    def test_reset_analysis_state(self, code_analyzer):
        """Test analysis state reset functionality."""
        # Set some state
        code_analyzer.current_iteration = 3
        code_analyzer.knowledge_base = ["finding1", "finding2"]
        code_analyzer.confidence_level = 0.5
        
        # Reset state
        code_analyzer._reset_analysis_state()
        
        # Verify reset
        assert code_analyzer.current_iteration == 0
        assert code_analyzer.knowledge_base == []
        assert code_analyzer.confidence_level == 0.0
    
    def test_extract_task_keywords_auth(self, code_analyzer):
        """Test keyword extraction for authentication tasks."""
        task = "implement OAuth authentication for user login"
        keywords = code_analyzer._extract_task_keywords(task)
        
        expected_keywords = {'auth', 'user', 'login', 'password', 'session'}
        assert any(keyword in keywords for keyword in expected_keywords)
    
    def test_extract_task_keywords_api(self, code_analyzer):
        """Test keyword extraction for API tasks."""
        task = "create REST API endpoints for data access"
        keywords = code_analyzer._extract_task_keywords(task)
        
        expected_keywords = {'api', 'route', 'endpoint', 'controller'}
        assert any(keyword in keywords for keyword in expected_keywords)
    
    def test_extract_task_keywords_database(self, code_analyzer):
        """Test keyword extraction for database tasks."""
        task = "design database models for user management"
        keywords = code_analyzer._extract_task_keywords(task)
        
        expected_keywords = {'model', 'database', 'orm', 'migration'}
        assert any(keyword in keywords for keyword in expected_keywords)
    
    def test_extract_task_keywords_frontend(self, code_analyzer):
        """Test keyword extraction for frontend tasks."""
        task = "build React components for dashboard"
        keywords = code_analyzer._extract_task_keywords(task)
        
        expected_keywords = {'component', 'react', 'frontend', 'jsx'}
        assert any(keyword in keywords for keyword in expected_keywords)
    
    def test_update_knowledge_base(self, code_analyzer):
        """Test knowledge base update functionality."""
        # Add some reports
        reports = [f"Report {i}" for i in range(7)]
        
        for report in reports:
            code_analyzer._update_knowledge_base(report)
        
        # Should keep only last 5 reports
        assert len(code_analyzer.knowledge_base) == 5
        assert code_analyzer.knowledge_base == reports[-5:]
    
    def test_assess_analysis_completeness_early_iteration(self, code_analyzer):
        """Test completeness assessment for early iterations."""
        code_analyzer.current_iteration = 1
        code_analyzer.knowledge_base = ["report1"]
        
        is_complete, confidence = code_analyzer._assess_analysis_completeness("test task")
        
        # Early iteration should have low confidence
        assert confidence < 0.5
        assert not is_complete
    
    def test_assess_analysis_completeness_later_iteration(self, code_analyzer):
        """Test completeness assessment for later iterations."""
        code_analyzer.current_iteration = 4
        code_analyzer.knowledge_base = ["report1", "report2", "report3", "report4"]
        
        is_complete, confidence = code_analyzer._assess_analysis_completeness("test task")
        
        # Later iteration with more knowledge should have higher confidence
        assert confidence >= 0.8
        assert is_complete
    
    def test_assess_analysis_completeness_max_iterations(self, code_analyzer):
        """Test completeness assessment at max iterations."""
        code_analyzer.current_iteration = 5  # max_iterations
        code_analyzer.knowledge_base = ["report1"]
        
        is_complete, confidence = code_analyzer._assess_analysis_completeness("test task")
        
        # Should be complete even with low confidence due to max iterations
        assert is_complete
    
    def test_execute_analysis_commands_iteration_1(self, code_analyzer, mock_shell_tool):
        """Test command execution logic for first iteration."""
        code_analyzer.current_iteration = 1
        
        # Mock successful command execution
        mock_shell_tool.execute_command.side_effect = [
            (True, "file1.py\nfile2.py\nfile3.py", ""),  # find command
            (True, "total 8\ndrwxr-xr-x  2 user user 4096", "")  # ls command
        ]
        
        report = code_analyzer._execute_analysis_commands("implement auth")
        
        assert "Analysis Iteration 1 Report" in report
        assert "Python files found" in report
        assert "Project root structure" in report
        
        # Verify commands were called
        assert mock_shell_tool.execute_command.call_count >= 2
    
    def test_execute_analysis_commands_with_keywords(self, code_analyzer, mock_shell_tool):
        """Test command execution with keyword-based search."""
        code_analyzer.current_iteration = 2
        
        # Mock command execution for keyword search
        mock_shell_tool.execute_command.side_effect = [
            (True, "auth.py\nuser.py", ""),  # auth search
            (True, "user.py\nmodels.py", ""),  # user search  
            (True, "", "")  # empty result
        ]
        
        report = code_analyzer._execute_analysis_commands("implement OAuth authentication")
        
        assert "Files containing" in report
        
        # Should execute keyword searches
        call_args_list = [call[0][0] for call in mock_shell_tool.execute_command.call_args_list]
        assert any("grep" in call for call in call_args_list)
    
    def test_execute_analysis_commands_error_handling(self, code_analyzer, mock_shell_tool):
        """Test error handling in command execution."""
        code_analyzer.current_iteration = 1
        
        # Mock command failure
        mock_shell_tool.execute_command.side_effect = Exception("Command failed")
        
        report = code_analyzer._execute_analysis_commands("test task")
        
        assert "Command execution error" in report
    
    def test_generate_final_report(self, code_analyzer):
        """Test final report generation."""
        code_analyzer.current_iteration = 3
        code_analyzer.confidence_level = 0.85
        code_analyzer.knowledge_base = ["Finding 1", "Finding 2", "Finding 3"]
        
        report = code_analyzer._generate_final_report("implement OAuth")
        
        assert "# Codebase Analysis Report" in report
        assert "Task: implement OAuth" in report
        assert "Total iterations performed: 3" in report
        assert "Final confidence level: 0.85" in report
        assert "Analysis status: Complete" in report
        assert "Finding 1" in report
        assert "Finding 2" in report
        assert "Finding 3" in report
    
    def test_analyze_codebase_integration(self, code_analyzer, mock_shell_tool):
        """Test the full analyze_codebase method integration."""
        # Mock shell commands to return quickly
        mock_shell_tool.execute_command.return_value = (True, "test output", "")
        
        # Override confidence threshold for quick completion
        code_analyzer.confidence_threshold = 0.3
        
        report, is_complete, iteration_count = code_analyzer.analyze_codebase(
            "test task", "/test/path"
        )
        
        assert isinstance(report, str)
        assert isinstance(is_complete, bool)
        assert isinstance(iteration_count, int)
        assert iteration_count > 0
        assert "# Codebase Analysis Report" in report
    
    def test_agent_property(self, code_analyzer):
        """Test that agent property returns AutoGen agent."""
        agent = code_analyzer.agent
        assert agent is not None
        assert hasattr(agent, 'name')
