"""
Unit tests for Task Specialist agent.

These tests validate the LLM-driven review behavior, prompt content, and
control flow (including force-accept after max reviews). Heuristic methods
are intentionally not tested as they were removed per design.
"""

import pytest
from unittest.mock import Mock, patch
from src.codebase_agent.agents.task_specialist import TaskSpecialist


class TestTaskSpecialist:
    """Test suite for TaskSpecialist class (LLM-driven version)."""

    @pytest.fixture
    def sample_config(self):
        return {"model": "gpt-4", "api_key": "test_key", "temperature": 0.1}

    @pytest.fixture
    def mock_agent(self):
        with patch('src.codebase_agent.agents.task_specialist.AssistantAgent') as MockAgent:
            instance = Mock()
            instance.name = "task_specialist"
            instance.on_messages = Mock()
            MockAgent.return_value = instance
            yield instance

    @pytest.fixture
    def task_specialist(self, sample_config, mock_agent):
        return TaskSpecialist(sample_config)

    def test_initialization(self, sample_config):
        with patch('src.codebase_agent.agents.task_specialist.AssistantAgent') as mock_cls:
            specialist = TaskSpecialist(sample_config)
            assert specialist.config == sample_config
            assert specialist.review_count == 0
            assert specialist.max_reviews == 3
            mock_cls.assert_called_once()

    def test_system_message_content(self, task_specialist):
        system_message = task_specialist._get_system_message()
        assert "Task Specialist" in system_message
        assert "project manager" in system_message
        assert "REVIEW CRITERIA" in system_message
        assert "Identification of existing related functionality" in system_message
        assert "Clear integration points" in system_message
        assert "Specific implementation steps" in system_message
        assert "Potential conflicts or issues" in system_message
        assert "FEEDBACK GUIDELINES" in system_message
        assert "abstract, high-level guidance" in system_message
        assert "WHAT information is missing, not HOW to find it" in system_message
        assert "FEEDBACK EXAMPLES" in system_message

    def test_build_review_prompt_contains_required_sections(self, task_specialist):
        prompt = task_specialist._build_review_prompt(
            task_description="implement OAuth authentication",
            analysis_report="Some analysis report...",
            review_number=1,
        )
        assert "REVIEW CONTEXT:" in prompt
        assert "ANALYSIS REPORT:" in prompt
        assert "REVIEW CRITERIA:" in prompt
        assert "OUTPUT FORMAT (MANDATORY):" in prompt
        assert "{\"is_complete\": true" in prompt  # example JSON

    def test_review_analysis_accept_llm_json(self, task_specialist, mock_agent):
        mock_agent.on_messages.return_value = '{"is_complete": true, "feedback": "Analysis accepted - looks good", "confidence": 0.9}'
        is_complete, feedback, confidence = task_specialist.review_analysis(
            analysis_report="Detailed analysis...",
            task_description="implement OAuth authentication",
            current_review_count=1,
        )
        assert is_complete is True
        assert feedback == "Analysis accepted - looks good"
        assert confidence == 0.9
        mock_agent.on_messages.assert_called_once()
        # Inspect that prompt likely had key markers
        called_args = mock_agent.on_messages.call_args[0][0]
        assert isinstance(called_args, list) and called_args[0]["role"] == "user"
        content = called_args[0]["content"]
        assert "REVIEW CONTEXT:" in content

    def test_review_analysis_reject_llm_json(self, task_specialist, mock_agent):
        mock_agent.on_messages.return_value = '{"is_complete": false, "feedback": "Need deeper analysis of integration points", "confidence": 0.55}'
        is_complete, feedback, confidence = task_specialist.review_analysis(
            analysis_report="Shallow analysis...",
            task_description="implement OAuth authentication",
            current_review_count=1,
        )
        assert is_complete is False
        assert "integration points" in feedback
        assert confidence == 0.55

    def test_review_analysis_unparsable_llm_response(self, task_specialist, mock_agent):
        mock_agent.on_messages.return_value = 'not a json response'
        is_complete, feedback, confidence = task_specialist.review_analysis(
            analysis_report="Some analysis...",
            task_description="any task",
            current_review_count=1,
        )
        assert is_complete is False
        assert feedback.startswith("Analysis review could not be completed")
        assert confidence == 0.0

    def test_review_analysis_force_accept_max_reviews(self, task_specialist, mock_agent):
        is_complete, feedback, confidence = task_specialist.review_analysis(
            analysis_report="Still incomplete",
            task_description="task",
            current_review_count=3,
        )
        assert is_complete is True
        assert "maximum review limit reached" in feedback
        assert confidence == 0.7
        mock_agent.on_messages.assert_not_called()

    def test_agent_property_exists(self, task_specialist):
        # Minimal check to ensure agent property is wired
        assert task_specialist.agent is not None
