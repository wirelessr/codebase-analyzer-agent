"""
Code Analyzer Agent for AutoGen Codebase Understanding Agent.

ThCRITICACRITICAL: COLLABORATIVE KNOWLEDGE BASE APPROACH
You will maintain a "key_findings" list that serves as a collaborative knowledge base:
1. REVIEW the existing key_findings from previous iterations
2. ADD your new important discoveries to the list
3. UPDATE or REFINE existing findings if you have new insights
4. REMOVE findings that are no longer relevant or were incorrectLABORATIVE KNOWLEDGE BASE APPROACH
You will maintain a "key_findings" list that serves as a collaborative knowledge base:
1. 📝 REVIEW the existing key_findings from previous iterations
2. 🔍 ADD your new important discoveries to the list
3. 🔄 UPDATE or REFINE existing findings if you have new insights
4. 🗑️ REMOVE findings that are no longer relevant or were incorrect

This shared knowledge base ensures all critical information is preserved across iterations.e implements the Code Analyzer agent responsible for technical analysis
of codebases using multi-round self-iteration and shell command execution.
"""

import logging

from autogen_agentchat.agents import AssistantAgent


class CodeAnalyzer:
    """
    Technical expert agent responsible for codebase analysis using shell commands
    and iterative exploration.

    The Code Analyzer performs multi-round self-iteration to progressively analyze
    codebases, building knowledge through targeted shell command execution and
    self-assessment of analysis completeness.
    """

    def __init__(self, config: dict, shell_tool):
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
        """Create and configure the AutoGen AssistantAgent without shell tool capability."""
        system_message = self._get_system_message()

        # Create the agent without tools (LLM will provide commands via JSON response)
        agent = AssistantAgent(
            name="code_analyzer",
            system_message=system_message,
            model_client=self.config,
        )

        return agent

    def _get_system_message(self) -> str:
        """Get the system message for the Code Analyzer agent."""
        return r"""You are a Code Analyzer, a technical expert responsible for comprehensive codebase analysis.

CRITICAL: You MUST always start by exploring the codebase with shell commands before providing any analysis.

Your capabilities:
- Multi-round iterative analysis with self-assessment
- Requesting shell command execution for codebase exploration
- Progressive knowledge building and confidence assessment
- Strategic command selection based on task context

🔍 DISCOVERY-DRIVEN ANALYSIS PHILOSOPHY:
Be a detective, not a robot. Let curiosity and discovery drive your analysis rather than following rigid checklists.
Trust your pattern recognition abilities and adapt your exploration strategy based on what the codebase reveals to you.

**Core Principles**:
- **Curiosity over Checklists**: Explore what's interesting rather than what's expected
- **Content-Driven Discovery**: Let what you find guide what you look for next
- **Adaptive Exploration**: Change strategy based on what the codebase reveals
- **Universal Understanding**: Focus on concepts rather than language-specific patterns

🚀 SMART ANALYSIS STRATEGY:

1. **Discovery Phase**: Start broad, then adapt based on what you find
   - Project landscape: `ls -la`, `find . -type f | head -20`
   - File type analysis: `file $(find . -type f | head -10)`
   - Content diversity: `wc -l $(find . -type f | head -10)`

2. **Adaptive Pattern Recognition**: Let the content guide your search patterns
   - Universal concepts: functions, classes, imports, configuration, logic flow
   - Creative grep usage: search for keywords that appear in the actual code
   - Pattern discovery: `grep`, `awk`, `sed` to extract interesting patterns you discover

3. **Progressive Understanding**: Build knowledge incrementally
   - Sample content: `head -20 filename && tail -20 filename`
   - Strategic reading: adapt based on file size and discovered patterns
   - Context building: connect findings across files

4. **Intelligent Tool Usage**: Be creative with standard tools
   - Text tools: `cat`, `head`, `tail`, `grep`, `awk`, `sed`
   - Analysis tools: `wc`, `file`, `stat`, `sort | uniq -c`
   - Search patterns: adapt based on content, not predefined rules

🛠️ SHELL COMMAND GUIDANCE:
Only request READ-ONLY commands for safety:
- File exploration: `ls`, `find`, `tree`
- Content reading: `cat`, `head`, `tail`, `less`
- Text processing: `grep`, `awk`, `sed` (without -i flag)
- Information: `wc`, `file`, `stat`
- Advanced search: `grep` with `-r`, `-n`, `-A`, `-B` options

📁 BINARY FILE HANDLING:
When encountering binary files (executables, images, compiled code, etc.):
- **First step**: Always use `file filename` to identify file type
- **For text extraction**: Use `strings filename | head -20` to extract readable text from binaries
- **Size analysis**: Use `ls -lh filename` to check file size
- **Focus on metadata**: Use `file`, `stat`, and `ls` for file information

⚠️ AVOID THESE TOOLS:
- **DO NOT use**: `xxd`, `od`, `hexdump` for binary inspection
- **DO NOT use**: `cat` on binary files (it can break terminals)
- **Reason**: These tools are rarely needed for codebase analysis and can produce excessive output
- **Alternative**: Focus on text content, file types, and using `strings` for binaries when needed

📋 FILE READING BEST PRACTICES:
1. **Always start with**: `file filename` and `wc -l filename`
2. **For small files** (<100 lines): Read entirely with `cat`
3. **For medium files** (100-500 lines): Sample sections, then read strategically
4. **For large files** (>500 lines): Use targeted reading based on discovered patterns
5. **Let content guide approach**: If you see SQL, search for database patterns; if config, look for settings

🧠 COLLABORATIVE KNOWLEDGE BASE:
Maintain a "key_findings" list that serves as shared memory across iterations:
1. 📝 REVIEW existing key_findings from previous iterations
2. 🔍 ADD your new important discoveries
3. 🔄 UPDATE or REFINE existing findings with new insights
4. 🗑️ REMOVE findings that are no longer relevant

📤 RESPONSE FORMAT:
You MUST respond in valid JSON format with these exact fields:
{
    "need_shell_execution": true/false,
    "shell_commands": ["command1", "command2", ...],
    "key_findings": ["Finding 1", "Finding 2", "..."],
    "current_analysis": "Your analysis of this iteration",
    "confidence_level": 1-10,
    "next_focus_areas": "What you plan to focus on next"
}

🎯 ANALYSIS PROCESS:
1. **First iteration**: ALWAYS set need_shell_execution: true with discovery commands
2. **Progressive exploration**: Let findings guide next steps
3. **Content reading**: Don't just list files - read and understand content
4. **Pattern adaptation**: Adapt search patterns based on what you discover
5. **Knowledge building**: Build understanding incrementally across iterations
6. **Convergence**: Continue until confident or max iterations reached

💡 FIRST ITERATION STARTER COMMANDS:
- `["ls -la", "find . -type f | head -20", "file $(find . -type f | head -5)"]`

🎯 YOUR GOAL: UNDERSTANDING through discovery, not checklist completion.
Adapt your reading strategy based on:
- File size and complexity
- The specific question being asked
- The type of content (code, config, docs, etc.)
- What the codebase reveals to you

Always explain your findings with specific examples, line numbers, and evidence from the code."""

    def analyze_codebase(
        self, query: str, codebase_path: str, specialist_feedback: str | None = None
    ) -> str:
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
        shell_execution_history = []
        shared_key_findings = []  # Collaborative knowledge base
        convergence_indicators = {
            "sufficient_code_coverage": False,
            "question_answered": False,
            "confidence_threshold_met": False,
        }

        while current_iteration < max_iterations:
            current_iteration += 1

            # Prepare iteration-specific prompt
            iteration_prompt = self._build_iteration_prompt(
                query,
                codebase_path,
                current_iteration,
                analysis_context,
                shell_execution_history,
                shared_key_findings,
                convergence_indicators,
                specialist_feedback,
            )

            # Execute analysis step with agent (LLM decision phase)
            def run_step(prompt):
                import asyncio

                async def async_step():
                    result = await self.agent.run(task=prompt)
                    return result

                return asyncio.run(async_step())

            step_response = run_step(iteration_prompt)

            # Extract text from TaskResult object
            response_text = self._extract_response_text(step_response)

            # Parse JSON response from LLM
            try:
                import json

                self.logger.debug(f"Raw LLM response: {response_text[:500]}...")

                # Extract JSON from markdown code blocks if present
                json_text = self._extract_json_from_response(response_text)

                llm_decision = json.loads(json_text)
                self.logger.debug(f"Parsed LLM decision: {llm_decision}")

                # Update shared key findings from LLM response
                if "key_findings" in llm_decision:
                    shared_key_findings = llm_decision["key_findings"]

            except json.JSONDecodeError as e:
                # Fallback: treat as plain text analysis without shell commands
                self.logger.warning(f"JSON parsing failed: {e}")
                self.logger.warning(f"Raw response was: {response_text[:200]}...")
                llm_decision = {
                    "need_shell_execution": False,
                    "shell_commands": [],
                    "key_findings": shared_key_findings,  # Preserve existing findings
                    "current_analysis": response_text,
                    "confidence_level": 5,
                    "next_focus_areas": "Continue analysis",
                }

            # Execute shell commands if needed (execution phase)
            shell_results = []
            if llm_decision.get("need_shell_execution", False):
                shell_commands = llm_decision.get("shell_commands", [])
                shell_results = self._execute_shell_commands(shell_commands)
                shell_execution_history.append(
                    {
                        "iteration": current_iteration,
                        "commands": shell_commands,
                        "results": shell_results,
                        "timestamp": self._get_timestamp(),
                    }
                )

            # Store analysis step
            analysis_context.append(
                {
                    "iteration": current_iteration,
                    "llm_decision": llm_decision,
                    "shell_results": shell_results,
                    "timestamp": self._get_timestamp(),
                }
            )

            # Assess convergence based on LLM's confidence and analysis
            convergence_indicators = self._assess_convergence_from_json(
                llm_decision, analysis_context
            )

            # Check if analysis is complete
            if self._should_terminate(convergence_indicators) or not llm_decision.get(
                "need_shell_execution", True
            ):
                break

        # Synthesize final response
        return self._synthesize_final_response(
            query, analysis_context, shared_key_findings, convergence_indicators
        )

    def _extract_response_text(self, step_response) -> str:
        """Extract text from AutoGen response object."""
        response_text = step_response
        if hasattr(step_response, "messages") and len(step_response.messages) > 0:
            # Get the last message from TaskResult
            last_message = step_response.messages[-1]
            if hasattr(last_message, "content"):
                response_text = last_message.content
            else:
                response_text = str(last_message)
        elif hasattr(step_response, "chat_message"):
            # Handle other AutoGen Response objects (fallback)
            if hasattr(step_response.chat_message, "content"):
                response_text = step_response.chat_message.content
            elif hasattr(step_response.chat_message, "to_text"):
                response_text = step_response.chat_message.to_text()
            else:
                response_text = str(step_response.chat_message)
        elif not isinstance(step_response, str):
            response_text = str(step_response)
        return response_text

    def _execute_shell_commands(self, commands: list[str]) -> list[dict]:
        """Execute a list of shell commands and return results."""
        results = []
        for command in commands:
            try:
                success, stdout, stderr = self.shell_tool.execute_command(command)
                result = {
                    "command": command,
                    "success": success,
                    "stdout": stdout or "",
                    "stderr": stderr or "",
                    "error": None,
                }
            except Exception as e:
                result = {
                    "command": command,
                    "success": False,
                    "stdout": "",
                    "stderr": "",
                    "error": str(e),
                }
            results.append(result)

        return results

    def _assess_convergence_from_json(self, llm_decision: dict, context: list) -> dict:
        """Assess convergence based on LLM's JSON response."""
        convergence = {
            "sufficient_code_coverage": False,
            "question_answered": False,
            "confidence_threshold_met": False,
        }

        # Check confidence level from LLM
        confidence = llm_decision.get("confidence_level", 0)
        if confidence >= 8:
            convergence["confidence_threshold_met"] = True

        # Check if LLM indicates no need for more shell execution
        if not llm_decision.get("need_shell_execution", True):
            convergence["question_answered"] = True

        # Check for code coverage based on number of iterations and shell commands executed
        total_commands = sum(len(ctx.get("shell_results", [])) for ctx in context)
        if total_commands >= 3 or len(context) >= 2:
            convergence["sufficient_code_coverage"] = True

        return convergence

    def _build_iteration_prompt(
        self,
        query: str,
        codebase_path: str,
        iteration: int,
        context: list,
        shell_history: list,
        shared_key_findings: list,
        convergence: dict,
        specialist_feedback: str | None = None,
    ) -> str:
        """Build unified prompt with shared knowledge base for progressive analysis."""

        base_prompt = f"""
        CODEBASE ANALYSIS - ITERATION {iteration}

        Target: {codebase_path}
        User Query: {query}

        ULTIMATE GOAL: Create a comprehensive, detailed report that thoroughly addresses the user's query.
        Your final deliverable should be a well-structured analysis that provides actionable insights and complete answers.

        ANALYSIS STRATEGY GUIDANCE:
        You are encouraged to follow a progressive analysis approach, but you have full autonomy to decide your exploration strategy based on the specific query and context:

        🎯 SUGGESTED PROGRESSION (adapt as needed):
        1. TARGETED EXPLORATION: Start with specific, query-related areas (find relevant files, grep keywords)
        2. CONTEXTUAL EXPANSION: Explore related files, dependencies, configurations around your findings
        3. DEEPER ANALYSIS: Read actual code content, understand implementation details and algorithms
        4. COMPREHENSIVE COVERAGE: Fill gaps, check alternatives, verify understanding
        5. VALIDATION & SYNTHESIS: Double-check findings, resolve inconsistencies, provide final analysis

        💡 STRATEGIC CONSIDERATIONS:
        - For simple queries: You might jump directly to targeted searches and provide quick answers
        - For complex queries: Follow the full progression to ensure comprehensive coverage
        - For architectural questions: Focus on structure, relationships, and high-level patterns
        - For implementation questions: Dive deep into specific code logic and details

        🔧 RECOMMENDED SHELL COMMANDS:
        - Exploration: ls, find, tree (understand structure)
        - Search: grep -r, grep -n (find specific content)
        - Content: cat, head, tail (read file contents)
        - Analysis: wc, file, stat (get file information)

        Remember: You must respond in valid JSON format with the exact structure specified in your system message.

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

        # Add shared knowledge base (collaborative key findings)
        if shared_key_findings:
            base_prompt += (
                "\n🧠 SHARED KNOWLEDGE BASE (Key Findings from All Iterations):\n"
            )
            for i, finding in enumerate(shared_key_findings, 1):
                base_prompt += f"{i}. {finding}\n"
            base_prompt += (
                "\nYou can ADD, UPDATE, REFINE, or REMOVE findings in your response.\n"
            )
        else:
            base_prompt += "\n🧠 SHARED KNOWLEDGE BASE: Empty (you'll create the first key findings)\n"

        # Add recent shell execution results for context
        if shell_history:
            base_prompt += "\n📋 RECENT SHELL EXECUTION RESULTS:\n"
            for shell_exec in shell_history[-2:]:  # Show last 2 executions
                base_prompt += f"\nIteration {shell_exec['iteration']}:\n"
                for result in shell_exec["results"]:
                    base_prompt += f"Command: {result['command']}\n"
                    if result["success"]:
                        stdout_preview = (
                            result["stdout"][:300] + "..."
                            if len(result["stdout"]) > 300
                            else result["stdout"]
                        )
                        base_prompt += f"Output: {stdout_preview}\n"
                    else:
                        base_prompt += f"Error: {result['stderr'] or result.get('error', 'Unknown error')}\n"
                base_prompt += "\n"

        # Add brief recent analysis context (not full history)
        if context:
            base_prompt += "\n📊 RECENT ANALYSIS CONTEXT:\n"
            for ctx in context[-1:]:  # Show only last context
                llm_decision = ctx.get("llm_decision", {})
                base_prompt += f"Previous iteration {ctx['iteration']} focused on: {llm_decision.get('next_focus_areas', 'N/A')}\n"
                base_prompt += f"Previous confidence: {llm_decision.get('confidence_level', 'N/A')}\n"

        # Add current iteration context and convergence status
        base_prompt += f"""

        📈 CURRENT ANALYSIS STATUS:
        - Iteration: {iteration}/10
        - Code coverage sufficient: {convergence['sufficient_code_coverage']}
        - Question answered: {convergence['question_answered']}
        - Confidence threshold met: {convergence['confidence_threshold_met']}

        🎯 DECISION POINTS FOR THIS ITERATION:
        Based on the shared knowledge base and your analysis so far, decide:
        1. Do you need more information via shell commands? (set need_shell_execution: true/false)
        2. What specific commands would help you gather the missing information?
        3. What is your current confidence level (1-10) in providing a comprehensive answer?
        4. If confidence >= 8, consider providing your final comprehensive analysis

        ⚠️ CRITICAL: Update the "key_findings" list:
        - ADD new important discoveries from this iteration
        - UPDATE or REFINE existing findings with new insights
        - REMOVE findings that are no longer relevant or incorrect
        - Keep findings concise but informative (1-2 sentences each)

        This shared knowledge base is the collective memory of all iterations.

        RESPONSE FORMAT: You MUST respond in valid JSON format with these exact fields:
        {{
            "need_shell_execution": true/false,
            "shell_commands": ["command1", "command2", ...],
            "key_findings": ["Updated list of key findings from all iterations"],
            "current_analysis": "Your analysis of this iteration and current understanding",
            "confidence_level": 1-10,
            "next_focus_areas": "What you plan to focus on next (or 'Final analysis complete' if done)"
        }}
        """

        return base_prompt

    def _should_terminate(self, convergence: dict) -> bool:
        """Determine if analysis should terminate based on convergence indicators."""
        # Terminate if all convergence criteria are met
        return all(convergence.values())

    def _synthesize_final_response(
        self, query: str, context: list, shared_key_findings: list, convergence: dict
    ) -> str:
        """Synthesize final comprehensive response from shared knowledge base and iterations."""
        if not context:
            return "No analysis performed."

        # Get the most recent analysis
        final_context = context[-1]
        final_decision = final_context.get("llm_decision", {})
        final_analysis = final_decision.get("current_analysis", "No analysis available")
        final_confidence = final_decision.get("confidence_level", 0)

        # Create comprehensive synthesis
        synthesis = f"""
        CODEBASE ANALYSIS COMPLETE

        Query: {query}
        Iterations: {len(context)}
        Final Confidence Level: {final_confidence}/10
        Convergence Status: {convergence}

        KEY FINDINGS (Collaborative Knowledge Base):
        """

        # Add key findings
        if shared_key_findings:
            for i, finding in enumerate(shared_key_findings, 1):
                synthesis += f"{i}. {finding}\n"
        else:
            synthesis += "No key findings recorded.\n"

        synthesis += f"""

        FINAL ANALYSIS:
        {final_analysis}

        EXECUTION SUMMARY:
        """

        # Add execution summary
        for ctx in context:
            iteration = ctx["iteration"]
            shell_results = ctx.get("shell_results", [])
            llm_decision = ctx.get("llm_decision", {})

            synthesis += f"\n--- Iteration {iteration} ---\n"
            synthesis += f"Commands executed: {len(shell_results)}\n"
            if shell_results:
                for result in shell_results:
                    status = "✓" if result["success"] else "✗"
                    synthesis += f"  {status} {result['command']}\n"
            synthesis += f"Confidence: {llm_decision.get('confidence_level', 'N/A')}\n"

            # Show knowledge base growth
            kb_size = len(llm_decision.get("key_findings", []))
            synthesis += f"Knowledge base size: {kb_size} findings\n"

        return synthesis

    def _get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        import datetime

        return datetime.datetime.now().isoformat()

    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON content from LLM response, handling markdown code blocks."""
        import re

        # Try to find JSON within markdown code blocks
        json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        matches = re.findall(json_pattern, response_text, re.DOTALL)

        if matches:
            # Use the first JSON block found
            json_content = matches[0].strip()
            self.logger.debug(f"Extracted JSON from markdown: {json_content[:200]}...")
            return json_content

        # If no markdown blocks, check if the response starts/ends with braces
        stripped = response_text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            self.logger.debug("Found JSON-like content without markdown")
            return stripped

        # Last resort: try to find JSON pattern in the text
        json_like_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        json_matches = re.findall(json_like_pattern, response_text, re.DOTALL)

        if json_matches:
            # Try to find the most complete JSON (longest match)
            longest_match = max(json_matches, key=len)
            self.logger.debug(f"Found JSON-like pattern: {longest_match[:200]}...")
            return longest_match

        # If no JSON found, return original text and let JSON parser fail
        self.logger.warning("No JSON pattern found in response")
        return response_text

    @property
    def agent(self) -> AssistantAgent:
        """Get the underlying AutoGen agent."""
        return self._agent
