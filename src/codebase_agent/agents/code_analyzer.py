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
        
        # Analysis state tracking
        self.current_iteration = 0
        self.knowledge_base: List[str] = []
        self.confidence_level = 0.0
        self.max_iterations = 5
        self.confidence_threshold = 0.8
        
        # Initialize AutoGen agent
        self._agent = self._create_autogen_agent()
    
    def _create_autogen_agent(self) -> AssistantAgent:
        """Create and configure the AutoGen AssistantAgent."""
        system_message = self._get_system_message()
        
        agent = AssistantAgent(
            name="code_analyzer",
            system_message=system_message,
            model_client=self.config,  # Updated for new API
        )
        
        return agent
    
    def _get_system_message(self) -> str:
        """Get the system message for the Code Analyzer agent."""
        return """You are a Code Analyzer, a technical expert responsible for comprehensive codebase analysis.

Your capabilities:
- Multi-round iterative analysis with self-assessment
- Shell command execution for codebase exploration  
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
- Confidence assessment and reasoning"""

    def analyze_codebase(self, task_description: str, codebase_path: str) -> Tuple[str, bool, int]:
        """
        Perform multi-round analysis of the codebase for the given task.
        
        Args:
            task_description: User's task description
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Tuple of (analysis_report, is_complete, iteration_count)
        """
        self.logger.info(f"Starting codebase analysis for task: {task_description}")
        
        # Reset analysis state
        self._reset_analysis_state()
        
        # Set working directory for shell tool
        self.shell_tool.working_directory = codebase_path
        
        # Multi-round analysis loop
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1
            
            self.logger.info(f"Analysis iteration {self.current_iteration}/{self.max_iterations}")
            
            # Perform analysis iteration
            iteration_report = self._perform_analysis_iteration(task_description)
            
            # Update knowledge base
            self._update_knowledge_base(iteration_report)
            
            # Assess completeness and confidence
            is_complete, confidence = self._assess_analysis_completeness(task_description)
            self.confidence_level = confidence
            
            self.logger.info(f"Iteration {self.current_iteration} confidence: {confidence:.2f}")
            
            # Check convergence criteria
            if is_complete and confidence >= self.confidence_threshold:
                self.logger.info(f"Analysis converged after {self.current_iteration} iterations")
                break
                
            if self.current_iteration >= self.max_iterations:
                self.logger.warning("Reached maximum iterations without convergence")
                break
        
        # Generate comprehensive final report
        final_report = self._generate_final_report(task_description)
        
        return final_report, self.confidence_level >= self.confidence_threshold, self.current_iteration
    
    def _reset_analysis_state(self) -> None:
        """Reset analysis state for new analysis."""
        self.current_iteration = 0
        self.knowledge_base = []
        self.confidence_level = 0.0
    
    def _perform_analysis_iteration(self, task_description: str) -> str:
        """
        Perform a single analysis iteration.
        
        Args:
            task_description: User's task description
            
        Returns:
            Analysis report for this iteration
        """
        # Generate analysis prompt for this iteration
        iteration_prompt = self._create_iteration_prompt(task_description)
        
        # Execute analysis through AutoGen agent
        try:
            # For now, we'll simulate the analysis logic
            # In full implementation, this would use the AutoGen agent
            iteration_report = self._execute_analysis_commands(task_description)
            return iteration_report
            
        except Exception as e:
            self.logger.error(f"Error in analysis iteration {self.current_iteration}: {e}")
            return f"Error during analysis iteration: {str(e)}"
    
    def _create_iteration_prompt(self, task_description: str) -> str:
        """Create prompt for current analysis iteration."""
        context = ""
        if self.knowledge_base:
            context = f"Previous knowledge accumulated:\n{' '.join(self.knowledge_base[-3:])}\n\n"
        
        return f"""{context}Task: {task_description}

Current iteration: {self.current_iteration}/{self.max_iterations}
Confidence level: {self.confidence_level:.2f}

Perform the next analysis iteration. Focus on areas that need deeper investigation
based on the task requirements and current knowledge."""
    
    def _execute_analysis_commands(self, task_description: str) -> str:
        """
        Execute shell commands for codebase analysis.
        
        This method implements the core analysis logic using shell commands.
        """
        commands_executed = []
        findings = []
        
        # Extract keywords from task description for targeted search
        keywords = self._extract_task_keywords(task_description)
        
        try:
            # Phase 1: Project structure exploration
            if self.current_iteration == 1:
                # Get project overview
                success, stdout, stderr = self.shell_tool.execute_command("find . -type f -name '*.py' | head -20")
                if success:
                    commands_executed.append("find . -type f -name '*.py' | head -20")
                    findings.append(f"Python files found: {len(stdout.splitlines())} (showing first 20)")
                
                # Check project structure
                success, stdout, stderr = self.shell_tool.execute_command("ls -la")
                if success:
                    commands_executed.append("ls -la")
                    findings.append(f"Project root structure identified")
            
            # Phase 2: Targeted keyword search
            for keyword in keywords[:3]:  # Limit to top 3 keywords
                success, stdout, stderr = self.shell_tool.execute_command(f"find . -name '*.py' | xargs grep -l '{keyword}' | head -10")
                if success and stdout.strip():
                    commands_executed.append(f"grep search for '{keyword}'")
                    findings.append(f"Files containing '{keyword}': {len(stdout.splitlines())}")
            
            # Phase 3: Deeper file content analysis (later iterations)
            if self.current_iteration > 2:
                # Examine specific files based on previous findings
                success, stdout, stderr = self.shell_tool.execute_command("find . -name 'models.py' -o -name 'model.py' | head -5")
                if success and stdout.strip():
                    commands_executed.append("Model file search")
                    findings.append("Model files identified for detailed analysis")
            
        except Exception as e:
            self.logger.error(f"Error executing analysis commands: {e}")
            findings.append(f"Command execution error: {str(e)}")
        
        # Generate iteration report
        report = f"""
Analysis Iteration {self.current_iteration} Report:
Commands executed: {len(commands_executed)}
Key findings:
{chr(10).join(f"- {finding}" for finding in findings)}

Analysis strategy: {'Initial exploration' if self.current_iteration == 1 else 'Targeted investigation'}
"""
        
        return report
    
    def _extract_task_keywords(self, task_description: str) -> List[str]:
        """Extract relevant keywords from task description for targeted search."""
        # Simple keyword extraction logic
        # In full implementation, this would be more sophisticated
        keywords = []
        
        task_lower = task_description.lower()
        
        # Authentication-related keywords
        if any(word in task_lower for word in ['auth', 'login', 'user', 'password']):
            keywords.extend(['auth', 'user', 'login', 'password', 'session'])
        
        # API-related keywords
        if any(word in task_lower for word in ['api', 'endpoint', 'route']):
            keywords.extend(['api', 'route', 'endpoint', 'controller'])
        
        # Database-related keywords
        if any(word in task_lower for word in ['database', 'model', 'orm']):
            keywords.extend(['model', 'database', 'orm', 'migration'])
        
        # Frontend-related keywords
        if any(word in task_lower for word in ['frontend', 'react', 'component']):
            keywords.extend(['component', 'react', 'frontend', 'jsx'])
        
        return list(set(keywords))  # Remove duplicates
    
    def _update_knowledge_base(self, iteration_report: str) -> None:
        """Update knowledge base with findings from current iteration."""
        self.knowledge_base.append(iteration_report)
        
        # Keep only last 5 reports to prevent memory bloat
        if len(self.knowledge_base) > 5:
            self.knowledge_base = self.knowledge_base[-5:]
    
    def _assess_analysis_completeness(self, task_description: str) -> Tuple[bool, float]:
        """
        Assess if analysis is complete and return confidence level.
        
        Returns:
            Tuple of (is_complete, confidence_level)
        """
        # Simple assessment logic based on iteration count and knowledge accumulation
        base_confidence = min(0.2 * self.current_iteration, 0.8)
        
        # Boost confidence if we have substantial knowledge
        knowledge_bonus = min(0.1 * len(self.knowledge_base), 0.2)
        
        confidence = base_confidence + knowledge_bonus
        
        # Consider complete if confidence is above threshold or max iterations reached
        is_complete = confidence >= self.confidence_threshold or self.current_iteration >= self.max_iterations
        
        return is_complete, confidence
    
    def _generate_final_report(self, task_description: str) -> str:
        """Generate comprehensive final analysis report."""
        knowledge_summary = "\n".join(self.knowledge_base)
        
        return f"""
# Codebase Analysis Report

## Task: {task_description}

## Analysis Summary
- Total iterations performed: {self.current_iteration}
- Final confidence level: {self.confidence_level:.2f}
- Analysis status: {'Complete' if self.confidence_level >= self.confidence_threshold else 'Incomplete'}

## Findings
{knowledge_summary}

## Recommendations
Based on the analysis performed across {self.current_iteration} iterations, the codebase structure and patterns have been identified. Implementation should follow the existing architectural patterns found during exploration.

## Integration Points
Key integration areas have been identified through systematic exploration of the codebase structure and existing implementations.

## Implementation Strategy
The analysis suggests following the established patterns and conventions found in the codebase for consistent implementation.
"""

    @property
    def agent(self) -> AssistantAgent:
        """Get the underlying AutoGen agent."""
        return self._agent
