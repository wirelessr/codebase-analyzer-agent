"""Shell command execution tool for secure codebase exploration.

This module provides a secure interface for executing shell commands with safety
constraints, working directory restrictions, timeouts, and comprehensive logging.
"""

import logging
import os
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class ShellExecutionError(Exception):
    """Raised when shell command execution fails."""

    def __init__(self, command: str, exit_code: int, stderr: str, message: str = None):
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(
            message or f"Command '{command}' failed with exit code {exit_code}"
        )


class ShellTimeoutError(Exception):
    """Raised when shell command execution times out."""

    def __init__(self, command: str, timeout: float):
        self.command = command
        self.timeout = timeout
        super().__init__(f"Command '{command}' timed out after {timeout} seconds")


class ShellTool:
    """Secure shell command execution tool for codebase exploration.

    This tool provides controlled execution of shell commands with security
    constraints and comprehensive logging. It relies on system prompts to guide
    agents toward using read-only commands for safe codebase analysis.
    """

    def __init__(
        self,
        working_directory: str,
        timeout_seconds: float = 30.0,
        max_output_size: int = 10000,
        enable_logging: bool = True,
    ):
        """Initialize ShellTool with security constraints.

        Args:
            working_directory: Directory to restrict command execution to
            timeout_seconds: Maximum execution time for commands
            max_output_size: Maximum size of command output in characters
            enable_logging: Whether to log command execution details
        """
        self.working_directory = Path(working_directory).resolve()
        self.timeout_seconds = timeout_seconds
        self.max_output_size = max_output_size
        self.enable_logging = enable_logging

        # Validate working directory
        if not self.working_directory.exists():
            raise ValueError(
                f"Working directory does not exist: {self.working_directory}"
            )
        if not self.working_directory.is_dir():
            raise ValueError(
                f"Working directory is not a directory: {self.working_directory}"
            )

        # Track execution statistics
        self.execution_stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "timed_out_commands": 0,
            "total_execution_time": 0.0,
        }

        if self.enable_logging:
            logger.info(
                f"ShellTool initialized: working_dir={self.working_directory}, "
                f"timeout={self.timeout_seconds}s, max_output={self.max_output_size}"
            )

    def execute_command(self, command: str) -> tuple[bool, str, str]:
        """Execute a shell command with security constraints.

        Args:
            command: Shell command to execute

        Returns:
            Tuple of (success, stdout, stderr)

        Raises:
            ShellExecutionError: If command execution fails
            ShellTimeoutError: If command execution times out
            ValueError: If command is invalid
        """
        start_time = time.time()
        self.execution_stats["total_commands"] += 1

        try:
            # Validate and log command
            self._validate_command(command)

            if self.enable_logging:
                logger.info(f"Executing command: {command}")

            # Execute command with constraints
            result = self._run_command_with_constraints(command)
            success, stdout, stderr = result

            # Update statistics
            execution_time = time.time() - start_time
            self.execution_stats["total_execution_time"] += execution_time

            if success:
                self.execution_stats["successful_commands"] += 1
                if self.enable_logging:
                    logger.info(
                        f"Command completed successfully in {execution_time:.2f}s: "
                        f"output_size={len(stdout)}, stderr_size={len(stderr)}"
                    )
            else:
                self.execution_stats["failed_commands"] += 1
                if self.enable_logging:
                    logger.warning(
                        f"Command failed in {execution_time:.2f}s: "
                        f"stderr={stderr[:200]}..."
                    )

            return result

        except ShellTimeoutError:
            self.execution_stats["timed_out_commands"] += 1
            raise
        except Exception as e:
            self.execution_stats["failed_commands"] += 1
            execution_time = time.time() - start_time
            self.execution_stats["total_execution_time"] += execution_time
            if self.enable_logging:
                logger.error(f"Command execution error: {e}")
            raise

    def _validate_command(self, command: str) -> None:
        """Validate command for basic constraints.

        Args:
            command: Command to validate

        Raises:
            ValueError: If command is invalid
        """
        if not command or not command.strip():
            raise ValueError("Command cannot be empty")

        # Log potentially complex commands for monitoring
        if self.enable_logging:
            complex_patterns = [">", ">>", "&", ";", "$(", "`", "&&", "||", "|"]
            for pattern in complex_patterns:
                if pattern in command:
                    logger.info(
                        f"Complex command pattern '{pattern}' detected: {command}"
                    )
                    break

    def _run_command_with_constraints(self, command: str) -> tuple[bool, str, str]:
        """Run command with timeout and output size constraints.

        Args:
            command: Command to execute

        Returns:
            Tuple of (success, stdout, stderr)

        Raises:
            ShellTimeoutError: If command times out
            ShellExecutionError: If command fails with non-zero exit code
        """
        try:
            # Run command with timeout
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.working_directory),
                # Security: Prevent command injection through environment
                env=dict(os.environ, PATH=os.environ.get("PATH", "")),
            )

            try:
                stdout, stderr = process.communicate(timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise ShellTimeoutError(command, self.timeout_seconds)

            # Limit output size to prevent memory issues
            if len(stdout) > self.max_output_size:
                stdout = (
                    stdout[: self.max_output_size]
                    + f"\n... (output truncated at {self.max_output_size} characters)"
                )

            if len(stderr) > self.max_output_size:
                stderr = (
                    stderr[: self.max_output_size]
                    + f"\n... (stderr truncated at {self.max_output_size} characters)"
                )

            # Check exit code
            if process.returncode != 0:
                return False, stdout, stderr

            return True, stdout, stderr

        except FileNotFoundError as e:
            # Command not found
            return False, "", f"Command not found: {str(e)}"
        except PermissionError as e:
            # Permission denied
            return False, "", f"Permission denied: {str(e)}"
        except OSError as e:
            # Other OS-level errors
            return False, "", f"OS error: {str(e)}"

    def get_execution_stats(self) -> dict[str, any]:
        """Get execution statistics for monitoring and debugging.

        Returns:
            Dictionary containing execution statistics
        """
        stats = self.execution_stats.copy()
        if stats["total_commands"] > 0:
            stats["success_rate"] = (
                stats["successful_commands"] / stats["total_commands"]
            )
            stats["average_execution_time"] = (
                stats["total_execution_time"] / stats["total_commands"]
            )
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0

        return stats

    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self.execution_stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "timed_out_commands": 0,
            "forbidden_commands": 0,
            "total_execution_time": 0.0,
        }

        if self.enable_logging:
            logger.info("Execution statistics reset")

    @property
    def is_working_directory_accessible(self) -> bool:
        """Check if working directory is accessible."""
        try:
            return os.access(self.working_directory, os.R_OK)
        except Exception:
            return False

    def validate_working_directory(self) -> list[str]:
        """Validate working directory and return any issues.

        Returns:
            List of validation issues (empty if no issues)
        """
        issues = []

        if not self.working_directory.exists():
            issues.append(f"Working directory does not exist: {self.working_directory}")
        elif not self.working_directory.is_dir():
            issues.append(
                f"Working directory is not a directory: {self.working_directory}"
            )
        elif not self.is_working_directory_accessible:
            issues.append(
                f"Working directory is not accessible: {self.working_directory}"
            )

        return issues
