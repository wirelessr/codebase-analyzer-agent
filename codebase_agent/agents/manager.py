"""
Agent Manager for orchestrating multi-agent codebase analysis.

This module implements the central orchestration layer that coordinates
Code Analyzer and Task Specialist through a review cycle mechanism.
"""

import logging
from typing import Any

from ..config.configuration import ConfigurationManager
from ..tools.shell_tool import ShellTool
from .code_analyzer import CodeAnalyzer
from .task_specialist import TaskSpecialist


class AgentManager:
    """
    Orchestrates multi-agent codebase analysis with review cycles.

    The manager coordinates between Code Analyzer and Task Specialist,
    implementing a review cycle where the specialist can provide feedback
    for up to 3 iterations, after which the analysis is forcibly accepted.
    """

    def __init__(self, config_manager: ConfigurationManager):
        """
        Initialize the Agent Manager.

        Args:
            config_manager: Configuration manager for LLM settings
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.max_specialist_reviews = 3

        # Initialize agents
        self.code_analyzer: CodeAnalyzer | None = None
        self.task_specialist: TaskSpecialist | None = None

    def initialize_agents(self) -> None:
        """Initialize all specialized agents with their configurations."""
        try:
            model_client = self.config_manager.get_model_client()

            # Create shell tool (we'll use current directory as default,
            # but this will be overridden by the actual codebase path during analysis)
            shell_tool = ShellTool(".")

            self.code_analyzer = CodeAnalyzer(model_client, shell_tool)
            self.task_specialist = TaskSpecialist(model_client)

            self.logger.info("Successfully initialized all agents")

        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise

    def process_query_with_review_cycle(
        self, query: str, codebase_path: str
    ) -> tuple[str, dict]:
        """
        Process user query through multi-round analysis and review cycle.

        This method implements the core review cycle:
        1. Code Analyzer analyzes the codebase
        2. Task Specialist reviews the analysis
        3. If not satisfied, specialist provides feedback and analyzer re-analyzes
        4. Repeat up to 3 times, then force accept

        Args:
            query: User's task description
            codebase_path: Path to the codebase to analyze

        Returns:
            Tuple of (final_response, statistics) where statistics contains:
            - total_review_cycles: Total number of review cycles executed
            - rejections: Number of times Task Specialist rejected the analysis
            - final_acceptance_type: 'accepted' or 'forced'
            - final_confidence: Final confidence score from Task Specialist
        """
        if not self.code_analyzer or not self.task_specialist:
            raise RuntimeError(
                "Agents not initialized. Call initialize_agents() first."
            )

        self.logger.info(f"Starting analysis for query: {query}")
        self.logger.info(f"Codebase path: {codebase_path}")

        # Initialize statistics tracking
        statistics = {
            "total_review_cycles": 0,
            "rejections": 0,
            "final_acceptance_type": "unknown",
            "final_confidence": 0.0,
        }

        specialist_feedback = None
        review_count = 0

        while review_count < self.max_specialist_reviews:
            review_count += 1
            statistics["total_review_cycles"] = review_count

            self.logger.info(
                f"Starting review cycle {review_count}/{self.max_specialist_reviews}"
            )

            # Code Analyzer analyzes the codebase
            self.logger.info("Code Analyzer starting analysis...")
            analysis_result = self.code_analyzer.analyze_codebase(
                query, codebase_path, specialist_feedback
            )

            # Task Specialist reviews the analysis
            self.logger.info("Task Specialist reviewing analysis...")
            (
                is_complete,
                feedback_message,
                confidence_score,
            ) = self.task_specialist.review_analysis(
                analysis_result, query, review_count
            )

            # Check if specialist accepts the analysis
            if is_complete:
                statistics["final_acceptance_type"] = "accepted"
                statistics["final_confidence"] = confidence_score
                self.logger.info(
                    f"Analysis accepted on review cycle {review_count} with confidence {confidence_score:.2f}"
                )
                final_response = self._synthesize_final_response(
                    analysis_result, True, feedback_message, query
                )
                return final_response, statistics

            # Track rejection
            statistics["rejections"] += 1

            # If this was the last allowed review, force accept
            if review_count >= self.max_specialist_reviews:
                statistics["final_acceptance_type"] = "forced"
                statistics["final_confidence"] = confidence_score
                self.logger.warning(
                    f"Max reviews ({self.max_specialist_reviews}) reached. Force accepting analysis."
                )
                final_response = self._synthesize_final_response(
                    analysis_result, False, feedback_message, query
                )
                return final_response, statistics

            # Get feedback and prepare for next iteration
            self.logger.info(f"Analysis rejected. Feedback: {feedback_message}")
            specialist_feedback = feedback_message

        # This should never be reached due to the force accept logic above
        statistics["final_acceptance_type"] = "forced"
        statistics["final_confidence"] = confidence_score
        final_response = self._synthesize_final_response(
            analysis_result, False, feedback_message, query
        )
        return final_response, statistics

    def _synthesize_final_response(
        self,
        analysis_result: str,
        is_accepted: bool,
        feedback_message: str,
        original_query: str,
    ) -> str:
        """
        Synthesize the final response from analysis and review results.

        Args:
            analysis_result: The final analysis from Code Analyzer
            is_accepted: Whether the analysis was accepted by the specialist
            feedback_message: The feedback from Task Specialist
            original_query: The original user query

        Returns:
            Synthesized final response
        """
        # Create a comprehensive response that includes both the analysis and any final insights
        final_response = f"""# Codebase Analysis Results

## Task: {original_query}

## Analysis:
{analysis_result}
"""

        # Add specialist insights if available and positive
        if is_accepted and feedback_message:
            final_response += f"""

## Specialist Review:
{feedback_message}
"""

        # Add any warnings or notes for forced acceptance
        if not is_accepted:
            final_response += """

## Note:
This analysis was completed after reaching the maximum number of review cycles. While comprehensive, there may be areas that could benefit from further investigation.
"""
            if feedback_message:
                final_response += f"""

## Areas for Further Investigation:
{feedback_message}
"""

        return final_response

    def get_agent(self, agent_name: str) -> Any:
        """
        Retrieve specific agent by name.

        Args:
            agent_name: Name of the agent ('code_analyzer' or 'task_specialist')

        Returns:
            The requested agent instance

        Raises:
            ValueError: If agent name is invalid
            RuntimeError: If agents not initialized
        """
        if not self.code_analyzer or not self.task_specialist:
            raise RuntimeError(
                "Agents not initialized. Call initialize_agents() first."
            )

        if agent_name == "code_analyzer":
            return self.code_analyzer
        elif agent_name == "task_specialist":
            return self.task_specialist
        else:
            raise ValueError(
                f"Unknown agent name: {agent_name}. Available: 'code_analyzer', 'task_specialist'"
            )
