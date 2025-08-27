"""
Unit tests for Task Specialist agent.

Tests the initialization, configuration, and basic logic components of the
Task Specialist agent without LLM dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from src.codebase_agent.agents.task_specialist import TaskSpecialist


class TestTaskSpecialist:
    """Test suite for TaskSpecialist class."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return {
            "model": "gpt-4",
            "api_key": "test_key", 
            "temperature": 0.1
        }
    
    @pytest.fixture
    def task_specialist(self, sample_config):
        """Create TaskSpecialist instance for testing."""
        with patch('src.codebase_agent.agents.task_specialist.AssistantAgent'):
            specialist = TaskSpecialist(sample_config)
            return specialist
    
    def test_initialization(self, sample_config):
        """Test TaskSpecialist initialization."""
        with patch('src.codebase_agent.agents.task_specialist.AssistantAgent') as mock_agent:
            specialist = TaskSpecialist(sample_config)
            
            assert specialist.config == sample_config
            assert specialist.review_count == 0
            assert specialist.max_reviews == 3
            
            # Verify AutoGen agent was created
            mock_agent.assert_called_once()
    
    def test_system_message_content(self, task_specialist):
        """Test that system message contains required review guidance."""
        system_message = task_specialist._get_system_message()
        
        # Check for role definition
        assert "Task Specialist" in system_message
        assert "project manager" in system_message
        
        # Check for review criteria
        assert "REVIEW CRITERIA" in system_message
        assert "Identification of existing related functionality" in system_message
        assert "Clear integration points" in system_message
        assert "Specific implementation steps" in system_message
        assert "Potential conflicts or issues" in system_message
        
        # Check for feedback guidelines
        assert "FEEDBACK GUIDELINES" in system_message
        assert "abstract, high-level guidance" in system_message
        assert "Focus on missing information areas" in system_message
        assert "WHAT information is missing, not HOW to find it" in system_message
        
        # Check for examples
        assert "FEEDBACK EXAMPLES" in system_message
        assert "Good:" in system_message
        assert "Bad:" in system_message
    
    def test_assess_completeness_high_score(self, task_specialist):
        """Test completeness assessment with comprehensive report."""
        comprehensive_report = """
        Analysis found existing authentication system with current implementation.
        Integration points identified through interface analysis.
        Recommended implementation approach follows established patterns.
        Potential conflicts identified with legacy code considerations.
        Code examples and patterns documented from structure analysis.
        Architecture understanding demonstrated through framework analysis.
        Dependencies and library compatibility assessed through requirements.
        """
        
        score, missing = task_specialist._assess_completeness(
            comprehensive_report, "implement OAuth authentication"
        )
        
        assert score >= 0.8
        assert len(missing) <= 2  # Should have few or no missing areas
    
    def test_assess_completeness_low_score(self, task_specialist):
        """Test completeness assessment with minimal report."""
        minimal_report = "Brief analysis completed. Some files found."
        
        score, missing = task_specialist._assess_completeness(
            minimal_report, "implement OAuth authentication"
        )
        
        assert score < 0.5
        assert len(missing) > 3  # Should have multiple missing areas
    
    def test_assess_completeness_auth_specific(self, task_specialist):
        """Test completeness assessment for authentication tasks."""
        report_without_security = """
        Analysis found existing functionality and integration points.
        Implementation recommendations provided with code patterns.
        Architecture understanding demonstrated.
        """
        
        score, missing = task_specialist._assess_completeness(
            report_without_security, "implement OAuth authentication"
        )
        
        # Should detect missing security considerations for auth tasks
        assert any("security" in area for area in missing)
        assert score < 1.0  # Should be penalized for missing security
    
    def test_assess_completeness_api_specific(self, task_specialist):
        """Test completeness assessment for API tasks."""
        report_without_endpoints = """
        Analysis found existing functionality and integration points.
        Implementation recommendations provided with code patterns.
        Architecture understanding demonstrated.
        """
        
        score, missing = task_specialist._assess_completeness(
            report_without_endpoints, "create REST API endpoints"
        )
        
        # Should detect missing API endpoint considerations
        assert any("endpoint" in area for area in missing)
        assert score < 1.0  # Should be penalized for missing endpoint design
    
    def test_generate_acceptance_feedback(self, task_specialist):
        """Test acceptance feedback generation."""
        feedback = task_specialist._generate_acceptance_feedback(0.85)
        
        assert "ACCEPTED" in feedback
        assert "0.85" in feedback
        assert "sufficient completeness" in feedback
        assert "meets the standards" in feedback
    
    def test_generate_rejection_feedback(self, task_specialist):
        """Test rejection feedback generation."""
        missing_areas = [
            "existing related functionality identification",
            "clear integration points",
            "specific implementation steps"
        ]
        
        feedback = task_specialist._generate_rejection_feedback(
            missing_areas, "implement OAuth authentication"
        )
        
        assert "REQUIRES DEEPER ANALYSIS" in feedback
        assert "incomplete for providing actionable implementation guidance" in feedback
        assert "existing related functionality identification" in feedback
        assert "clear integration points" in feedback
        assert "specific implementation steps" in feedback
    
    def test_get_task_specific_guidance_auth(self, task_specialist):
        """Test task-specific guidance for authentication tasks."""
        guidance = task_specialist._get_task_specific_guidance(
            "implement OAuth authentication"
        )
        
        assert "user management" in guidance
        assert "session handling" in guidance
        assert "security measures" in guidance
        assert "authentication flows" in guidance
        assert "database schema" in guidance
    
    def test_get_task_specific_guidance_api(self, task_specialist):
        """Test task-specific guidance for API tasks."""
        guidance = task_specialist._get_task_specific_guidance(
            "create REST API endpoints"
        )
        
        assert "API structure" in guidance
        assert "routing patterns" in guidance
        assert "middleware" in guidance
        assert "request/response" in guidance
        assert "error handling" in guidance
    
    def test_get_task_specific_guidance_database(self, task_specialist):
        """Test task-specific guidance for database tasks."""
        guidance = task_specialist._get_task_specific_guidance(
            "design database models"
        )
        
        assert "data model relationships" in guidance
        assert "migration patterns" in guidance
        assert "ORM usage" in guidance
        assert "database interaction" in guidance
    
    def test_get_task_specific_guidance_frontend(self, task_specialist):
        """Test task-specific guidance for frontend tasks."""
        guidance = task_specialist._get_task_specific_guidance(
            "build React components"
        )
        
        assert "component structure" in guidance
        assert "state management" in guidance
        assert "routing" in guidance
        assert "styling" in guidance
    
    def test_review_analysis_accept_first_review(self, task_specialist):
        """Test accepting analysis on first review."""
        comprehensive_report = """
        Existing authentication mechanisms found with current implementation patterns.
        Clear integration points identified for connecting new OAuth system.
        Specific implementation steps recommended following project conventions.
        Potential conflicts assessed with consideration for backward compatibility.
        Concrete code examples extracted from existing authentication patterns.
        Architecture understanding demonstrated through framework analysis.
        Dependencies evaluated for compatibility with current requirements.
        """
        
        is_complete, feedback, confidence = task_specialist.review_analysis(
            comprehensive_report, "implement OAuth authentication", 1
        )
        
        assert is_complete
        assert "ACCEPTED" in feedback
        assert confidence >= 0.8
        assert task_specialist.review_count == 1
    
    def test_review_analysis_reject_first_review(self, task_specialist):
        """Test rejecting analysis on first review."""
        incomplete_report = "Brief analysis completed. Some files examined."
        
        is_complete, feedback, confidence = task_specialist.review_analysis(
            incomplete_report, "implement OAuth authentication", 1
        )
        
        assert not is_complete
        assert "REQUIRES DEEPER ANALYSIS" in feedback
        assert confidence < 0.8
        assert task_specialist.review_count == 1
        assert "Missing areas that need attention:" in feedback
    
    def test_review_analysis_force_accept_max_reviews(self, task_specialist):
        """Test force accepting analysis at maximum reviews."""
        incomplete_report = "Still incomplete analysis."
        
        is_complete, feedback, confidence = task_specialist.review_analysis(
            incomplete_report, "implement OAuth authentication", 3
        )
        
        assert is_complete  # Should be force accepted
        assert "maximum review limit reached" in feedback
        assert confidence == 0.7  # Default force accept confidence
        assert task_specialist.review_count == 3
    
    def test_review_analysis_second_review(self, task_specialist):
        """Test second review iteration."""
        improved_report = """
        Enhanced analysis with existing functionality identified.
        Integration points clarified through deeper examination.
        Implementation approach detailed with specific steps.
        Some potential issues identified but need more detail.
        Code patterns found but examples could be more concrete.
        """
        
        is_complete, feedback, confidence = task_specialist.review_analysis(
            improved_report, "implement OAuth authentication", 2
        )
        
        # Result depends on completeness score, but should handle second review properly
        assert task_specialist.review_count == 2
        assert "Review 2/3" in feedback or "ACCEPTED" in feedback
    
    def test_reset_review_count(self, task_specialist):
        """Test review count reset functionality."""
        task_specialist.review_count = 2
        
        task_specialist.reset_review_count()
        
        assert task_specialist.review_count == 0
    
    def test_has_reviews_remaining_property(self, task_specialist):
        """Test has_reviews_remaining property."""
        # Initially should have reviews remaining
        assert task_specialist.has_reviews_remaining
        
        # Set to max reviews
        task_specialist.review_count = 3
        assert not task_specialist.has_reviews_remaining
        
        # Set below max
        task_specialist.review_count = 2
        assert task_specialist.has_reviews_remaining
    
    def test_agent_property(self, task_specialist):
        """Test that agent property returns AutoGen agent."""
        agent = task_specialist.agent
        assert agent is not None
        assert hasattr(agent, 'name')
    
    def test_feedback_limit_missing_areas(self, task_specialist):
        """Test that feedback limits missing areas to top 5."""
        # Create many missing areas
        missing_areas = [f"missing area {i}" for i in range(10)]
        
        feedback = task_specialist._generate_rejection_feedback(
            missing_areas, "test task"
        )
        
        # Count occurrences of "missing area" in feedback
        missing_count = feedback.count("missing area")
        assert missing_count <= 5  # Should be limited to 5
