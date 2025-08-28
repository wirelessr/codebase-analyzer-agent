"""
Integration test for Code Analyzer with real LLM and tool calls.

This test verifies that the Code Analyzer actually calls shell tools
when interacting with a real LLM to analyze codebases.
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
    
    def execute_command(self, command: str):
        """Execute command and track the call."""
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
            return (result.returncode == 0, result.stdout, result.stderr)
            
        except Exception as e:
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
            return (False, "", str(e))


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
    
    def test_analyzer_calls_shell_tools(self, real_config, test_codebase):
        """Test that analyzer actually calls shell tools with real LLM."""
        
        tracking_tool = TrackingShellTool(test_codebase)
        analyzer = CodeAnalyzer(real_config, tracking_tool)
        
        task = f"""
        Analyze the Python project in: {test_codebase}
        
        Use shell commands to:
        1. List the files
        2. Find Python files
        3. Provide a brief summary
        """
        
        print("🚀 Starting analysis with real LLM...")
        
        async def run_analysis():
            return await analyzer.agent.run(task=task)
        
        result = asyncio.run(run_analysis())
        
        print(f"📊 Analysis completed!")
        print(f"🔧 Commands executed: {tracking_tool.calls}")
        
        # Verify that tools were called
        assert len(tracking_tool.calls) > 0, \
            f"No shell tools were called. Result: {result}"
        
        # Verify basic exploration happened
        commands_str = ' '.join(tracking_tool.calls).lower()
        exploration_happened = any(cmd in commands_str for cmd in 
                                 ['ls', 'find', 'dir', '*.py'])
        
        assert exploration_happened, \
            f"Expected exploration commands, got: {tracking_tool.calls}"
        
        print("✅ Test passed: Analyzer successfully called shell tools!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
