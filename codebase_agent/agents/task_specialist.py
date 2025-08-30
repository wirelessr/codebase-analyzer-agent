"""
Task Specialist Agent for AutoGen Codebase Understanding Agent.

This module implements the Task Specialist agent responsible for reviewing
analysis completeness and providing abstract feedback to guide further analysis.
"""

import json
import logging
import re

from autogen_agentchat.agents import AssistantAgent

from ..utils.autogen_utils import extract_text_from_autogen_response


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

CONFIDENCE SCORING (CRITICAL):
- 0.9-1.0: Ready for immediate implementation with complete technical details
- 0.8-0.89: Good technical depth but missing some implementation specifics
- 0.7-0.79: Adequate overview but needs significant additional investigation
- 0.6-0.69: Insufficient technical detail for confident implementation
- Below 0.6: Completely inadequate, needs major rework

REJECTION EXAMPLES OF UNACCEPTABLE FLUFF:
- "The system uses AutoGen framework" → REJECT: HOW is it integrated? What specific APIs?
- "Has three main components" → REJECT: What do they DO exactly? How do they communicate?
- "Comprehensive testing setup" → REJECT: What test types? Mock strategies? Coverage targets?
- "Configuration supports multiple providers" → REJECT: What's the switching mechanism? How are credentials handled?

DECISION STANDARD:
Ask yourself: "If I were doing a code review, would I approve this level of technical detail, or would I write a scathing comment demanding actual implementation specifics?"

ONLY ACCEPT WITH HIGH CONFIDENCE (0.8+) if the report contains enough implementation details that you could start coding immediately without asking follow-up questions.

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

        # Force accept if maximum reviews reached with stricter confidence penalty
        if self.review_count >= self.max_reviews:
            self.logger.warning(
                "Maximum reviews reached - forcing acceptance with low confidence"
            )
            return (
                True,
                "Analysis accepted (maximum review limit reached - quality may be insufficient)",
                0.5,
            )  # Lower confidence score for forced acceptance

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

            # If parsing succeeded, honor LLM decision but apply minimum confidence threshold
            if feedback:
                # Apply stricter confidence threshold for acceptance
                min_confidence_for_acceptance = 0.80

                # First review should be extra strict - always ask for improvements
                if self.review_count == 1:
                    min_confidence_for_acceptance = 0.90
                    self.logger.info(
                        "First review - applying extra strict confidence threshold (0.90)"
                    )

                if is_complete and confidence < min_confidence_for_acceptance:
                    self.logger.warning(
                        f"LLM accepted but confidence {confidence:.2f} below threshold {min_confidence_for_acceptance}"
                    )
                    is_complete = False
                    feedback = f"Analysis needs improvement. {feedback} (Confidence {confidence:.2f} below required {min_confidence_for_acceptance})"

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
        # Extract only the FINAL ANALYSIS section for evaluation
        final_analysis = self._extract_final_analysis(analysis_report)

        return f"""
You are a CODE REVIEW SPECIALIST evaluating analysis reports. Think like a tech lead who has to implement this task.

TASK: {task_description}

ANALYSIS TO EVALUATE:
{final_analysis}

CORE QUESTION: "Can I start implementing this task immediately, or do I need to investigate the codebase further?"

QUALITY REQUIREMENTS:
1. SYSTEM UNDERSTANDING: Explains HOW components work together, not just what they are
2. ENTRY POINTS: Shows WHERE to start investigating or modifying code
3. DATA FLOW: Describes how information flows through the system
4. TASK RELEVANCE: Connects analysis directly to the requested task

REJECT IMMEDIATELY IF:
- Lists components without explaining interactions
- Shows code examples instead of architectural understanding
- Provides generic advice not specific to this codebase
- Missing explanation of how the system actually operates
- No clear guidance on where to focus for this specific task

CONFIDENCE SCORING:
- 0.9+: Ready to implement - clear system understanding and task guidance
- 0.8-0.89: Good foundation but missing some implementation details
- 0.7-0.79: Basic overview but needs significant additional investigation
- Below 0.7: Inadequate - requires major additional analysis

FEEDBACK RULES:
- For REJECTIONS: Provide specific shell commands to fill gaps
- For ACCEPTANCE: Briefly confirm what makes it ready for implementation

RESPONSE FORMAT:
JSON only: {{"is_complete": boolean, "feedback": "specific actionable guidance", "confidence": float}}

REJECTION EXAMPLES:
{{"is_complete": false, "feedback": "Missing data flow. Run: grep -r 'def process\\|def handle' . to find entry points, then trace how requests flow through the system", "confidence": 0.35}}

{{"is_complete": false, "feedback": "Component interactions unclear. Execute: find . -name '*manager*.py' -exec grep -l 'def __init__' {{}} \\; then examine dependency injection patterns", "confidence": 0.40}}

ACCEPTANCE EXAMPLE:
{{"is_complete": true, "feedback": "Clear system operation explanation with task-specific entry points identified", "confidence": 0.87}}
"""

    def _extract_final_analysis(self, analysis_report: str) -> str:
        """Extract only the FINAL ANALYSIS section from the complete report."""
        import re

        # Look for FINAL ANALYSIS section
        final_analysis_pattern = r"FINAL ANALYSIS:\s*(.*?)(?=\n\s*EXECUTION SUMMARY:|$)"
        match = re.search(
            final_analysis_pattern, analysis_report, re.DOTALL | re.IGNORECASE
        )

        if match:
            final_analysis = match.group(1).strip()
            if final_analysis:
                return final_analysis

        # Fallback: if we can't find the section, return a note about missing analysis
        return "No FINAL ANALYSIS section found in the report."

    def _parse_llm_review_response(self, raw_response) -> tuple[bool, str, float]:
        """Parse the LLM response and extract the JSON decision.

        Supports plain JSON or fenced code blocks. Falls back to empty feedback on failure.
        """
        # Handle TaskResult object from agent.run()
        response_text = extract_text_from_autogen_response(raw_response)

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
