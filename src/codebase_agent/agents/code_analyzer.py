"""
Code Analyzer Agent for AutoGen Codebase Understanding Agent.

This module implements the Code Analyzer agent responsible for technical analysis
of codebases using multi-round self-iteration and shell command execution.
"""

from typing import Dict, List, Optional, Tuple
from autogen_agentchat.agents import AssistantAgent
import logging


class CodeAnalyzer:
    """
    Technical expert agent responsible for codebase analysis using shell commands
    and iterative exploration.
    
    The Code Analyzer performs multi-round self-iteration to progressively analyze
    codebases, building knowledge through targeted shell command execution and
    self-assessment of analysis completeness.
    """
    
    def __init__(self, config: Dict, shell_tool):
        """
        Initialize the Code Analyzer agent.
        
        Args:
            config: Configuration dict containing model settings
            shell_tool: Shell execution tool for codebase exploration
        """
        self.config = config
        self.shell_tool = shell_tool
        self.logger = logging.getLogger(__name__)
        
        # Initialize AutoGen agent with shell tool capability
        self._agent = self._create_autogen_agent()
    
    def _create_autogen_agent(self) -> AssistantAgent:
        """Create and configure the AutoGen AssistantAgent with shell tool capability."""
        system_message = self._get_system_message()
        
        # Create tool list with shell command execution
        tools = [self.shell_tool.execute_command]
        
        # Create the agent with shell tool access
        agent = AssistantAgent(
            name="code_analyzer",
            system_message=system_message,
            model_client=self.config,
            tools=tools
        )
        
        return agent
    
    def _get_system_message(self) -> str:
        """Get the system message for the Code Analyzer agent."""
        return """You are a Code Analyzer, a technical expert responsible for comprehensive codebase analysis.

Your capabilities:
- Multi-round iterative analysis with self-assessment
- Shell command execution for codebase exploration via execute_shell_command tool
- Progressive knowledge building and confidence assessment
- Strategic command selection based on task context

SHELL COMMAND SAFETY GUIDANCE:
Only use READ-ONLY commands for safety:
- File exploration: ls, find, tree
- Content reading: cat, head, tail, less
- Text processing: grep, awk, sed (without -i flag)
- Information: wc, file, stat

NEVER use commands that modify files or system state.
Use pipes and command combinations as needed for analysis.

ANALYSIS PROCESS:
1. Start with broad exploration to understand project structure
2. Use targeted searches based on task keywords
3. Progressively deepen analysis based on findings
4. Build knowledge incrementally across iterations
5. Assess analysis completeness and confidence
6. Continue until confident or max iterations reached

SELF-ASSESSMENT CRITERIA:
- Confidence level (0.0 to 1.0)
- Knowledge completeness for the specific task
- Identification of integration points and existing patterns
- Understanding of project architecture and conventions

When ready to provide analysis, include:
- Comprehensive summary of relevant code structures
- Integration points and connection strategies
- Implementation recommendations based on existing patterns
- Potential conflicts or considerations
- Confidence assessment and reasoning

Use the execute_shell_command tool to explore the codebase systematically."""

    def analyze_codebase(self, query: str, codebase_path: str, specialist_feedback: Optional[str] = None) -> str:
        """
        Analyze codebase with multi-round self-iteration for progressive analysis.
        
        Args:
            query: User's analysis request
            codebase_path: Path to the codebase to analyze
            specialist_feedback: Optional feedback from Task Specialist to guide analysis focus
            
        Returns:
            Comprehensive analysis result
        """
        # Initialize iteration state
        max_iterations = 10
        current_iteration = 0
        analysis_context = []
        convergence_indicators = {
            'sufficient_code_coverage': False,
            'question_answered': False,
            'confidence_threshold_met': False
        }
        
        while current_iteration < max_iterations:
            current_iteration += 1
            
            # Prepare iteration-specific prompt
            iteration_prompt = self._build_iteration_prompt(
                query, codebase_path, current_iteration, analysis_context, convergence_indicators, specialist_feedback
            )
            
            # Execute analysis step with agent
            import asyncio
            import autogen_core
            
            def run_step():
                from autogen_agentchat.messages import UserMessage
                cancellation_token = autogen_core.CancellationToken()
                
                user_message = UserMessage(content=iteration_prompt, source="user")
                return self.agent.on_messages([user_message], cancellation_token)
            
            step_response = run_step()
            
            # Extract text from Response object if needed
            response_text = step_response
            if hasattr(step_response, 'chat_message'):
                if hasattr(step_response.chat_message, 'content'):
                    response_text = step_response.chat_message.content
                elif hasattr(step_response.chat_message, 'to_text'):
                    response_text = step_response.chat_message.to_text()
                else:
                    response_text = str(step_response.chat_message)
            elif not isinstance(step_response, str):
                response_text = str(step_response)
            
            # Store analysis step
            analysis_context.append({
                'iteration': current_iteration,
                'response': response_text,
                'timestamp': self._get_timestamp()
            })
            
            # Assess convergence
            convergence_indicators = self._assess_convergence(response_text, query, analysis_context)
            
            # Check if analysis is complete
            if self._should_terminate(convergence_indicators):
                break
                
        # Synthesize final response
        return self._synthesize_final_response(query, analysis_context, convergence_indicators)
    
    def _build_iteration_prompt(self, query: str, codebase_path: str, iteration: int, 
                               context: list, convergence: dict, specialist_feedback: Optional[str] = None) -> str:
        """Build iteration-specific prompt for progressive analysis."""
        
        base_prompt = f"""
        CODEBASE ANALYSIS - ITERATION {iteration}
        
        Target: {codebase_path}
        User Query: {query}
        
        ULTIMATE GOAL: Create a comprehensive, detailed report that thoroughly addresses the user's query.
        Your final deliverable should be a well-structured analysis that provides actionable insights and complete answers.
        
        Remember: Each exploration step should contribute towards building this detailed report.
        
        """
        
        # Add specialist feedback if provided
        if specialist_feedback:
            base_prompt += f"""
        🎯 TASK SPECIALIST FEEDBACK - PRIORITY FOCUS AREAS:
        {specialist_feedback}
        
        IMPORTANT: Address the above feedback areas as your primary focus. The Task Specialist has identified 
        these as critical gaps in the previous analysis. Make sure to specifically target these areas in your 
        exploration strategy.
        
        """
        
        # Progressive search strategy: targeted → broader → comprehensive
        if iteration == 1:
            # Stage 1: Targeted exploration
            base_prompt += """
            STAGE 1 - TARGETED EXPLORATION:
            
            MISSION: Quickly identify the most relevant code areas for answering the user's question.
            
            Start with the most specific and likely relevant areas:
            1. Extract keywords from the user query
            2. Use targeted 'find' or 'grep' commands to locate files matching these keywords
            3. Look for obvious entry points (main.py, index.js, README.md)
            4. Focus on file names, function names, or class names that directly relate to the query
            5. Prioritize files that are most likely to contain the answer
            
            Keep in mind: This is the foundation for your comprehensive report - focus on finding the right starting points.
            """
        elif iteration == 2:
            # Stage 2: Contextual expansion
            base_prompt += f"""
            STAGE 2 - CONTEXTUAL EXPANSION:
            
            MISSION: Build comprehensive context around your initial findings.
            
            Previous findings:
            {self._summarize_previous_context(context[-1:])}
            
            Expand around the areas you've already identified:
            1. Explore related files in the same directories
            2. Look for imports/dependencies of files you've found
            3. Check for configuration files, tests, or documentation related to your findings
            4. Use 'grep -r' to find broader usage patterns
            5. Examine file structure and relationships
            
            Keep in mind: You're building the structural understanding needed to thoroughly address the user's question.
            """
        elif iteration == 3:
            # Stage 3: Deeper analysis
            base_prompt += f"""
            STAGE 3 - DEEPER ANALYSIS:
            
            MISSION: Dive deep into implementation details to gather concrete evidence for your report.
            
            Previous findings:
            {self._summarize_previous_context(context[-2:])}
            
            Dive deeper into the code logic:
            1. Read actual code content of relevant files
            2. Understand implementation details and algorithms
            3. Look for edge cases, error handling, or special conditions
            4. Trace execution flows and data transformations
            5. Check for comments, docstrings, or inline documentation
            
            Keep in mind: Gather specific examples and technical details that will make your report actionable and complete.
            """
        elif iteration == 4:
            # Stage 4: Comprehensive coverage
            base_prompt += f"""
            STAGE 4 - COMPREHENSIVE COVERAGE:
            
            MISSION: Ensure no critical information is missing from your analysis.
            
            Previous findings:
            {self._summarize_previous_context(context[-3:])}
            
            Ensure complete coverage and fill gaps:
            1. Look for any missing pieces or alternative implementations
            2. Check for recent changes or version differences
            3. Explore less obvious but potentially relevant areas
            4. Verify your understanding against multiple sources
            5. Look for performance considerations, security aspects, or architectural patterns
            
            Keep in mind: This is your chance to validate and complete your findings before synthesis.
            """
        else:
            # Stage 5+: Validation and synthesis
            base_prompt += f"""
            STAGE {iteration} - VALIDATION & SYNTHESIS:
            
            MISSION: Prepare your final comprehensive report.
            
            Full analysis history:
            {self._summarize_previous_context(context)}
            
            Current convergence status:
            - Code coverage sufficient: {convergence['sufficient_code_coverage']}
            - Question answered: {convergence['question_answered']}
            - Confidence met: {convergence['confidence_threshold_met']}
            
            Focus on validation and final synthesis:
            1. Double-check any uncertain findings from previous iterations
            2. Resolve any contradictions or inconsistencies
            3. Gather final evidence for remaining uncertainties
            4. Prepare comprehensive answer synthesis
            5. Validate your conclusions against the original query
            
            Keep in mind: You're preparing the final detailed report - ensure it's comprehensive, accurate, and actionable.
            """
        
        # Add convergence-specific guidance
        if iteration > 1:
            base_prompt += "\n\nPRIORITY AREAS TO ADDRESS:\n"
            if not convergence['sufficient_code_coverage']:
                base_prompt += "- Explore additional relevant files or directories\n"
            if not convergence['question_answered']:
                base_prompt += "- Look for specific information to answer the user's question\n"
            if not convergence['confidence_threshold_met']:
                base_prompt += "- Gather more evidence to increase confidence in findings\n"
        
        base_prompt += """
        
        ITERATION OUTPUT REQUIREMENTS:
        1. What you discovered in this iteration
        2. Your confidence level (1-10) in providing a comprehensive answer
        3. Whether you need more information and what specific areas to explore next
        4. If confident enough (8+), provide your comprehensive analysis
        
        Use shell commands to explore the codebase systematically.
        Remember: Every command should contribute to building your comprehensive report.
        """
        
        return base_prompt
    
    def _assess_convergence(self, response: str, query: str, context: list) -> dict:
        """Assess whether analysis has converged based on response quality."""
        convergence = {
            'sufficient_code_coverage': False,
            'question_answered': False,
            'confidence_threshold_met': False
        }
        
        response_lower = response.lower()
        
        # Check for confidence indicators
        confidence_keywords = ['confident', 'certain', 'found', 'complete', 'comprehensive']
        if any(keyword in response_lower for keyword in confidence_keywords):
            convergence['confidence_threshold_met'] = True
            
        # Check for specific answer indicators
        answer_keywords = ['answer', 'solution', 'result', 'conclusion', 'summary']
        if any(keyword in response_lower for keyword in answer_keywords):
            convergence['question_answered'] = True
            
        # Check for code coverage indicators (file exploration, code analysis)
        coverage_keywords = ['file', 'function', 'class', 'code', 'implementation']
        coverage_count = sum(1 for keyword in coverage_keywords if keyword in response_lower)
        if coverage_count >= 3 or len(context) >= 2:
            convergence['sufficient_code_coverage'] = True
            
        return convergence
    
    def _should_terminate(self, convergence: dict) -> bool:
        """Determine if analysis should terminate based on convergence indicators."""
        # Terminate if all convergence criteria are met
        return all(convergence.values())
    
    def _summarize_previous_context(self, context: list) -> str:
        """Summarize findings from previous iterations."""
        if not context:
            return "No previous iterations."
            
        summary = ""
        for step in context:
            # Extract key findings (first 300 chars for better context)
            response_summary = step['response'][:300] + "..." if len(step['response']) > 300 else step['response']
            summary += f"\nIteration {step['iteration']}: {response_summary}"
            
        return summary
    
    def _synthesize_final_response(self, query: str, context: list, convergence: dict) -> str:
        """Synthesize final comprehensive response from all iterations."""
        if not context:
            return "No analysis performed."
            
        # Get the most recent and comprehensive response
        final_analysis = context[-1]['response']
        
        # Add synthesis header
        synthesis = f"""
        CODEBASE ANALYSIS COMPLETE
        
        Query: {query}
        Iterations: {len(context)}
        Convergence Status: {convergence}
        
        ANALYSIS RESULT:
        {final_analysis}
        """
        
        return synthesis
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    @property
    def agent(self) -> AssistantAgent:
        """Get the underlying AutoGen agent."""
        return self._agent
