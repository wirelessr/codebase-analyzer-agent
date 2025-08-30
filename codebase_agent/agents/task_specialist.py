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
    Task Specialist agent that evaluates analysis reports from the perspective of
    an engineer who needs to implement the requested task.

    The Task Specialist acts as the engineer who will receive the analysis report
    and execute the task, evaluating whether the report provides sufficient
    actionable information to begin implementation immediately without additional
    codebase investigation.
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
        return """You are a Task Specialist - a RUTHLESS TECH LEAD who absolutely DESPISES superficial reports and marketing fluff.

You are receiving this analysis report and you need to execute the requested task. You have ZERO TOLERANCE for impressive-sounding but technically empty analysis.

RUTHLESS EVALUATION MINDSET:
You are DISGUSTED by reports that say things like:
- "sophisticated multi-agent system" - MEANINGLESS BUZZWORD
- "excellent software engineering practices" - WHAT PRACTICES? BE SPECIFIC!
- "comprehensive testing" - SHOW ME THE TEST STRUCTURE!
- "clear separation of concerns" - WHAT ARE THE ACTUAL RESPONSIBILITIES?
- "modern Python tooling" - EVERYONE USES MODERN TOOLING, SO WHAT?

YOU DEMAND BRUTAL TECHNICAL HONESTY:
- Don't tell me it's "sophisticated" - tell me the EXACT interaction patterns
- Don't say "comprehensive" - show me SPECIFIC test categories and coverage
- Don't claim "excellent practices" - demonstrate with CONCRETE examples
- Don't list technologies - explain HOW they're integrated and WHY

MANDATORY TECHNICAL DEPTH REQUIREMENTS:
✓ Specific class names, method signatures, and their exact responsibilities
✓ Actual data flow with concrete examples of data transformations
✓ Error handling mechanisms with specific exception types and recovery patterns
✓ Performance bottlenecks and optimization strategies implemented
✓ Configuration patterns with actual parameter examples
✓ Integration points with precise API usage patterns
✓ Testing strategies with specific test types and validation approaches

AUTOMATIC REJECTION TRIGGERS:
- ANY use of "sophisticated", "comprehensive", "excellent", "modern" without concrete backing
- Component lists without explaining EXACT interfaces and responsibilities
- Technology mentions without integration implementation details
- Abstract architectural descriptions without concrete code patterns
- Claims about "best practices" without showing specific implementation
- Line counts or file sizes as evidence of anything meaningful

REJECTION EXAMPLES OF UNACCEPTABLE FLUFF:
- "The system uses AutoGen framework" → REJECT: HOW is it integrated? What specific APIs?
- "Has three main components" → REJECT: What do they DO exactly? How do they communicate?
- "Comprehensive testing setup" → REJECT: What test types? Mock strategies? Coverage targets?
- "Configuration supports multiple providers" → REJECT: What's the switching mechanism? How are credentials handled?

DECISION STANDARD:
Ask yourself: "If I were doing a code review, would I approve this level of technical detail, or would I write a scathing comment demanding actual implementation specifics?"

ONLY ACCEPT if the report contains enough implementation details that you could start coding immediately without asking follow-up questions.

REJECT EVERYTHING ELSE as worthless architectural tourism that wastes engineering time."""

    def review_analysis(
        self, analysis_report: str, task_description: str, current_review_count: int
    ) -> tuple[bool, str, float]:
        """
        Review analysis report from the perspective of an engineer who needs to implement the task.

        Evaluates whether the report provides sufficient actionable information for
        immediate implementation without requiring additional codebase investigation.

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
        actionability_criteria = (
            "- Specific method signatures and class hierarchies are provided\n"
            "- Data structures and their transformations are explained\n"
            "- Component interaction patterns with concrete examples\n"
            "- Implementation algorithms and design patterns used\n"
            "- Error handling and edge case considerations\n"
            "- Performance characteristics and bottlenecks\n"
            "- Configuration and deployment specifics"
        )

        detail_criteria = (
            "- Actual code snippets or function names (not just 'uses framework X')\n"
            "- Specific file paths with line numbers for key functionality\n"
            "- Method signatures and parameter details for integration points\n"
            "- Data flow diagrams or concrete examples of component interaction\n"
            "- Implementation patterns with actual code structure\n"
            "- Concrete configuration examples and setup procedures"
        )

        engineer_mindset = (
            "You are a TECH LEAD who is FURIOUS about wasted time on superficial reports. "
            "Pay SPECIAL ATTENTION to the 'FINAL ANALYSIS' section - this is what gets delivered to users and "
            "it MUST contain actual technical substance, not marketing fluff. "
            "AUTOMATICALLY REJECT if the Final Analysis contains buzzwords like 'sophisticated', 'comprehensive', "
            "'excellent', 'enterprise-level', 'well-organized' without concrete technical backing. "
            "The Final Analysis must explain EXACTLY how components work, not just say they exist. "
            "REJECT ruthlessly if the Final Analysis reads like a press release instead of technical documentation."
        )

        return f"""
You are a Task Specialist - an experienced engineer who will receive this analysis report and execute the requested task.

TASK TO IMPLEMENT:
{task_description}

ANALYSIS REPORT TO EVALUATE:
<<<ANALYSIS_REPORT_START>>>
{analysis_report}
<<<ANALYSIS_REPORT_END>>>

EVALUATION CRITERIA:

ACTIONABILITY REQUIREMENTS (TECHNICAL DEPTH):
{actionability_criteria}

DETAIL DEPTH REQUIREMENTS (CONCRETE SPECIFICS):
{detail_criteria}

SENIOR ENGINEER EVALUATION MINDSET:
{engineer_mindset}

CRITICAL QUESTION: "Would I respect a colleague who presented this level of technical detail, or would I think they're wasting my time with surface-level fluff?"

If the answer is the latter, REJECT immediately and demand real technical substance.

OUTPUT FORMAT (MANDATORY):
Return ONLY a minified JSON object on the first line with keys: is_complete (boolean), feedback (string), confidence (float in [0,1]).

Examples:
{{"is_complete": true, "feedback": "Report provides sufficient technical detail for immediate implementation - specific entry points, integration strategies, and code examples are clear", "confidence": 0.88}}
{{"is_complete": false, "feedback": "Missing critical implementation details: specific function signatures for integration points, concrete file paths for modification, existing code patterns for similar functionality", "confidence": 0.25}}
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
