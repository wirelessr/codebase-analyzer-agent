"""
Enhanced logging and monitoring system for AutoGen Codebase Agent.

This module provides structured event logging for analysis cycles, commands, and reviews,
with conversation timeline tracking and performance monitoring capabilities.
"""

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LogEvent:
    """Represents a single logged event with structured data."""

    step_id: int | float
    timestamp: str
    agent: str
    event_type: str
    data: dict[str, Any]


@dataclass
class SessionStats:
    """Statistics for a complete session."""

    total_analyzer_iterations: int = 0
    total_specialist_reviews: int = 0
    total_commands_executed: int = 0
    execution_time: float = 0.0


class SessionLogs:
    """Container for session log data with filtering and analysis methods."""

    def __init__(self, log_data: dict[str, Any]):
        """Initialize from log data dictionary."""
        self.session_id = log_data["session_id"]
        self.timestamp = log_data.get("timestamp", "")
        self.codebase_path = log_data.get("codebase_path", "")
        self.user_query = log_data.get("user_query", "")
        self.agents_involved = log_data.get("agents_involved", [])
        self.timeline = [
            LogEvent(**event) for event in log_data.get("execution_timeline", [])
        ]
        self.final_response = log_data.get("final_response", "")
        self.stats = SessionStats(**log_data.get("execution_stats", {}))

    def filter_by_event_type(self, event_type: str) -> list[LogEvent]:
        """Filter events by type."""
        return [event for event in self.timeline if event.event_type == event_type]

    def filter_by_agent(self, agent_name: str) -> list[LogEvent]:
        """Filter events by agent."""
        return [event for event in self.timeline if event.agent == agent_name]

    def filter_after_timestamp(self, timestamp: str) -> "SessionLogs":
        """Get events after a specific timestamp."""
        filtered_timeline = [
            event for event in self.timeline if event.timestamp > timestamp
        ]
        return SessionLogs(
            {
                "session_id": self.session_id,
                "timestamp": self.timestamp,
                "codebase_path": self.codebase_path,
                "user_query": self.user_query,
                "agents_involved": self.agents_involved,
                "execution_timeline": [asdict(event) for event in filtered_timeline],
                "final_response": self.final_response,
                "execution_stats": asdict(self.stats),
            }
        )

    def get_knowledge_before_timestamp(self, timestamp: str) -> str:
        """Extract accumulated knowledge before a timestamp."""
        knowledge_events = [
            event
            for event in self.timeline
            if event.event_type == "knowledge_update" and event.timestamp < timestamp
        ]
        if not knowledge_events:
            return ""
        # Get the latest knowledge update before the timestamp
        latest_event = max(knowledge_events, key=lambda e: e.timestamp)
        return " ".join(latest_event.data.get("new_findings", []))

    def get_final_knowledge(self) -> str:
        """Extract final accumulated knowledge."""
        knowledge_events = [
            event for event in self.timeline if event.event_type == "knowledge_update"
        ]
        if not knowledge_events:
            return ""
        # Get the most recent knowledge update
        latest_event = max(knowledge_events, key=lambda e: e.timestamp)
        return " ".join(latest_event.data.get("new_findings", []))


class LogParser:
    """Utility for parsing and analyzing session logs."""

    @staticmethod
    def get_session_logs(
        session_id: str, logs_dir: str | Path = None
    ) -> SessionLogs | None:
        """Parse and structure logs for a specific session."""
        if logs_dir is None:
            logs_dir = Path("logs/conversations")
        else:
            logs_dir = Path(logs_dir)  # Ensure it's a Path object

        # Look for log files matching the session ID
        for log_file in logs_dir.glob(f"*_{session_id}.json"):
            try:
                with open(log_file) as f:
                    log_data = json.load(f)
                return SessionLogs(log_data)
            except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
                logging.error(f"Failed to parse log file {log_file}: {e}")
                continue

        return None

    @staticmethod
    def filter_by_event_type(logs: SessionLogs, event_type: str) -> list[LogEvent]:
        """Filter logs by specific event types."""
        return logs.filter_by_event_type(event_type)

    @staticmethod
    def get_state_at_step(logs: SessionLogs, step_id: int | float) -> dict[str, Any]:
        """Reconstruct agent state at a specific step."""
        # Find all events up to and including the specified step
        events_up_to_step = [
            event for event in logs.timeline if event.step_id <= step_id
        ]

        # Reconstruct state from events
        state = {
            "current_iteration": 0,
            "accumulated_knowledge": [],
            "confidence_level": 0.0,
            "commands_executed": [],
            "review_count": 0,
        }

        for event in events_up_to_step:
            if event.event_type == "iteration_start":
                state["current_iteration"] = event.data.get("iteration_number", 0)
            elif event.event_type == "knowledge_update":
                state["accumulated_knowledge"].extend(
                    event.data.get("new_findings", [])
                )
                state["confidence_level"] = event.data.get("confidence_level", 0.0)
            elif event.event_type == "command_executed":
                state["commands_executed"].append(event.data.get("command", ""))
            elif event.event_type == "review_complete":
                state["review_count"] = event.data.get("review_number", 0)

        return state


class StructuredLogger:
    """Enhanced logger for structured event logging with conversation timeline tracking."""

    def __init__(self, logs_dir: str = "logs"):
        """Initialize the structured logger."""
        self.logs_dir = Path(logs_dir)
        self.conversations_dir = self.logs_dir / "conversations"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

        # Set up standard logging
        self._setup_standard_logging()

        # Session tracking
        self.current_session: dict[str, Any] | None = None
        self.step_counter = 0
        self.session_start_time: float | None = None

        self.logger = logging.getLogger(__name__)

    def _setup_standard_logging(self) -> None:
        """Set up standard Python logging configuration."""
        log_file = self.logs_dir / "agent.log"

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File handler - captures all INFO and above
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler - only shows ERROR and above
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.ERROR)

        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Prevent duplicate logs
        logger.propagate = False

    def start_session(
        self, user_query: str, codebase_path: str, agents_involved: list[str]
    ) -> str:
        """Start a new logging session."""
        session_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc).isoformat()

        self.current_session = {
            "session_id": session_id,
            "timestamp": timestamp,
            "codebase_path": codebase_path,
            "user_query": user_query,
            "agents_involved": agents_involved,
            "execution_timeline": [],
            "final_response": "",
            "execution_stats": SessionStats(),
        }

        self.step_counter = 0
        self.session_start_time = time.time()

        self.logger.info(f"Started session {session_id} for query: {user_query}")
        return session_id

    def log_event(self, agent: str, event_type: str, data: dict[str, Any]) -> None:
        """Log a structured event to the current session."""
        if self.current_session is None:
            raise ValueError("No active session. Call start_session() first.")

        self.step_counter += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        event = {
            "step_id": self.step_counter,
            "timestamp": timestamp,
            "agent": agent,
            "event_type": event_type,
            "data": data,
        }

        self.current_session["execution_timeline"].append(event)

        # Update statistics
        stats = self.current_session["execution_stats"]
        if event_type == "iteration_complete":
            stats.total_analyzer_iterations += 1
        elif event_type == "review_complete":
            stats.total_specialist_reviews += 1
        elif event_type == "command_executed":
            stats.total_commands_executed += 1

    def log_analysis_cycle_start(
        self,
        agent: str,
        iteration_number: int,
        current_knowledge: list[str],
        planned_commands: list[str],
    ) -> None:
        """Log the start of an analysis cycle."""
        data = {
            "iteration_number": iteration_number,
            "current_knowledge": current_knowledge,
            "planned_commands": planned_commands,
        }
        self.log_event(agent, "iteration_start", data)

    def log_command_executed(
        self,
        agent: str,
        command: str,
        exit_code: int,
        output_size: int,
        files_found: list[str] = None,
    ) -> None:
        """Log a shell command execution."""
        data = {
            "command": command,
            "exit_code": exit_code,
            "output_size": output_size,
            "files_found": files_found or [],
        }
        self.log_event(agent, "command_executed", data)

    def log_knowledge_update(
        self,
        agent: str,
        new_findings: list[str],
        confidence_level: float,
        next_investigation_areas: list[str],
    ) -> None:
        """Log a knowledge update event."""
        data = {
            "new_findings": new_findings,
            "confidence_level": confidence_level,
            "next_investigation_areas": next_investigation_areas,
        }
        self.log_event(agent, "knowledge_update", data)

    def log_iteration_complete(
        self,
        agent: str,
        iteration_number: int,
        total_commands: int,
        self_assessment: str,
        continue_analysis: bool,
    ) -> None:
        """Log the completion of an analysis iteration."""
        data = {
            "iteration_number": iteration_number,
            "total_commands": total_commands,
            "self_assessment": self_assessment,
            "continue_analysis": continue_analysis,
        }
        self.log_event(agent, "iteration_complete", data)

    def log_self_assessment(
        self,
        agent: str,
        iteration_number: int,
        confidence_level: float,
        knowledge_completeness: float,
        assessment_result: str,
        reasoning: str,
    ) -> None:
        """Log a self-assessment event."""
        data = {
            "iteration_number": iteration_number,
            "confidence_level": confidence_level,
            "knowledge_completeness": knowledge_completeness,
            "assessment_result": assessment_result,
            "reasoning": reasoning,
        }
        self.log_event(agent, "self_assessment", data)

    def log_convergence_decision(
        self,
        agent: str,
        decision: str,
        confidence_threshold_met: bool,
        iteration_limit_check: bool,
        final_confidence: float,
    ) -> None:
        """Log a convergence decision event."""
        data = {
            "decision": decision,
            "confidence_threshold_met": confidence_threshold_met,
            "iteration_limit_check": iteration_limit_check,
            "final_confidence": final_confidence,
        }
        self.log_event(agent, "convergence_decision", data)

    def log_analysis_submitted(
        self,
        agent: str,
        total_iterations: int,
        comprehensive_report: str,
        confidence_score: float,
    ) -> None:
        """Log analysis submission event."""
        data = {
            "total_iterations": total_iterations,
            "comprehensive_report": comprehensive_report,
            "confidence_score": confidence_score,
        }
        self.log_event(agent, "analysis_submitted", data)

    def log_review_start(
        self,
        agent: str,
        review_number: int,
        report_length: int,
        review_criteria: list[str],
    ) -> None:
        """Log the start of a specialist review."""
        data = {
            "review_number": review_number,
            "report_length": report_length,
            "review_criteria": review_criteria,
        }
        self.log_event(agent, "review_start", data)

    def log_review_complete(
        self,
        agent: str,
        review_number: int,
        is_complete: bool,
        missing_areas: list[str],
        feedback_provided: str,
    ) -> None:
        """Log the completion of a specialist review."""
        data = {
            "review_number": review_number,
            "is_complete": is_complete,
            "missing_areas": missing_areas,
            "feedback_provided": feedback_provided,
        }
        self.log_event(agent, "review_complete", data)

    def log_strategy_adjustment(
        self,
        agent: str,
        previous_strategy: str,
        new_strategy: str,
        reason: str,
        feedback_triggers: list[str],
    ) -> None:
        """Log a strategy adjustment based on feedback."""
        data = {
            "previous_strategy": previous_strategy,
            "new_strategy": new_strategy,
            "reason": reason,
            "feedback_triggers": feedback_triggers,
        }
        self.log_event(agent, "strategy_adjustment", data)

    def log_error_with_context(
        self,
        agent: str,
        error_type: str,
        error_message: str,
        context: dict[str, Any],
        recovery_suggestions: list[str],
    ) -> None:
        """Log an error with full context and recovery suggestions."""
        data = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "recovery_suggestions": recovery_suggestions,
        }
        self.log_event(agent, "error_occurred", data)

        # Also log to standard logger
        self.logger.error(f"{agent}: {error_type} - {error_message}")
        for suggestion in recovery_suggestions:
            self.logger.info(f"Recovery suggestion: {suggestion}")

    def end_session(self, final_response: str) -> str:
        """End the current session and save logs."""
        if self.current_session is None:
            raise ValueError("No active session to end.")

        # Calculate execution time
        if self.session_start_time:
            execution_time = time.time() - self.session_start_time
            self.current_session["execution_stats"].execution_time = execution_time

        # Set final response
        self.current_session["final_response"] = final_response

        # Convert dataclass to dict for JSON serialization
        stats_dict = asdict(self.current_session["execution_stats"])
        self.current_session["execution_stats"] = stats_dict

        # Save session logs to file
        session_id = self.current_session["session_id"]
        timestamp = self.current_session["timestamp"].replace(":", "-")
        log_filename = f"{timestamp}_{session_id}.json"
        log_file = self.conversations_dir / log_filename

        try:
            with open(log_file, "w") as f:
                json.dump(self.current_session, f, indent=2)

            self.logger.info(f"Session {session_id} completed and saved to {log_file}")

            # Log summary statistics
            stats = self.current_session["execution_stats"]
            self.logger.info(
                f"Session summary - Analyzer iterations: {stats['total_analyzer_iterations']}, "
                f"Specialist reviews: {stats['total_specialist_reviews']}, "
                f"Commands executed: {stats['total_commands_executed']}, "
                f"Execution time: {stats['execution_time']:.2f}s"
            )

        except Exception as e:
            self.logger.error(f"Failed to save session logs: {e}")

        session_id_to_return = session_id
        self.current_session = None
        self.step_counter = 0
        self.session_start_time = None

        return session_id_to_return


# Global logger instance
_structured_logger: StructuredLogger | None = None


def get_structured_logger(logs_dir: str = "logs") -> StructuredLogger:
    """Get or create the global structured logger instance."""
    global _structured_logger
    if _structured_logger is None:
        _structured_logger = StructuredLogger(logs_dir)
    return _structured_logger


def setup_logging(
    log_level: str = "INFO", logs_dir: str = "logs", console_level: str = "ERROR"
) -> None:
    """Set up enhanced logging configuration.

    Args:
        log_level: Log level for file output (default: INFO)
        logs_dir: Directory for log files (default: logs)
        console_level: Log level for console output (default: ERROR)
    """
    # Convert string levels to logging constants
    file_numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    console_numeric_level = getattr(logging, console_level.upper(), logging.ERROR)

    # Initialize structured logger (this will set up standard logging too)
    get_structured_logger(logs_dir)

    # Update log levels for existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Root logger should capture everything

    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setLevel(file_numeric_level)
        elif isinstance(handler, logging.StreamHandler):
            handler.setLevel(console_numeric_level)

    logging.info(
        f"Enhanced logging initialized - File: {log_level}, Console: {console_level}"
    )
