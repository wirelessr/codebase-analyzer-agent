"""
Task Specialist Agent for AutoGen Codebase Understanding Agent.

This module implements the Task Specialist agent responsible for reviewing
analysis completeness and providing abstract feedback to guide further analysis.
"""

from typing import Dict, List, Optional, Tuple
from autogen_agentchat.agents import AssistantAgent
import logging


class TaskSpecialist:
    """
    Project manager agent responsible for reviewing analysis completeness and
    determining if results meet user requirements.
    
    The Task Specialist provides abstract feedback without giving specific technical
    commands, focusing on WHAT information is missing rather than HOW to find it.
    """
    
    def __init__(self, config: Dict):
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

    def review_analysis(self, analysis_report: str, task_description: str, current_review_count: int) -> Tuple[bool, str, float]:
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
        
        self.logger.info(f"Starting Task Specialist review {self.review_count}/{self.max_reviews}")
        
        # Force accept if maximum reviews reached
        if self.review_count >= self.max_reviews:
            self.logger.info("Maximum reviews reached, force accepting analysis")
            return True, "Analysis accepted (maximum review limit reached)", 0.7
        
        # Perform completeness assessment
        completeness_score, missing_areas = self._assess_completeness(analysis_report, task_description)
        
        # Determine if analysis is complete
        is_complete = completeness_score >= 0.8
        
        if is_complete:
            feedback = self._generate_acceptance_feedback(completeness_score)
            self.logger.info(f"Analysis accepted with completeness score: {completeness_score:.2f}")
        else:
            feedback = self._generate_rejection_feedback(missing_areas, task_description)
            self.logger.info(f"Analysis rejected, completeness score: {completeness_score:.2f}")
        
        return is_complete, feedback, completeness_score
    
    def _assess_completeness(self, analysis_report: str, task_description: str) -> Tuple[float, List[str]]:
        """
        Assess the completeness of the analysis report.
        
        Returns:
            Tuple of (completeness_score, missing_areas)
        """
        missing_areas = []
        criteria_met = 0
        total_criteria = 7
        
        report_lower = analysis_report.lower()
        task_lower = task_description.lower()
        
        # Check each completeness criterion
        
        # 1. Existing functionality identification
        if any(keyword in report_lower for keyword in ['existing', 'current', 'found', 'identified']):
            criteria_met += 1
        else:
            missing_areas.append("existing related functionality identification")
        
        # 2. Integration points
        if any(keyword in report_lower for keyword in ['integration', 'connect', 'interface', 'endpoint']):
            criteria_met += 1
        else:
            missing_areas.append("clear integration points and connection strategies")
        
        # 3. Implementation steps
        if any(keyword in report_lower for keyword in ['recommend', 'implement', 'step', 'approach']):
            criteria_met += 1
        else:
            missing_areas.append("specific implementation steps and recommendations")
        
        # 4. Conflict identification
        if any(keyword in report_lower for keyword in ['conflict', 'issue', 'problem', 'consideration']):
            criteria_met += 1
        else:
            missing_areas.append("potential conflicts or issues identification")
        
        # 5. Code examples/patterns
        if any(keyword in report_lower for keyword in ['pattern', 'example', 'code', 'structure']):
            criteria_met += 1
        else:
            missing_areas.append("concrete code examples or patterns from the codebase")
        
        # 6. Architecture understanding
        if any(keyword in report_lower for keyword in ['architecture', 'structure', 'organization', 'framework']):
            criteria_met += 1
        else:
            missing_areas.append("understanding of project architecture and conventions")
        
        # 7. Dependencies consideration
        if any(keyword in report_lower for keyword in ['depend', 'library', 'package', 'requirement']):
            criteria_met += 1
        else:
            missing_areas.append("consideration of dependencies and compatibility")
        
        # Calculate completeness score
        completeness_score = criteria_met / total_criteria
        
        # Task-specific adjustments
        if 'auth' in task_lower and 'security' not in report_lower:
            missing_areas.append("security considerations for authentication implementation")
            completeness_score *= 0.9
        
        if 'api' in task_lower and 'endpoint' not in report_lower:
            missing_areas.append("API endpoint design and routing considerations")
            completeness_score *= 0.95
        
        return completeness_score, missing_areas
    
    def _generate_acceptance_feedback(self, completeness_score: float) -> str:
        """Generate feedback message for accepted analysis."""
        return f"""Analysis review complete - ACCEPTED

The analysis demonstrates sufficient completeness for implementation guidance with a score of {completeness_score:.2f}.

The report provides adequate coverage of:
- Existing functionality identification
- Integration strategies
- Implementation recommendations
- Architectural considerations

The analysis meets the standards for proceeding with implementation planning."""
    
    def _generate_rejection_feedback(self, missing_areas: List[str], task_description: str) -> str:
        """Generate feedback message for rejected analysis with guidance."""
        feedback_parts = [
            "Analysis review complete - REQUIRES DEEPER ANALYSIS",
            "",
            "The current analysis is incomplete for providing actionable implementation guidance.",
            "",
            "Missing areas that need attention:"
        ]
        
        for area in missing_areas[:5]:  # Limit to top 5 missing areas
            feedback_parts.append(f"- {area}")
        
        # Add task-specific guidance
        task_guidance = self._get_task_specific_guidance(task_description)
        if task_guidance:
            feedback_parts.extend(["", "Task-specific guidance:", task_guidance])
        
        feedback_parts.extend([
            "",
            "Focus on gathering information about these areas to provide comprehensive implementation guidance.",
            f"Review {self.review_count}/{self.max_reviews} - Continue analysis to address these gaps."
        ])
        
        return "\n".join(feedback_parts)
    
    def _get_task_specific_guidance(self, task_description: str) -> str:
        """Generate task-specific guidance based on the task description."""
        task_lower = task_description.lower()
        guidance_parts = []
        
        if 'auth' in task_lower or 'login' in task_lower:
            guidance_parts.append("- Examine existing user management and session handling mechanisms")
            guidance_parts.append("- Identify current security measures and authentication flows")
            guidance_parts.append("- Assess database schema for user-related tables and relationships")
        
        if 'api' in task_lower:
            guidance_parts.append("- Analyze existing API structure and routing patterns")
            guidance_parts.append("- Identify middleware and request/response handling conventions")
            guidance_parts.append("- Examine error handling and validation approaches")
        
        if 'database' in task_lower or 'model' in task_lower:
            guidance_parts.append("- Investigate data model relationships and constraints")
            guidance_parts.append("- Examine migration patterns and database evolution strategy")
            guidance_parts.append("- Assess ORM usage and database interaction patterns")
        
        if 'frontend' in task_lower or 'ui' in task_lower:
            guidance_parts.append("- Analyze component structure and state management patterns")
            guidance_parts.append("- Examine routing and navigation implementation")
            guidance_parts.append("- Identify styling and theming approaches")
        
        return "\n".join(guidance_parts) if guidance_parts else ""
    
    def reset_review_count(self) -> None:
        """Reset review count for new analysis cycle."""
        self.review_count = 0
    
    @property
    def agent(self) -> AssistantAgent:
        """Get the underlying AutoGen agent."""
        return self._agent
    
    @property
    def has_reviews_remaining(self) -> bool:
        """Check if there are reviews remaining."""
        return self.review_count < self.max_reviews
