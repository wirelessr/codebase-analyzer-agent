"""
Unit tests for the structured logging and monitoring system.
"""

import json
import logging
import os
import tempfile
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import pytest

from codebase_agent.utils.logging import (
    LogEvent,
    LogParser,
    SessionLogs,
    SessionStats,
    StructuredLogger,
    get_structured_logger,
    setup_logging
)


class TestLogEvent(TestCase):
    """Test LogEvent dataclass."""
    
    def test_log_event_creation(self):
        """Test creating a LogEvent instance."""
        event = LogEvent(
            step_id=1,
            timestamp="2024-08-26T10:30:00Z",
            agent="code_analyzer",
            event_type="iteration_start",
            data={"iteration_number": 1}
        )
        
        self.assertEqual(event.step_id, 1)
        self.assertEqual(event.agent, "code_analyzer")
        self.assertEqual(event.event_type, "iteration_start")
        self.assertEqual(event.data["iteration_number"], 1)


class TestSessionStats(TestCase):
    """Test SessionStats dataclass."""
    
    def test_session_stats_defaults(self):
        """Test SessionStats default values."""
        stats = SessionStats()
        
        self.assertEqual(stats.total_analyzer_iterations, 0)
        self.assertEqual(stats.total_specialist_reviews, 0)
        self.assertEqual(stats.total_commands_executed, 0)
        self.assertEqual(stats.execution_time, 0.0)
    
    def test_session_stats_with_values(self):
        """Test SessionStats with specific values."""
        stats = SessionStats(
            total_analyzer_iterations=3,
            total_specialist_reviews=2,
            total_commands_executed=15,
            execution_time=45.2
        )
        
        self.assertEqual(stats.total_analyzer_iterations, 3)
        self.assertEqual(stats.total_specialist_reviews, 2)
        self.assertEqual(stats.total_commands_executed, 15)
        self.assertEqual(stats.execution_time, 45.2)


class TestSessionLogs(TestCase):
    """Test SessionLogs container class."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_log_data = {
            "session_id": "test123",
            "timestamp": "2024-08-26T10:30:00Z",
            "codebase_path": "/test/path",
            "user_query": "test query",
            "agents_involved": ["code_analyzer", "task_specialist"],
            "execution_timeline": [
                {
                    "step_id": 1,
                    "timestamp": "2024-08-26T10:30:15Z",
                    "agent": "code_analyzer",
                    "event_type": "iteration_start",
                    "data": {"iteration_number": 1}
                },
                {
                    "step_id": 2,
                    "timestamp": "2024-08-26T10:30:20Z",
                    "agent": "code_analyzer",
                    "event_type": "command_executed",
                    "data": {"command": "find . -name '*.py'"}
                },
                {
                    "step_id": 3,
                    "timestamp": "2024-08-26T10:30:25Z",
                    "agent": "code_analyzer",
                    "event_type": "knowledge_update",
                    "data": {"new_findings": ["User model exists"], "confidence_level": 0.6}
                },
                {
                    "step_id": 4,
                    "timestamp": "2024-08-26T10:30:30Z",
                    "agent": "task_specialist",
                    "event_type": "review_complete",
                    "data": {"review_number": 1, "is_complete": True}
                }
            ],
            "final_response": "Test response",
            "execution_stats": {
                "total_analyzer_iterations": 1,
                "total_specialist_reviews": 1,
                "total_commands_executed": 1,
                "execution_time": 30.0
            }
        }
        self.session_logs = SessionLogs(self.sample_log_data)
    
    def test_session_logs_initialization(self):
        """Test SessionLogs initialization from dict."""
        self.assertEqual(self.session_logs.session_id, "test123")
        self.assertEqual(self.session_logs.codebase_path, "/test/path")
        self.assertEqual(self.session_logs.user_query, "test query")
        self.assertEqual(len(self.session_logs.timeline), 4)
        self.assertEqual(self.session_logs.stats.total_analyzer_iterations, 1)
    
    def test_filter_by_event_type(self):
        """Test filtering events by event type."""
        iteration_events = self.session_logs.filter_by_event_type("iteration_start")
        self.assertEqual(len(iteration_events), 1)
        self.assertEqual(iteration_events[0].event_type, "iteration_start")
        
        command_events = self.session_logs.filter_by_event_type("command_executed")
        self.assertEqual(len(command_events), 1)
        self.assertEqual(command_events[0].data["command"], "find . -name '*.py'")
    
    def test_filter_by_agent(self):
        """Test filtering events by agent."""
        analyzer_events = self.session_logs.filter_by_agent("code_analyzer")
        self.assertEqual(len(analyzer_events), 3)
        
        specialist_events = self.session_logs.filter_by_agent("task_specialist")
        self.assertEqual(len(specialist_events), 1)
        self.assertEqual(specialist_events[0].event_type, "review_complete")
    
    def test_filter_after_timestamp(self):
        """Test filtering events after a specific timestamp."""
        filtered_logs = self.session_logs.filter_after_timestamp("2024-08-26T10:30:22Z")
        self.assertEqual(len(filtered_logs.timeline), 2)  # Only last 2 events
        self.assertEqual(filtered_logs.timeline[0].event_type, "knowledge_update")
    
    def test_get_knowledge_before_timestamp(self):
        """Test extracting knowledge before a timestamp."""
        knowledge = self.session_logs.get_knowledge_before_timestamp("2024-08-26T10:30:27Z")
        self.assertEqual(knowledge, "User model exists")
        
        # Test with timestamp before any knowledge updates
        early_knowledge = self.session_logs.get_knowledge_before_timestamp("2024-08-26T10:30:10Z")
        self.assertEqual(early_knowledge, "")
    
    def test_get_final_knowledge(self):
        """Test extracting final accumulated knowledge."""
        knowledge = self.session_logs.get_final_knowledge()
        self.assertEqual(knowledge, "User model exists")
    
    def test_empty_knowledge_handling(self):
        """Test handling of sessions with no knowledge updates."""
        log_data_no_knowledge = {
            "session_id": "test456",
            "execution_timeline": [
                {
                    "step_id": 1,
                    "timestamp": "2024-08-26T10:30:15Z",
                    "agent": "code_analyzer",
                    "event_type": "iteration_start",
                    "data": {"iteration_number": 1}
                }
            ],
            "execution_stats": {}
        }
        
        session_logs = SessionLogs(log_data_no_knowledge)
        knowledge = session_logs.get_final_knowledge()
        self.assertEqual(knowledge, "")


class TestLogParser(TestCase):
    """Test LogParser utility class."""
    
    def setUp(self):
        """Set up test data and temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.temp_dir) / "conversations"
        self.logs_dir.mkdir(parents=True)
        
        # Create sample log file
        self.session_id = "test789"
        self.sample_log = {
            "session_id": self.session_id,
            "timestamp": "2024-08-26T10:30:00Z",
            "execution_timeline": [
                {
                    "step_id": 1,
                    "timestamp": "2024-08-26T10:30:15Z",
                    "agent": "code_analyzer",
                    "event_type": "iteration_start",
                    "data": {"iteration_number": 1}
                },
                {
                    "step_id": 2,
                    "timestamp": "2024-08-26T10:30:20Z",
                    "agent": "code_analyzer",
                    "event_type": "knowledge_update",
                    "data": {"new_findings": ["Found auth module"], "confidence_level": 0.7}
                }
            ],
            "execution_stats": {"total_analyzer_iterations": 1}
        }
        
        log_file = self.logs_dir / f"2024-08-26T10-30-00_{self.session_id}.json"
        with open(log_file, 'w') as f:
            json.dump(self.sample_log, f)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_session_logs_success(self):
        """Test successful retrieval of session logs."""
        session_logs = LogParser.get_session_logs(self.session_id, self.logs_dir)
        
        self.assertIsNotNone(session_logs)
        self.assertEqual(session_logs.session_id, self.session_id)
        self.assertEqual(len(session_logs.timeline), 2)
    
    def test_get_session_logs_not_found(self):
        """Test behavior when session logs are not found."""
        session_logs = LogParser.get_session_logs("nonexistent", self.logs_dir)
        self.assertIsNone(session_logs)
    
    def test_filter_by_event_type_static(self):
        """Test static method for filtering by event type."""
        session_logs = LogParser.get_session_logs(self.session_id, self.logs_dir)
        events = LogParser.filter_by_event_type(session_logs, "knowledge_update")
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "knowledge_update")
    
    def test_get_state_at_step(self):
        """Test reconstructing agent state at a specific step."""
        session_logs = LogParser.get_session_logs(self.session_id, self.logs_dir)
        state = LogParser.get_state_at_step(session_logs, 2)
        
        self.assertEqual(state["current_iteration"], 1)
        self.assertEqual(state["accumulated_knowledge"], ["Found auth module"])
        self.assertEqual(state["confidence_level"], 0.7)
    
    def test_get_state_at_early_step(self):
        """Test state reconstruction at an early step."""
        session_logs = LogParser.get_session_logs(self.session_id, self.logs_dir)
        state = LogParser.get_state_at_step(session_logs, 1)
        
        self.assertEqual(state["current_iteration"], 1)
        self.assertEqual(state["accumulated_knowledge"], [])
        self.assertEqual(state["confidence_level"], 0.0)


class TestStructuredLogger(TestCase):
    """Test StructuredLogger class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = StructuredLogger(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test logger initialization."""
        self.assertTrue(self.logger.conversations_dir.exists())
        self.assertIsNone(self.logger.current_session)
        self.assertEqual(self.logger.step_counter, 0)
    
    def test_start_session(self):
        """Test starting a new session."""
        session_id = self.logger.start_session(
            "test query",
            "/test/path",
            ["code_analyzer"]
        )
        
        self.assertIsNotNone(session_id)
        self.assertIsNotNone(self.logger.current_session)
        self.assertEqual(self.logger.current_session["user_query"], "test query")
        self.assertEqual(self.logger.step_counter, 0)
        self.assertIsNotNone(self.logger.session_start_time)
    
    def test_log_event_without_session(self):
        """Test logging event without active session raises error."""
        with self.assertRaises(ValueError):
            self.logger.log_event("test_agent", "test_event", {})
    
    def test_log_event_with_session(self):
        """Test logging event with active session."""
        self.logger.start_session("test", "/test", ["agent"])
        self.logger.log_event("test_agent", "test_event", {"key": "value"})
        
        self.assertEqual(self.logger.step_counter, 1)
        self.assertEqual(len(self.logger.current_session["execution_timeline"]), 1)
        
        event = self.logger.current_session["execution_timeline"][0]
        self.assertEqual(event["agent"], "test_agent")
        self.assertEqual(event["event_type"], "test_event")
        self.assertEqual(event["data"]["key"], "value")
    
    def test_log_analysis_cycle_start(self):
        """Test logging analysis cycle start."""
        self.logger.start_session("test", "/test", ["agent"])
        self.logger.log_analysis_cycle_start(
            "code_analyzer", 1, ["existing knowledge"], ["find . -name '*.py'"]
        )
        
        event = self.logger.current_session["execution_timeline"][0]
        self.assertEqual(event["event_type"], "iteration_start")
        self.assertEqual(event["data"]["iteration_number"], 1)
        self.assertEqual(event["data"]["current_knowledge"], ["existing knowledge"])
    
    def test_log_command_executed(self):
        """Test logging command execution."""
        self.logger.start_session("test", "/test", ["agent"])
        self.logger.log_command_executed(
            "code_analyzer", "find . -name '*.py'", 0, 1024, ["file1.py", "file2.py"]
        )
        
        event = self.logger.current_session["execution_timeline"][0]
        self.assertEqual(event["event_type"], "command_executed")
        self.assertEqual(event["data"]["command"], "find . -name '*.py'")
        self.assertEqual(event["data"]["exit_code"], 0)
        self.assertEqual(event["data"]["files_found"], ["file1.py", "file2.py"])
        
        # Check statistics update
        stats = self.logger.current_session["execution_stats"]
        self.assertEqual(stats.total_commands_executed, 1)
    
    def test_log_knowledge_update(self):
        """Test logging knowledge update."""
        self.logger.start_session("test", "/test", ["agent"])
        self.logger.log_knowledge_update(
            "code_analyzer", ["new finding"], 0.8, ["next area"]
        )
        
        event = self.logger.current_session["execution_timeline"][0]
        self.assertEqual(event["event_type"], "knowledge_update")
        self.assertEqual(event["data"]["new_findings"], ["new finding"])
        self.assertEqual(event["data"]["confidence_level"], 0.8)
    
    def test_log_iteration_complete(self):
        """Test logging iteration completion."""
        self.logger.start_session("test", "/test", ["agent"])
        self.logger.log_iteration_complete(
            "code_analyzer", 2, 5, "need more info", True
        )
        
        event = self.logger.current_session["execution_timeline"][0]
        self.assertEqual(event["event_type"], "iteration_complete")
        self.assertEqual(event["data"]["iteration_number"], 2)
        self.assertEqual(event["data"]["continue_analysis"], True)
        
        # Check statistics update
        stats = self.logger.current_session["execution_stats"]
        self.assertEqual(stats.total_analyzer_iterations, 1)
    
    def test_log_review_complete(self):
        """Test logging review completion."""
        self.logger.start_session("test", "/test", ["agent"])
        self.logger.log_review_complete(
            "task_specialist", 1, False, ["missing area"], "need more details"
        )
        
        event = self.logger.current_session["execution_timeline"][0]
        self.assertEqual(event["event_type"], "review_complete")
        self.assertEqual(event["data"]["is_complete"], False)
        self.assertEqual(event["data"]["missing_areas"], ["missing area"])
        
        # Check statistics update
        stats = self.logger.current_session["execution_stats"]
        self.assertEqual(stats.total_specialist_reviews, 1)
    
    def test_log_error_with_context(self):
        """Test logging error with context."""
        self.logger.start_session("test", "/test", ["agent"])
        
        with patch.object(self.logger.logger, 'error') as mock_error:
            self.logger.log_error_with_context(
                "code_analyzer", "CommandError", "Command failed",
                {"command": "invalid_cmd"}, ["try different command"]
            )
            
            # Check structured event
            event = self.logger.current_session["execution_timeline"][0]
            self.assertEqual(event["event_type"], "error_occurred")
            self.assertEqual(event["data"]["error_type"], "CommandError")
            
            # Check standard logging call
            mock_error.assert_called_once()
    
    def test_end_session(self):
        """Test ending a session and saving logs."""
        session_id = self.logger.start_session("test", "/test", ["agent"])
        self.logger.log_event("test_agent", "test_event", {})
        
        # Add small delay to ensure execution time > 0
        time.sleep(0.01)
        
        returned_id = self.logger.end_session("final response")
        
        self.assertEqual(returned_id, session_id)
        self.assertIsNone(self.logger.current_session)
        self.assertEqual(self.logger.step_counter, 0)
        
        # Check file was created
        log_files = list(self.logger.conversations_dir.glob(f"*_{session_id}.json"))
        self.assertEqual(len(log_files), 1)
        
        # Verify file contents
        with open(log_files[0], 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["session_id"], session_id)
        self.assertEqual(saved_data["final_response"], "final response")
        self.assertGreater(saved_data["execution_stats"]["execution_time"], 0)
    
    def test_end_session_without_active_session(self):
        """Test ending session without active session raises error."""
        with self.assertRaises(ValueError):
            self.logger.end_session("response")


class TestGlobalLogger(TestCase):
    """Test global logger functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
        # Reset global logger
        import src.codebase_agent.utils.logging as logging_module
        logging_module._structured_logger = None
    
    def test_get_structured_logger(self):
        """Test getting global structured logger."""
        logger1 = get_structured_logger(self.temp_dir)
        logger2 = get_structured_logger(self.temp_dir)
        
        # Should return the same instance
        self.assertIs(logger1, logger2)
    
    @patch('logging.getLogger')
    def test_setup_logging(self, mock_get_logger):
        """Test setup_logging function."""
        mock_logger = mock_get_logger.return_value
        mock_logger.handlers = []
        
        setup_logging("DEBUG", self.temp_dir)
        
        # Should initialize structured logger
        logger = get_structured_logger()
        self.assertIsNotNone(logger)


class TestEdgeCases(TestCase):
    """Test edge cases and error conditions."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = StructuredLogger(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_multiple_knowledge_updates_final_knowledge(self):
        """Test final knowledge extraction with multiple updates."""
        log_data = {
            "session_id": "test",
            "execution_timeline": [
                {
                    "step_id": 1,
                    "timestamp": "2024-08-26T10:30:15Z",
                    "agent": "code_analyzer",
                    "event_type": "knowledge_update",
                    "data": {"new_findings": ["first finding"], "confidence_level": 0.3}
                },
                {
                    "step_id": 2,
                    "timestamp": "2024-08-26T10:30:25Z",
                    "agent": "code_analyzer",
                    "event_type": "knowledge_update",
                    "data": {"new_findings": ["second finding"], "confidence_level": 0.7}
                }
            ],
            "execution_stats": {}
        }
        
        session_logs = SessionLogs(log_data)
        final_knowledge = session_logs.get_final_knowledge()
        self.assertEqual(final_knowledge, "second finding")
    
    def test_log_parser_with_corrupted_json(self):
        """Test LogParser handling of corrupted JSON files."""
        logs_dir = Path(self.temp_dir) / "conversations"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create corrupted JSON file
        corrupted_file = logs_dir / "2024-08-26T10-30-00_corrupted123.json"
        with open(corrupted_file, 'w') as f:
            f.write("{invalid json")
        
        with patch('logging.error') as mock_error:
            result = LogParser.get_session_logs("corrupted123", logs_dir)
            self.assertIsNone(result)
            mock_error.assert_called()
    
    def test_session_logs_with_missing_fields(self):
        """Test SessionLogs initialization with missing optional fields."""
        minimal_data = {
            "session_id": "minimal123"
        }
        
        session_logs = SessionLogs(minimal_data)
        self.assertEqual(session_logs.session_id, "minimal123")
        self.assertEqual(session_logs.codebase_path, "")
        self.assertEqual(session_logs.user_query, "")
        self.assertEqual(session_logs.agents_involved, [])
        self.assertEqual(len(session_logs.timeline), 0)
        self.assertEqual(session_logs.final_response, "")


if __name__ == '__main__':
    pytest.main([__file__])
