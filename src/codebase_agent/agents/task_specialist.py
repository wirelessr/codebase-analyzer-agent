"""
Task Specialist Agent for AutoGen Codebase Understanding Agent.

This module implements the Task Specialist agent responsible for reviewing
analysis completeness and providing abstract feedback to guide further analysis.
"""

import json
import logging
import re

from autogen_agentchat.agents import AssistantAgent


class TaskSpecialist:
    """
    Project manager agent responsible for reviewing analysis completeness and
    determining if results meet user requirements.

    The Task Specialist provides abstract feedback without giving specific technical
    commands, focusing on WHAT information is missing rather than HOW to find it.
    """

    def __init__(self, config: dict):
        """
        Initialize the Task Specialist agent.

        Args:
            config: Configuration dict containing model settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Review tracking
        self.review_count = 0
        self.max_reviews = 3

        # Initialize AutoGen agent
        self._agent = self._create_autogen_agent()

    def _create_autogen_agent(self) -> AssistantAgent:
        """Create and configure the AutoGen AssistantAgent."""
        system_message = self._get_system_message()

        agent = AssistantAgent(
            name="task_specialist",
            system_message=system_message,
            model_client=self.config,  # Updated for new API
        )

        return agent

    def _get_system_message(self) -> str:
        """Get the system message for the Task Specialist agent."""
        return """You are a Task Specialist, acting as a project manager responsible for reviewing analysis completeness and ensuring results meet user requirements.

Your responsibilities:
- Review analysis reports for completeness against task requirements
- Provide abstract guidance on missing areas without giving specific technical commands
- Determine if analysis meets the standard for implementation guidance
- Focus on WHAT information is missing, not HOW to find it

REVIEW CRITERIA - Check if analysis includes:
✓ Identification of existing related functionality
✓ Clear integration points and connection strategies  
✓ Specific implementation steps and recommendations
✓ Potential conflicts or issues identification
✓ Concrete code examples or patterns from the codebase
✓ Understanding of project architecture and conventions
✓ Consideration of dependencies and compatibility

FEEDBACK GUIDELINES:
- Provide abstract, high-level guidance
- Focus on missing information areas, not search techniques
- Be specific about what's missing but not how to find it
- Consider the complexity of the user's task
- Evaluate if current analysis provides actionable implementation guidance

REVIEW DECISION CRITERIA:
- Accept if analysis provides sufficient information for implementation
- Reject if critical information gaps exist that would hinder implementation
- Consider task complexity when evaluating completeness
- Force accept after maximum reviews reached (3 reviews total)

FEEDBACK EXAMPLES:
Good: "Need deeper analysis of existing authentication mechanisms and their integration patterns"
Bad: "Run grep commands to find auth files"

Good: "Missing database schema impact assessment and migration considerations"  
Bad: "Check models.py and migrations folder"

Your role is strategic oversight, not technical execution."""

    def review_analysis(
        self, analysis_report: str, task_description: str, current_review_count: int
    ) -> tuple[bool, str, float]:
        """
        Review analysis report for completeness against task requirements.

        Args:
            analysis_report: The analysis report to review
            task_description: Original task description
            current_review_count: Current review iteration (1-based)

        Returns:
            Tuple of (is_complete, feedback_message, confidence_score)
        """
        self.review_count = current_review_count

        self.logger.info(
            f"Starting Task Specialist review {self.review_count}/{self.max_reviews}"
        )

        # Force accept if maximum reviews reached
        if self.review_count >= self.max_reviews:
            self.logger.info("Maximum reviews reached, force accepting analysis")
            return True, "Analysis accepted (maximum review limit reached)", 0.7

        # Primary path: Ask the LLM to perform the review with a structured prompt
        try:
            review_prompt = self._build_review_prompt(
                task_description, analysis_report, self.review_count
            )

            # Use agent.run() method directly like in the integration test
            def run_review():
                import asyncio

                async def async_review():
                    result = await self._agent.run(task=review_prompt)
                    return result

                return asyncio.run(async_review())

            llm_response = run_review()
            is_complete, feedback, confidence = self._parse_llm_review_response(
                llm_response
            )

            # If parsing succeeded, honor LLM decision
            if feedback:
                self.logger.info(
                    f"LLM review completed. Decision: {'ACCEPT' if is_complete else 'REJECT'} "
                    f"(confidence={confidence:.2f})"
                )
                return is_complete, feedback, confidence
        except Exception as e:
            # Fall back to heuristic assessment on any failure
            self.logger.warning(f"LLM-driven review error: {e}")

        # If we couldn't parse or call the LLM appropriately, return a neutral rejection
        # without applying any hardcoded judgement logic.
        return (
            False,
            "Analysis review could not be completed due to unparsable LLM response. Please retry the review step.",
            0.0,
        )

    def _build_review_prompt(
        self, task_description: str, analysis_report: str, review_number: int
    ) -> str:
        """Build a structured prompt instructing the LLM to review and respond in JSON.

        The LLM must decide completeness per the review criteria and return a JSON object:
        {"is_complete": bool, "feedback": str, "confidence": float}
        """
        criteria = (
            "- Identification of existing related functionality\n"
            "- Clear integration points and connection strategies\n"
            "- Specific implementation steps and recommendations\n"
            "- Potential conflicts or issues identification\n"
            "- Concrete code examples or patterns from the codebase\n"
            "- Understanding of project architecture and conventions\n"
            "- Consideration of dependencies and compatibility"
        )

        guidance = (
            "Provide abstract, high-level guidance. Focus on WHAT information is missing, "
            "not HOW to find it. Be specific about missing areas without prescribing technical commands."
        )

        return f"""
You are a Task Specialist, acting as a project manager responsible for reviewing analysis completeness and ensuring results meet user requirements.

REVIEW CONTEXT:
- Review number: {review_number}
- Task description: {task_description}

ANALYSIS REPORT:
<<<ANALYSIS_REPORT_START>>>
{analysis_report}
<<<ANALYSIS_REPORT_END>>>

REVIEW CRITERIA:
{criteria}

FEEDBACK GUIDELINES:
- {guidance}
- If critical information gaps exist, you must reject and list the most important missing areas (up to 5)
- If the analysis is sufficient to proceed with implementation, you must accept

OUTPUT FORMAT (MANDATORY):
Return ONLY a minified JSON object on the first line with keys: is_complete (boolean), feedback (string), confidence (float in [0,1]).
Examples:
{{"is_complete": true, "feedback": "Analysis accepted - rationale...", "confidence": 0.86}}
{{"is_complete": false, "feedback": "Analysis requires deeper coverage: - missing area 1 - missing area 2", "confidence": 0.55}}
"""

    def _parse_llm_review_response(self, raw_response) -> tuple[bool, str, float]:
        """Parse the LLM response and extract the JSON decision.

        Supports plain JSON or fenced code blocks. Falls back to empty feedback on failure.
        """
        # Handle TaskResult object from agent.run()
        response_text = raw_response
        if hasattr(raw_response, "messages") and len(raw_response.messages) > 0:
            # Get the last message from TaskResult
            last_message = raw_response.messages[-1]
            if hasattr(last_message, "content"):
                response_text = last_message.content
            else:
                response_text = str(last_message)
        elif hasattr(raw_response, "chat_message"):
            # Handle other AutoGen Response objects
            if hasattr(raw_response.chat_message, "content"):
                response_text = raw_response.chat_message.content
            elif hasattr(raw_response.chat_message, "to_text"):
                response_text = raw_response.chat_message.to_text()
            else:
                response_text = str(raw_response.chat_message)
        elif not isinstance(raw_response, str):
            response_text = str(raw_response)

        if not isinstance(response_text, str):
            response_text = str(response_text)

        # Try to extract JSON object from the response
        json_text = None

        # 1) Exact JSON on first line
        first_line = (
            response_text.strip().splitlines()[0] if response_text.strip() else ""
        )
        if first_line.startswith("{") and first_line.endswith("}"):
            json_text = first_line
        else:
            # 2) Look for fenced JSON ```json ... ``` or any {...}
            fenced = re.search(
                r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", response_text, re.IGNORECASE
            )
            if fenced:
                json_text = fenced.group(1)
            else:
                obj = re.search(r"(\{[\s\S]*\})", response_text)
                if obj:
                    json_text = obj.group(1)

        if not json_text:
            return False, "", 0.0

        try:
            data = json.loads(json_text)
            is_complete = bool(data.get("is_complete", False))
            feedback = str(data.get("feedback", "")).strip()
            confidence_raw = data.get("confidence", 0.0)
            try:
                confidence = float(confidence_raw)
            except (TypeError, ValueError):
                confidence = 0.0

            # Clamp confidence to [0,1]
            confidence = max(0.0, min(1.0, confidence))

            return is_complete, feedback, confidence
        except Exception:
            return False, "", 0.0

    @property
    def agent(self) -> AssistantAgent:
        """Get the underlying AutoGen agent."""
        return self._agent
