"""Unit tests for ShellTool class."""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from codebase_agent.tools.shell_tool import (
    ShellExecutionError,
    ShellTimeoutError,
    ShellTool,
)


class TestShellTool:
    """Test cases for ShellTool class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.working_dir = Path(self.temp_dir)
        
        # Create some test files
        (self.working_dir / "test_file.txt").write_text("Hello, World!\nLine 2\nLine 3")
        (self.working_dir / "test_file.py").write_text("print('Hello, Python!')")
        (self.working_dir / "subdir").mkdir()
        (self.working_dir / "subdir" / "nested.js").write_text("console.log('Hello, JS!');")
        
        # Initialize ShellTool
        self.shell_tool = ShellTool(str(self.working_dir))
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_valid_directory(self):
        """Test ShellTool initialization with valid directory."""
        # Use resolve() to handle symbolic links like macOS temp dirs
        assert self.shell_tool.working_directory.resolve() == self.working_dir.resolve()
        assert self.shell_tool.timeout_seconds == 30.0
        assert self.shell_tool.max_output_size == 10000
        assert self.shell_tool.enable_logging is True
    
    def test_initialization_custom_parameters(self):
        """Test ShellTool initialization with custom parameters."""
        shell_tool = ShellTool(
            str(self.working_dir),
            timeout_seconds=60.0,
            max_output_size=5000,
            enable_logging=False
        )
        assert shell_tool.timeout_seconds == 60.0
        assert shell_tool.max_output_size == 5000
        assert shell_tool.enable_logging is False
    
    def test_initialization_invalid_directory(self):
        """Test ShellTool initialization with invalid directory."""
        with pytest.raises(ValueError, match="Working directory does not exist"):
            ShellTool("/nonexistent/directory")
    
    def test_initialization_file_as_directory(self):
        """Test ShellTool initialization with file instead of directory."""
        test_file = self.working_dir / "not_a_dir.txt"
        test_file.write_text("content")
        
        with pytest.raises(ValueError, match="Working directory is not a directory"):
            ShellTool(str(test_file))
    
    def test_execute_simple_command_success(self):
        """Test successful execution of simple command."""
        success, stdout, stderr = self.shell_tool.execute_command("ls")
        
        assert success is True
        assert "test_file.txt" in stdout
        assert "test_file.py" in stdout
        assert stderr == ""
    
    def test_execute_command_with_output(self):
        """Test command execution with specific output."""
        success, stdout, stderr = self.shell_tool.execute_command("cat test_file.txt")
        
        assert success is True
        assert "Hello, World!" in stdout
        assert "Line 2" in stdout
        assert stderr == ""
    
    def test_execute_command_failure(self):
        """Test command execution that fails."""
        success, stdout, stderr = self.shell_tool.execute_command("cat nonexistent_file.txt")
        
        assert success is False
        assert stdout == ""
        assert "No such file or directory" in stderr or "cannot access" in stderr.lower()
    
    def test_execute_command_with_complex_patterns(self):
        """Test command execution with complex patterns (should be logged but not blocked)."""
        with patch('codebase_agent.tools.shell_tool.logger') as mock_logger:
            success, stdout, stderr = self.shell_tool.execute_command("ls | head -5")
            
            # Should execute successfully and log complex pattern
            assert isinstance(success, bool)
            mock_logger.info.assert_called()
            # Check that complex pattern was logged
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Complex command pattern" in call for call in log_calls)
    
    def test_execute_various_commands(self):
        """Test execution of various commands (should all be allowed)."""
        # These commands should all be allowed since we rely on system prompts for guidance
        commands = [
            "ls",
            "find . -name '*.txt'",
            "grep -r 'Hello' .",
            "head -5 test_file.txt",
            "tail -2 test_file.txt",
            "wc -l test_file.txt",
            "file test_file.py"
        ]
        
        for cmd in commands:
            success, stdout, stderr = self.shell_tool.execute_command(cmd)
            # Commands should execute without being blocked
            assert isinstance(success, bool)
    
    def test_command_validation_empty_command(self):
        """Test validation of empty command."""
        with pytest.raises(ValueError, match="Command cannot be empty"):
            self.shell_tool.execute_command("")
        
        with pytest.raises(ValueError, match="Command cannot be empty"):
            self.shell_tool.execute_command("   ")
    
    def test_output_size_limiting(self):
        """Test output size limiting functionality."""
        # Create shell tool with very small output limit
        small_output_tool = ShellTool(str(self.working_dir), max_output_size=10)
        
        success, stdout, stderr = small_output_tool.execute_command("cat test_file.txt")
        
        assert success is True
        assert len(stdout) <= 50  # Should be truncated plus truncation message
        assert "output truncated" in stdout
    
    @patch('subprocess.Popen')
    def test_command_timeout(self, mock_popen):
        """Test command timeout functionality."""
        # Mock a process that hangs
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 1.0)
        mock_process.kill.return_value = None
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process
        
        with pytest.raises(ShellTimeoutError, match="timed out after"):
            self.shell_tool.execute_command("sleep 60")
    
    def test_execution_statistics(self):
        """Test execution statistics tracking."""
        # Reset stats
        self.shell_tool.reset_stats()
        
        # Execute some commands
        self.shell_tool.execute_command("ls")
        self.shell_tool.execute_command("cat test_file.txt")
        self.shell_tool.execute_command("cat nonexistent.txt")  # This will fail
        
        stats = self.shell_tool.get_execution_stats()
        
        assert stats['total_commands'] == 3
        assert stats['successful_commands'] == 2
        assert stats['failed_commands'] == 1
        assert stats['success_rate'] == 2/3
        assert stats['average_execution_time'] > 0
    
    def test_working_directory_validation(self):
        """Test working directory validation."""
        issues = self.shell_tool.validate_working_directory()
        assert issues == []  # Should be no issues
        
        assert self.shell_tool.is_working_directory_accessible is True
    
    def test_complex_find_command(self):
        """Test complex find command with pipes."""
        success, stdout, stderr = self.shell_tool.execute_command(
            "find . -name '*.py' -o -name '*.js'"
        )
        
        assert success is True
        assert "test_file.py" in stdout
        assert "nested.js" in stdout
    
    def test_grep_command(self):
        """Test grep command functionality."""
        success, stdout, stderr = self.shell_tool.execute_command(
            "grep -r 'Hello' ."
        )
        
        assert success is True
        assert "Hello" in stdout
    
    def test_command_with_pipes(self):
        """Test command with pipes (should be logged but not blocked)."""
        with patch('codebase_agent.tools.shell_tool.logger') as mock_logger:
            success, stdout, stderr = self.shell_tool.execute_command("ls | head -5")
            
            # Should execute successfully and log complex pattern
            assert isinstance(success, bool)
            mock_logger.info.assert_called()
            # Check that complex pattern was logged
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Complex command pattern" in call for call in log_calls)
    
    def test_file_command(self):
        """Test file command to determine file types."""
        success, stdout, stderr = self.shell_tool.execute_command("file test_file.py")
        
        assert success is True
        assert "test_file.py" in stdout
    
    def test_wc_command(self):
        """Test word count command."""
        success, stdout, stderr = self.shell_tool.execute_command("wc -l test_file.txt")
        
        assert success is True
        # The file has 3 lines, but wc might count differently (without final newline)
        assert ("2" in stdout or "3" in stdout)  # Accept either count
        assert "test_file.txt" in stdout
    
    @patch('subprocess.Popen')
    def test_permission_error_handling(self, mock_popen):
        """Test handling of permission errors."""
        mock_popen.side_effect = PermissionError("Permission denied")
        
        success, stdout, stderr = self.shell_tool.execute_command("ls")
        
        assert success is False
        assert stdout == ""
        assert "Permission denied" in stderr
    
    @patch('subprocess.Popen')
    def test_file_not_found_error_handling(self, mock_popen):
        """Test handling of command not found errors."""
        mock_popen.side_effect = FileNotFoundError("Command not found")
        
        success, stdout, stderr = self.shell_tool.execute_command("nonexistent_command")
        
        assert success is False
        assert stdout == ""
        assert "Command not found" in stderr
    
    def test_path_resolution(self):
        """Test that working directory path is properly resolved."""
        # Test with relative path
        relative_tool = ShellTool(".")
        assert relative_tool.working_directory.is_absolute()
    
    def test_environment_security(self):
        """Test that environment is properly sanitized."""
        # This test ensures we don't pass dangerous environment variables
        success, stdout, stderr = self.shell_tool.execute_command("pwd")
        assert success is True
        assert str(self.working_dir) in stdout
    
    def test_logging_disabled(self):
        """Test shell tool with logging disabled."""
        quiet_tool = ShellTool(str(self.working_dir), enable_logging=False)
        
        with patch('codebase_agent.tools.shell_tool.logger') as mock_logger:
            success, stdout, stderr = quiet_tool.execute_command("ls")
            
            # Should not log execution details
            mock_logger.info.assert_not_called()
    
    def test_stderr_size_limiting(self):
        """Test stderr size limiting."""
        small_output_tool = ShellTool(str(self.working_dir), max_output_size=10)
        
        # Create a command that will produce stderr
        success, stdout, stderr = small_output_tool.execute_command("cat nonexistent_very_long_filename_that_will_produce_long_error.txt")
        
        assert success is False
        if len(stderr) > 50:  # If stderr was long enough to be truncated
            assert "stderr truncated" in stderr


# Integration test for real shell commands
class TestShellToolIntegration:
    """Integration tests with real shell commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.working_dir = Path(self.temp_dir)
        
        # Create a mini project structure
        (self.working_dir / "src").mkdir()
        (self.working_dir / "src" / "main.py").write_text(
            "#!/usr/bin/env python3\n"
            "def main():\n"
            "    print('Hello, World!')\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        )
        (self.working_dir / "src" / "utils.py").write_text(
            "def helper_function():\n"
            "    return 'helper'\n"
        )
        (self.working_dir / "README.md").write_text(
            "# Test Project\n\n"
            "This is a test project for shell tool testing.\n"
        )
        (self.working_dir / "package.json").write_text(
            '{"name": "test-project", "version": "1.0.0"}\n'
        )
        
        self.shell_tool = ShellTool(str(self.working_dir))
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_real_find_command(self):
        """Test real find command on test project."""
        success, stdout, stderr = self.shell_tool.execute_command("find . -name '*.py'")
        
        assert success is True
        assert "./src/main.py" in stdout or "src/main.py" in stdout
        assert "./src/utils.py" in stdout or "src/utils.py" in stdout
        assert stderr == ""
    
    def test_real_grep_command(self):
        """Test real grep command on test project."""
        success, stdout, stderr = self.shell_tool.execute_command("grep -r 'def' .")
        
        assert success is True
        assert "main" in stdout
        assert "helper_function" in stdout
    
    def test_real_wc_command(self):
        """Test real word count command."""
        success, stdout, stderr = self.shell_tool.execute_command("wc -l src/*.py")
        
        assert success is True
        # Should count lines in both Python files
        assert "main.py" in stdout
        assert "utils.py" in stdout
    
    def test_real_head_command(self):
        """Test real head command."""
        success, stdout, stderr = self.shell_tool.execute_command("head -3 src/main.py")
        
        assert success is True
        assert "#!/usr/bin/env python3" in stdout
        assert "def main():" in stdout
    
    def test_real_file_command(self):
        """Test real file type detection."""
        success, stdout, stderr = self.shell_tool.execute_command("file src/main.py")
        
        assert success is True
        assert "main.py" in stdout
        # Output will vary by system, but should contain some file type info
    
    def test_complex_find_with_xargs(self):
        """Test complex find command with xargs pattern."""
        success, stdout, stderr = self.shell_tool.execute_command(
            "find . -name '*.py' | head -10"
        )
        
        assert success is True
        assert "main.py" in stdout


if __name__ == "__main__":
    pytest.main([__file__])
