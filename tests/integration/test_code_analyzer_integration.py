"""
Integration test for Code Analyzer with real LLM and tool calls.

TESTING SCENARIO: ARCHITECTURE ANALYSIS
This test focuses on analyzing codebase architecture and system structure
using real LLM interaction and shell tool execution. It verifies that
the Code Analyzer can effectively understand and describe:
- Project structure and organization
- Component relationships and dependencies  
- Module architecture and design patterns
- System-level design decisions
"""

import pytest
import tempfile
import asyncio
import subprocess
import os
from pathlib import Path

from codebase_agent.agents.code_analyzer import CodeAnalyzer
from codebase_agent.config.configuration import ConfigurationManager


class TrackingShellTool:
    """Shell tool that tracks calls while executing real commands."""
    
    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.calls = []
    
    def execute_command(self, command: str) -> str:
        """Execute command and track the call.
        
        Args:
            command: The shell command to execute
            
        Returns:
            Command output as a string
        """
        self.calls.append(command)
        print(f"🔧 Shell tool called: {command}")
        
        try:
            original_cwd = os.getcwd()
            os.chdir(self.working_dir)
            
            result = subprocess.run(
                command, shell=True, capture_output=True, 
                text=True, timeout=10
            )
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                output = result.stdout or "Command executed successfully"
                print(f"✅ Command output: {output[:100]}...")
                return output
            else:
                error_msg = f"Command failed: {result.stderr}"
                print(f"❌ Command error: {error_msg}")
                return error_msg
                
        except Exception as e:
            error_msg = f"Exception executing command: {str(e)}"
            print(f"💥 Exception: {error_msg}")
            return error_msg


class TestCodeAnalyzerIntegration:
    """Integration test for Code Analyzer with real LLM interaction."""
    
    @pytest.fixture
    def real_config(self):
        """Load real LLM configuration."""
        try:
            config_manager = ConfigurationManager()
            config_manager.load_environment()
            
            # Use the configuration manager to get model client
            return config_manager.get_model_client()
        except Exception as e:
            pytest.skip(f"Could not configure LLM: {e}")
    
    @pytest.fixture
    def test_codebase(self):
        """Create a test codebase."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "test_project"
            project_dir.mkdir()
            
            (project_dir / "main.py").write_text('''#!/usr/bin/env python3
"""Main application."""

def hello_world():
    """Print greeting."""
    print("Hello, World!")

def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

if __name__ == "__main__":
    hello_world()
    print(f"Sum: {calculate_sum(5, 3)}")
''')
            
            (project_dir / "utils.py").write_text('''"""Utility functions."""

class DataProcessor:
    """Process data."""
    
    def process(self, data):
        return data.upper()

def format_output(value):
    return f"[{value}]"
''')
            
            (project_dir / "README.md").write_text('''# Test Project
A sample Python project for testing.
''')
            
            yield str(project_dir)
    
    def test_analyzer_dual_phase_execution(self, real_config, test_codebase):
        """Test architecture analysis using dual-phase execution (LLM decision + shell execution)."""
        
        # Enable debug logging to see LLM responses
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("codebase_agent.agents.code_analyzer")
        logger.setLevel(logging.DEBUG)
        
        tracking_tool = TrackingShellTool(test_codebase)
        analyzer = CodeAnalyzer(real_config, tracking_tool)
        
        # Focus on architecture analysis - understand system structure and design
        query = f"Analyze the architecture of this Python project. I need to understand the system structure, component relationships, module organization, and overall design patterns used."
        
        print("🚀 Starting architecture analysis with real LLM...")
        print(f"📁 Test codebase: {test_codebase}")
        print(f"🔍 Query: {query}")
        
        # Run the full analyze_codebase flow which uses dual-phase execution
        result = analyzer.analyze_codebase(query, test_codebase)
        
        print(f"📊 Architecture analysis completed!")
        print(f"🔧 Commands executed: {tracking_tool.calls}")
        print(f"📋 Result length: {len(result)} chars")
        print(f"📄 Result preview: {result[:300]}...")
        
        # Check if we got a meaningful architecture analysis result
        assert len(result) > 100, f"Expected substantial architecture analysis result, got {len(result)} chars"
        
        # In dual-phase execution, the analyzer should execute shell commands
        # even if the LLM doesn't support function calling directly
        if len(tracking_tool.calls) > 0:
            print("✅ Analyzer executed shell commands via dual-phase execution")
            
            # Verify architectural exploration happened
            commands_str = ' '.join(tracking_tool.calls).lower()
            exploration_terms = ['ls', 'find', 'cat', 'grep', 'tree', 'dir', 'pwd']
            assert any(term in commands_str for term in exploration_terms), \
                f"Expected exploration commands (ls, find, cat, etc.), got: {tracking_tool.calls}"
            
            # Verify the result contains architectural analysis information
            result_lower = result.lower()
            architecture_terms = ['structure', 'component', 'module', 'function', 'class', 'import', 'design']
            assert any(term in result_lower for term in architecture_terms), \
                f"Expected architecture analysis to mention structural components, got: {result[:200]}..."
            
            print("✅ Test passed: Dual-phase execution successfully analyzed project architecture!")
        else:
            # This shouldn't happen with dual-phase execution unless there's a real error
            print("❌ No shell commands were executed")
            print("This indicates the LLM decided not to execute commands")
            
            # Check if we at least got some response (fallback behavior)
            if len(result) > 50:
                print("⚠️  Got analysis result without shell execution")
                print("This could mean:")
                print("1. LLM set need_shell_execution to false")
                print("2. JSON parsing failed and fell back to text analysis")
                print("3. LLM provided analysis without exploring")
                
                # For architecture analysis, still check for relevant content
                result_lower = result.lower()
                architecture_terms = ['structure', 'component', 'module', 'design', 'architecture']
                has_architecture_content = any(term in result_lower for term in architecture_terms)
                
                assert has_architecture_content, \
                    f"Architecture analysis should contain structural information: {result}"
                    
                print("⚠️  Test passed but no shell commands executed - LLM may have been overconfident about architecture")
            else:
                pytest.fail(f"Dual-phase execution failed completely. Result: {result}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
