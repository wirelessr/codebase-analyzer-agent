"""
Integration test for Code Analyzer Milestone Summary LLM Integration.

TESTING SCENARIO: MILESTONE SUMMARY EFFECTIVENESS
This test specifically validates the milestone summary prompt effectiveness
and LLM integration for progressive knowledge synthesis across iterations.

Tests the following milestone summary behaviors:
- Milestone summary prompt quality and comprehensiveness
- Complete history access for comprehensive analysis
- Knowledge synthesis across multiple iterations
- Technical insight preservation and evolution
- Milestone interval calculation and triggering
- Integration with shared knowledge base mechanism
"""

import os
import tempfile

import pytest

from codebase_agent.agents.code_analyzer import CodeAnalyzer


class TestCodeAnalyzerMilestoneIntegration:
    """Integration tests for milestone summary LLM effectiveness."""

    @pytest.fixture
    def shell_tool(self, milestone_test_codebase):
        """Create a real shell tool for testing milestone functionality."""
        from codebase_agent.tools.shell_tool import ShellTool

        return ShellTool(milestone_test_codebase)

    @pytest.fixture
    def config(self):
        """Create real LLM configuration for testing."""
        try:
            from codebase_agent.config.configuration import ConfigurationManager

            config_manager = ConfigurationManager()
            config_manager.load_environment()
            return config_manager.get_model_client()
        except Exception as e:
            pytest.skip(f"Could not configure LLM for milestone testing: {e}")

    @pytest.fixture
    def analyzer(self, config, shell_tool):
        """Create a real CodeAnalyzer instance with LLM integration."""
        return CodeAnalyzer(config, shell_tool)

    @pytest.fixture
    def milestone_test_codebase(self):
        """Create a multi-component codebase for testing milestone summaries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a realistic project structure with multiple components
            dirs = [
                "src/core",
                "src/api",
                "src/database",
                "src/utils",
                "tests",
                "config",
                "docs",
            ]
            for dir_path in dirs:
                os.makedirs(os.path.join(temp_dir, dir_path))

            # Core business logic
            with open(os.path.join(temp_dir, "src/core/user_service.py"), "w") as f:
                f.write(
                    """
class UserService:
    \"\"\"Core user business logic with authentication and authorization.\"\"\"

    def __init__(self, db_manager, auth_provider):
        self.db = db_manager
        self.auth = auth_provider
        self._user_cache = {}

    async def create_user(self, user_data):
        \"\"\"Create new user with validation and security checks.\"\"\"
        if not self._validate_user_data(user_data):
            raise ValueError("Invalid user data")

        # Hash password with salt
        password_hash = self.auth.hash_password(user_data['password'])
        user_data['password'] = password_hash

        # Store in database
        user_id = await self.db.insert_user(user_data)

        # Cache user data
        self._user_cache[user_id] = user_data

        return user_id

    def _validate_user_data(self, data):
        required_fields = ['username', 'email', 'password']
        return all(field in data for field in required_fields)
"""
                )

            # API layer
            with open(os.path.join(temp_dir, "src/api/auth_controller.py"), "w") as f:
                f.write(
                    """
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

class AuthController:
    \"\"\"REST API controller for authentication endpoints.\"\"\"

    def __init__(self, user_service, jwt_manager):
        self.user_service = user_service
        self.jwt = jwt_manager
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        self.router.post("/login")(self.login)
        self.router.post("/register")(self.register)
        self.router.post("/refresh")(self.refresh_token)

    async def login(self, credentials: dict):
        \"\"\"Authenticate user and return JWT token.\"\"\"
        user = await self.user_service.authenticate(
            credentials['username'],
            credentials['password']
        )

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = self.jwt.create_access_token(user['id'])
        return {"access_token": token, "token_type": "bearer"}

    async def register(self, user_data: dict):
        \"\"\"Register new user account.\"\"\"
        try:
            user_id = await self.user_service.create_user(user_data)
            return {"user_id": user_id, "status": "created"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
"""
                )

            # Database layer
            with open(os.path.join(temp_dir, "src/database/models.py"), "w") as f:
                f.write(
                    """
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    \"\"\"User database model with relationships and constraints.\"\"\"
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    profile_data = Column(Text, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Session(Base):
    \"\"\"User session tracking for security and analytics.\"\"\"
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
"""
                )

            # Configuration
            with open(os.path.join(temp_dir, "config/settings.py"), "w") as f:
                f.write(
                    """
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    \"\"\"Application configuration with environment variable support.\"\"\"

    # Database configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Authentication settings
    jwt_secret_key: str = os.getenv("JWT_SECRET", "your-secret-key")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Security settings
    password_min_length: int = 8
    max_login_attempts: int = 5
    session_timeout_minutes: int = 30

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    class Config:
        env_file = ".env"
"""
                )

            # Main application file
            with open(os.path.join(temp_dir, "main.py"), "w") as f:
                f.write(
                    """
from fastapi import FastAPI
from src.api.auth_controller import AuthController
from src.core.user_service import UserService
from src.database.models import Base
from config.settings import Settings

app = FastAPI(
    title="User Authentication Service",
    description="Secure user authentication and management API",
    version="1.0.0"
)

settings = Settings()

@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize application components and database.\"\"\"
    # Initialize database
    # Initialize services
    # Setup middleware
    pass

@app.get("/health")
async def health_check():
    \"\"\"Health check endpoint for monitoring.\"\"\"
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
"""
                )

            yield temp_dir

    def test_milestone_summary_prompt_effectiveness(
        self, analyzer, milestone_test_codebase
    ):
        """Test that milestone summary prompts produce comprehensive technical insights."""

        # Capture milestone summary prompts and responses
        milestone_calls = []
        original_generate_milestone = analyzer._generate_milestone_summary

        def capture_milestone_summary(*args, **kwargs):
            # Capture the prompt by mocking the agent run call
            original_agent_run = analyzer._agent.run

            async def capture_agent_run(task):
                milestone_calls.append({"prompt": task, "args": args, "kwargs": kwargs})
                # Call original method to get real LLM response
                return await original_agent_run(task)

            analyzer._agent.run = capture_agent_run
            result = original_generate_milestone(*args, **kwargs)
            analyzer._agent.run = original_agent_run

            return result

        analyzer._generate_milestone_summary = capture_milestone_summary

        # Run analysis that should trigger milestone summaries
        query = "Analyze the architecture and identify security considerations in this authentication service"
        analysis_result = analyzer.analyze_codebase(query, milestone_test_codebase)

        # Verify milestone summaries were generated
        assert (
            len(milestone_calls) >= 1
        ), f"Expected at least one milestone summary, got {len(milestone_calls)}"

        # Analyze first milestone summary prompt
        milestone_prompt = milestone_calls[0]["prompt"]

        # Verify prompt contains milestone-specific formatting
        assert "MILESTONE SUMMARY" in milestone_prompt
        assert "comprehensive milestone summary" in milestone_prompt.lower()

        # Verify prompt includes technical analysis requirements
        technical_requirements = [
            "Key Technical Discoveries",
            "Architectural Patterns",
            "Important Files/Components",
            "Relationships & Dependencies",
            "Configuration & Setup",
        ]

        for requirement in technical_requirements:
            assert (
                requirement in milestone_prompt
            ), f"Milestone prompt should include '{requirement}'"

        # Verify prompt includes complete history context
        assert "Original Query:" in milestone_prompt
        assert "SHELL EXECUTION HISTORY" in milestone_prompt
        assert "ANALYSIS INSIGHTS" in milestone_prompt

        # Verify analysis completed successfully
        assert "CODEBASE ANALYSIS COMPLETE" in analysis_result
        assert len(analysis_result) > 200  # Should be substantial analysis

    def test_milestone_summary_complete_history_access(
        self, analyzer, milestone_test_codebase
    ):
        """Test that milestone summaries have access to complete analysis history."""

        # Track all shell executions and analysis context
        shell_history_tracker = []
        milestone_history_access = []

        # Capture shell execution history
        original_execute_commands = analyzer._execute_shell_commands

        def track_shell_execution(commands):
            result = original_execute_commands(commands)
            shell_history_tracker.extend(commands)
            return result

        analyzer._execute_shell_commands = track_shell_execution

        # Capture milestone summary history access
        original_generate_milestone = analyzer._generate_milestone_summary

        def track_milestone_history(
            query,
            shell_history,
            analysis_context,
            current_iteration,
            milestone_interval,
        ):
            milestone_history_access.append(
                {
                    "iteration": current_iteration,
                    "shell_history_count": len(shell_history),
                    "analysis_context_count": len(analysis_context),
                    "shell_commands_total": sum(
                        len(sh.get("results", [])) for sh in shell_history
                    ),
                }
            )
            return original_generate_milestone(
                query,
                shell_history,
                analysis_context,
                current_iteration,
                milestone_interval,
            )

        analyzer._generate_milestone_summary = track_milestone_history

        # Run comprehensive analysis
        query = "Perform detailed analysis of this authentication service including security, architecture, and code quality"
        analyzer.analyze_codebase(query, milestone_test_codebase)

        # Verify milestone had access to complete history
        if milestone_history_access:
            history_access = milestone_history_access[0]

            # Should have access to multiple iterations of history
            assert (
                history_access["analysis_context_count"] >= 3
            ), f"Milestone should have access to multiple analysis iterations, got {history_access['analysis_context_count']}"

            # Should have access to multiple shell executions
            assert (
                history_access["shell_commands_total"] >= 3
            ), f"Milestone should have access to multiple shell commands, got {history_access['shell_commands_total']}"

            # Should occur at expected iteration (5 or 10 with max_iterations=10)
            assert history_access["iteration"] in [
                5,
                10,
            ], f"Milestone should occur at iteration 5 or 10, got {history_access['iteration']}"

    def test_milestone_summary_knowledge_synthesis(
        self, analyzer, milestone_test_codebase
    ):
        """Test that milestone summaries effectively synthesize knowledge across iterations."""

        # Capture milestone summaries and compare with individual iteration findings
        milestone_summaries = []
        iteration_findings = []

        # Track individual iteration key findings
        original_build_prompt = analyzer._build_iteration_prompt

        def track_iteration_findings(
            query,
            codebase_path,
            iteration,
            context,
            shell_history,
            shared_key_findings,
            convergence,
            specialist_feedback=None,
        ):
            if context:
                latest_context = context[-1]
                if (
                    "llm_decision" in latest_context
                    and "key_findings" in latest_context["llm_decision"]
                ):
                    iteration_findings.extend(
                        latest_context["llm_decision"]["key_findings"]
                    )

            return original_build_prompt(
                query,
                codebase_path,
                iteration,
                context,
                shell_history,
                shared_key_findings,
                convergence,
                specialist_feedback,
            )

        analyzer._build_iteration_prompt = track_iteration_findings

        # Capture milestone summaries
        original_generate_milestone = analyzer._generate_milestone_summary

        def capture_milestone_summaries(*args, **kwargs):
            summary = original_generate_milestone(*args, **kwargs)
            milestone_summaries.append(summary)
            return summary

        analyzer._generate_milestone_summary = capture_milestone_summaries

        # Run analysis
        query = "Analyze the authentication service for security vulnerabilities, architectural patterns, and code quality issues"
        analyzer.analyze_codebase(query, milestone_test_codebase)

        # Verify milestone summaries were generated
        assert (
            len(milestone_summaries) >= 1
        ), "Should generate at least one milestone summary"

        # Analyze synthesis quality
        for milestone_summary in milestone_summaries:
            # Should be substantial summary (not just fallback)
            assert (
                len(milestone_summary) > 50
            ), "Milestone summary should be substantial"

            # Should contain synthesized technical insights
            technical_keywords = [
                "authentication",
                "security",
                "database",
                "api",
                "service",
                "architecture",
            ]
            found_keywords = [
                kw
                for kw in technical_keywords
                if kw.lower() in milestone_summary.lower()
            ]
            assert (
                len(found_keywords) >= 3
            ), f"Milestone should synthesize technical insights, found keywords: {found_keywords}"

            # Should not be just a simple concatenation
            assert (
                "iterations" in milestone_summary.lower()
                or "analysis" in milestone_summary.lower()
            ), "Milestone should reference the analysis process"

    def test_milestone_integration_with_shared_knowledge_base(
        self, analyzer, milestone_test_codebase
    ):
        """Test that milestone summaries properly integrate with shared knowledge base."""

        # Track shared knowledge base evolution
        kb_evolution = []

        # Track knowledge base changes
        original_build_prompt = analyzer._build_iteration_prompt

        def track_kb_evolution(
            query,
            codebase_path,
            iteration,
            context,
            shell_history,
            shared_key_findings,
            convergence,
            specialist_feedback=None,
        ):
            kb_evolution.append(
                {
                    "iteration": iteration,
                    "kb_size": len(shared_key_findings),
                    "findings": shared_key_findings.copy(),
                }
            )
            return original_build_prompt(
                query,
                codebase_path,
                iteration,
                context,
                shell_history,
                shared_key_findings,
                convergence,
                specialist_feedback,
            )

        analyzer._build_iteration_prompt = track_kb_evolution

        # Run analysis
        query = "Comprehensive analysis of authentication service focusing on security and architecture"
        analyzer.analyze_codebase(query, milestone_test_codebase)

        # Analyze knowledge base evolution around milestone iterations
        if len(kb_evolution) >= 5:  # Ensure we have enough data
            # Find milestone iterations (should be at iteration 5 and/or 10)
            milestone_iterations = []
            for i, kb_state in enumerate(kb_evolution):
                if (
                    kb_state["iteration"] % 5 == 0
                ):  # milestone_interval = max_iterations // 2 = 5
                    milestone_iterations.append(i)

            if milestone_iterations:
                # Check if milestone summaries were added to knowledge base
                milestone_idx = milestone_iterations[0]

                if milestone_idx + 1 < len(kb_evolution):
                    pre_milestone_kb = kb_evolution[milestone_idx]["findings"]
                    post_milestone_kb = kb_evolution[milestone_idx + 1]["findings"]

                    # Knowledge base should have grown after milestone
                    assert len(post_milestone_kb) > len(
                        pre_milestone_kb
                    ), "Knowledge base should grow after milestone summary"

                    # Should contain milestone-specific content
                    new_findings = [
                        f for f in post_milestone_kb if f not in pre_milestone_kb
                    ]
                    milestone_findings = [
                        f for f in new_findings if "MILESTONE" in f.upper()
                    ]

                    assert (
                        len(milestone_findings) > 0
                    ), "Should add milestone summary to shared knowledge base"


if __name__ == "__main__":
    print("Milestone Summary Integration Tests")
    print("==================================")
    print(
        "These tests validate milestone summary LLM integration and prompt effectiveness:"
    )
    print("- Milestone summary prompt comprehensiveness")
    print("- Complete history access during summarization")
    print("- Knowledge synthesis across multiple iterations")
    print("- Integration with shared knowledge base mechanism")
    print()
    print(
        "Run with: pytest tests/integration/test_code_analyzer_milestone_integration.py -v"
    )
