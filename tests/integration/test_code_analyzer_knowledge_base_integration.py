"""
Integration test for Code Analyzer LLM Knowledge Base Sharing Behavior.

TESTING SCENARIO: DATA FLOW ANALYSIS
This test specifically validates the LLM's ability to analyze data flow
patterns and information processing paths across the system using a 
shared knowledge base across multiple analysis iterations.

Tests the following data flow analysis behaviors:
- Data transformation and processing pipeline understanding
- Information flow between system components
- Data persistence and storage patterns
- API request/response data handling
- Cross-layer data exchange mechanisms
- Knowledge accumulation for complex data flow mapping
"""

import pytest
import tempfile
import os
import json
import re
from unittest.mock import Mock, patch
from codebase_agent.agents.code_analyzer import CodeAnalyzer


class TestCodeAnalyzerKnowledgeBaseSharing:
    """Tests for LLM Knowledge Base sharing and collaborative learning behavior."""

    @pytest.fixture
    def shell_tool(self, complex_test_codebase):
        """Create a real shell tool for testing with complex codebase."""
        from codebase_agent.tools.shell_tool import ShellTool
        return ShellTool(complex_test_codebase)

    @pytest.fixture
    def config(self):
        """Create real LLM configuration for testing."""
        try:
            from codebase_agent.config.configuration import ConfigurationManager
            config_manager = ConfigurationManager()
            config_manager.load_environment()
            return config_manager.get_model_client()
        except Exception as e:
            pytest.skip(f"Could not configure LLM for knowledge base testing: {e}")

    @pytest.fixture
    def analyzer(self, config, shell_tool):
        """Create a real CodeAnalyzer instance with LLM integration."""
        return CodeAnalyzer(config, shell_tool)

    @pytest.fixture
    def complex_test_codebase(self):
        """Create a more complex codebase for testing knowledge accumulation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a complex Python project structure
            project_dirs = [
                "src/models", "src/services", "src/utils", "src/api",
                "tests/unit", "tests/integration", "docs", "config"
            ]
            for dir_path in project_dirs:
                os.makedirs(os.path.join(temp_dir, dir_path))
            
            # Create model files
            with open(os.path.join(temp_dir, "src/models/user.py"), "w") as f:
                f.write("""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    \"\"\"User model with validation and business logic.\"\"\"
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True
    profile_data: Optional[dict] = None
    
    def validate_email(self) -> bool:
        \"\"\"Validate email format using regex.\"\"\"
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, self.email))
    
    def activate(self):
        \"\"\"Activate user account.\"\"\"
        self.is_active = True
    
    def deactivate(self):
        \"\"\"Deactivate user account.\"\"\"
        self.is_active = False
""")

            # Create service files
            with open(os.path.join(temp_dir, "src/services/user_service.py"), "w") as f:
                f.write("""
from typing import List, Optional
from src.models.user import User
from src.utils.database import DatabaseConnection
from src.utils.logger import Logger

class UserService:
    \"\"\"Service layer for user operations with business logic.\"\"\"
    
    def __init__(self, db_connection: DatabaseConnection, logger: Logger):
        self.db = db_connection
        self.logger = logger
    
    async def create_user(self, username: str, email: str) -> User:
        \"\"\"Create a new user with validation.\"\"\"
        # Business logic: check if username exists
        existing_user = await self.get_user_by_username(username)
        if existing_user:
            raise ValueError(f"Username {username} already exists")
        
        # Create user
        user = User(
            id=await self.db.get_next_id(),
            username=username,
            email=email,
            created_at=datetime.now()
        )
        
        # Validate
        if not user.validate_email():
            raise ValueError("Invalid email format")
        
        # Save to database
        await self.db.save_user(user)
        self.logger.info(f"Created user: {username}")
        
        return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        \"\"\"Retrieve user by username.\"\"\"
        return await self.db.find_user_by_username(username)
    
    async def list_active_users(self) -> List[User]:
        \"\"\"Get all active users.\"\"\"
        users = await self.db.get_all_users()
        return [user for user in users if user.is_active]
""")

            # Create API files
            with open(os.path.join(temp_dir, "src/api/user_controller.py"), "w") as f:
                f.write("""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from src.services.user_service import UserService
from src.utils.dependencies import get_user_service

router = APIRouter(prefix="/api/users", tags=["users"])

class CreateUserRequest(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

@router.post("/", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    \"\"\"Create a new user endpoint.\"\"\"
    try:
        user = await user_service.create_user(request.username, request.email)
        return UserResponse(
            id=user.id,
            username=user.username, 
            email=user.email,
            is_active=user.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[UserResponse])
async def list_users(user_service: UserService = Depends(get_user_service)):
    \"\"\"List all active users.\"\"\"
    users = await user_service.list_active_users()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email, 
            is_active=user.is_active
        ) for user in users
    ]
""")

            # Create utility files
            with open(os.path.join(temp_dir, "src/utils/database.py"), "w") as f:
                f.write("""
import asyncpg
from typing import List, Optional
from src.models.user import User

class DatabaseConnection:
    \"\"\"Database connection and operations.\"\"\"
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def connect(self):
        \"\"\"Establish database connection pool.\"\"\"
        self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def get_next_id(self) -> int:
        \"\"\"Get next available user ID.\"\"\"
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT MAX(id) FROM users")
            return (result or 0) + 1
    
    async def save_user(self, user: User) -> None:
        \"\"\"Save user to database.\"\"\"
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (id, username, email, created_at, is_active) VALUES ($1, $2, $3, $4, $5)",
                user.id, user.username, user.email, user.created_at, user.is_active
            )
""")

            # Create configuration files
            with open(os.path.join(temp_dir, "config/settings.py"), "w") as f:
                f.write("""
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    \"\"\"Application settings with environment variables.\"\"\"
    
    # Database settings
    database_url: str = "postgresql://localhost/testdb"
    database_pool_size: int = 10
    
    # API settings  
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug_mode: bool = False
    
    # Security settings
    secret_key: str
    jwt_expiration_hours: int = 24
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
""")

            # Create test files
            with open(os.path.join(temp_dir, "tests/unit/test_user_model.py"), "w") as f:
                f.write("""
import pytest
from datetime import datetime
from src.models.user import User

class TestUserModel:
    \"\"\"Unit tests for User model.\"\"\"
    
    def test_user_creation(self):
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            created_at=datetime.now()
        )
        assert user.id == 1
        assert user.username == "testuser"
        assert user.is_active is True
    
    def test_email_validation_valid(self):
        user = User(1, "test", "valid@email.com", datetime.now())
        assert user.validate_email() is True
    
    def test_email_validation_invalid(self):
        user = User(1, "test", "invalid-email", datetime.now())
        assert user.validate_email() is False
    
    def test_user_activation(self):
        user = User(1, "test", "test@example.com", datetime.now())
        user.deactivate()
        assert user.is_active is False
        user.activate()
        assert user.is_active is True
""")

            # Create README and documentation
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write("""
# User Management System

A comprehensive user management system built with FastAPI and PostgreSQL.

## Architecture

This project follows a layered architecture pattern:

### Layers
- **API Layer** (`src/api/`): FastAPI controllers and request/response models
- **Service Layer** (`src/services/`): Business logic and operations
- **Model Layer** (`src/models/`): Data models and validation
- **Utils Layer** (`src/utils/`): Shared utilities and infrastructure

### Key Components

#### User Model (`src/models/user.py`)
- Core user data structure with validation
- Email validation using regex patterns
- User activation/deactivation methods

#### User Service (`src/services/user_service.py`)
- Business logic for user operations
- Handles user creation with validation
- Manages user queries and updates

#### User API (`src/api/user_controller.py`)
- RESTful endpoints for user management
- Request/response validation with Pydantic
- Error handling and HTTP status codes

#### Database Layer (`src/utils/database.py`)
- Async PostgreSQL connection management
- Connection pooling for performance
- Database operation abstraction

#### Configuration (`config/settings.py`)
- Environment-based configuration
- Settings for database, API, security, and logging
- Type-safe configuration with Pydantic

## Features

- ✅ User registration with email validation
- ✅ User authentication and authorization
- ✅ Account activation/deactivation
- ✅ RESTful API with OpenAPI documentation
- ✅ Async database operations
- ✅ Comprehensive test coverage
- ✅ Environment-based configuration

## Design Patterns

- **Dependency Injection**: Service dependencies injected via FastAPI
- **Repository Pattern**: Database operations abstracted
- **Validation**: Input validation at API and model levels
- **Async/Await**: Non-blocking I/O operations
- **Configuration Management**: Centralized settings
""")

            # Create requirements file
            with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
                f.write("""
fastapi==0.104.1
pydantic==2.5.0
asyncpg==0.29.0
uvicorn==0.24.0
pytest==7.4.3
pytest-asyncio==0.21.1
""")

            yield temp_dir

    def test_knowledge_base_accumulation_across_iterations(self, analyzer, complex_test_codebase):
        """Test data flow analysis with knowledge accumulation across multiple iterations."""
        
        # Use a query focused on data flow analysis
        query = "分析這個用戶管理系統的資料流設計：從API請求到資料庫操作的完整數據傳遞路徑、資料轉換過程、以及各層之間的資料交互模式"
        
        # Patch the LLM agent to capture intermediate responses
        captured_iterations = []
        original_extract_response = analyzer._extract_response_text
        
        def capture_iteration_response(step_response):
            response_text = original_extract_response(step_response)
            captured_iterations.append(response_text)
            return response_text
        
        with patch.object(analyzer, '_extract_response_text', side_effect=capture_iteration_response):
            result = analyzer.analyze_codebase(query, complex_test_codebase)
        
        # Validate that we captured multiple iterations
        assert len(captured_iterations) >= 2, f"Expected multiple iterations, got {len(captured_iterations)}"
        
        # Extract knowledge bases from each iteration
        knowledge_bases = []
        for iteration_text in captured_iterations:
            try:
                # Extract JSON from the response
                json_text = analyzer._extract_json_from_response(iteration_text)
                iteration_data = json.loads(json_text)
                if 'key_findings' in iteration_data:
                    knowledge_bases.append(iteration_data['key_findings'])
            except (json.JSONDecodeError, KeyError):
                # Skip invalid JSON responses
                continue
        
        # Validate knowledge accumulation
        assert len(knowledge_bases) >= 2, "Should have captured knowledge bases from multiple iterations"
        
        # Check that knowledge base grows over iterations
        first_kb = knowledge_bases[0] if knowledge_bases else []
        last_kb = knowledge_bases[-1] if knowledge_bases else []
        
        # Knowledge base should either grow or become more refined
        assert len(last_kb) >= len(first_kb), "Knowledge base should accumulate or refine findings"
        
        # Final result should contain comprehensive data flow analysis
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert len(result) > 500  # Should be substantial data flow analysis
        
        # Check for data flow related content
        data_flow_terms = ['data', 'flow', 'api', 'database', 'request', 'response', 'transformation', '資料', '數據', '流程']
        result_lower = result.lower()
        found_terms = [term for term in data_flow_terms if term in result_lower]
        assert len(found_terms) >= 3, f"Expected data flow analysis terms, found: {found_terms}"

    def test_knowledge_base_refinement_and_updates(self, analyzer, complex_test_codebase):
        """Test data flow knowledge refinement and updates across iterations."""
        
        query = "分析這個專案的資料庫操作模式和資料持久化策略，包括連接管理、事務處理、資料存取層設計"
        
        # Capture all LLM responses to track knowledge refinement
        all_responses = []
        original_extract_response = analyzer._extract_response_text
        
        def capture_iteration_response(step_response):
            response_text = original_extract_response(step_response)
            all_responses.append(response_text)
            return response_text
        
        with patch.object(analyzer, '_extract_response_text', side_effect=capture_iteration_response):
            result = analyzer.analyze_codebase(query, complex_test_codebase)
        
        # Extract key findings from responses
        findings_evolution = []
        for response in all_responses:
            try:
                json_text = analyzer._extract_json_from_response(response)
                data = json.loads(json_text)
                if 'key_findings' in data:
                    findings_evolution.append(data['key_findings'])
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Validate refinement occurred
        if len(findings_evolution) >= 2:
            first_findings = findings_evolution[0]
            later_findings = findings_evolution[-1]
            
            # Check for evidence of data flow analysis refinement
            # Either findings become more specific, or new data flow findings are added
            database_related_count_first = sum(
                1 for finding in first_findings 
                if any(keyword in finding.lower() for keyword in ['database', 'connection', 'async', 'pool', 'transaction', 'data', 'persistence'])
            )
            
            database_related_count_later = sum(
                1 for finding in later_findings
                if any(keyword in finding.lower() for keyword in ['database', 'connection', 'async', 'pool', 'transaction', 'data', 'persistence'])
            )
            
            # Should have more data flow related findings as analysis progresses
            assert database_related_count_later >= database_related_count_first, \
                "Should accumulate more data flow related findings over iterations"
        
        # Final analysis should be comprehensive data flow analysis
        assert "CODEBASE ANALYSIS COMPLETE" in result
        # Should contain data flow related analysis
        assert any(keyword in result.lower() for keyword in ['database', 'postgresql', 'async', 'connection', 'transaction', 'data', 'persistence'])

    def test_knowledge_base_persistence_and_continuity(self, analyzer, complex_test_codebase):
        """Test that knowledge base maintains continuity and doesn't lose important findings."""
        
        query = "評估這個專案的代碼品質和架構設計模式"
        
        # Track knowledge base across iterations to ensure persistence
        kb_timeline = []
        
        # Mock the iteration prompt building to capture knowledge base usage
        original_build_prompt = analyzer._build_iteration_prompt
        
        def track_kb_usage(query, codebase_path, iteration, context, shell_history, shared_key_findings, convergence, specialist_feedback=None):
            kb_timeline.append({
                'iteration': iteration,
                'kb_size': len(shared_key_findings),
                'findings': shared_key_findings.copy()
            })
            return original_build_prompt(query, codebase_path, iteration, context, shell_history, shared_key_findings, convergence, specialist_feedback)
        
        with patch.object(analyzer, '_build_iteration_prompt', side_effect=track_kb_usage):
            result = analyzer.analyze_codebase(query, complex_test_codebase)
        
        # Validate knowledge base persistence
        if len(kb_timeline) >= 2:
            # Check that knowledge base grows or maintains size over iterations
            initial_kb_size = kb_timeline[0]['kb_size']
            final_kb_size = kb_timeline[-1]['kb_size']
            
            # Knowledge base should grow or at least maintain some findings
            assert final_kb_size >= initial_kb_size, \
                f"Knowledge base should grow or maintain size (initial: {initial_kb_size}, final: {final_kb_size})"
            
            # Check for evidence of knowledge evolution
            non_empty_kbs = [entry for entry in kb_timeline if entry['kb_size'] > 0]
            assert len(non_empty_kbs) > 0, "Should have at least some iterations with knowledge base content"
            
            # If we have knowledge, it should be relevant to the query
            if final_kb_size > 0:
                final_findings = kb_timeline[-1]['findings']
                quality_keywords = ['quality', 'pattern', 'design', 'architecture', 'code', '品質', '設計', '架構', '模式']
                
                relevant_findings = sum(
                    1 for finding in final_findings
                    if any(keyword in finding.lower() for keyword in quality_keywords)
                )
                
                # At least some findings should be relevant to the query
                assert relevant_findings > 0 or final_kb_size == 0, \
                    "Final knowledge base should contain query-relevant findings"
        
        # Final result should be comprehensive
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert len(result) > 400

    def test_knowledge_base_convergence_quality(self, analyzer, complex_test_codebase):
        """Test that knowledge base converges to high-quality, comprehensive findings."""
        
        query = "完整分析這個FastAPI專案的架構層次和依賴注入設計"
        
        result = analyzer.analyze_codebase(query, complex_test_codebase)
        
        # Extract final knowledge base if available in result
        # (The final result might contain the synthesized knowledge)
        assert "CODEBASE ANALYSIS COMPLETE" in result
        
        # Check for comprehensive coverage of the requested analysis
        architecture_keywords = [
            'layer', 'api', 'service', 'model', 'controller', 
            'fastapi', 'dependency', 'injection', 'pattern',
            '層', '架構', '依賴', '注入', '設計'
        ]
        
        found_keywords = [keyword for keyword in architecture_keywords 
                         if keyword in result.lower()]
        
        # Should cover multiple architectural concepts
        assert len(found_keywords) >= 3, f"Analysis should cover architectural concepts, found: {found_keywords}"
        
        # Should be substantial and detailed
        assert len(result) > 600, "Final analysis should be comprehensive"
        
        # Should indicate analysis completion
        assert "Iterations:" in result or "complete" in result.lower()

    def test_knowledge_base_multilingual_handling(self, analyzer, complex_test_codebase):
        """Test that knowledge base works correctly with Chinese queries and findings."""
        
        query = "分析這個專案使用了哪些設計模式，以及它們如何改善代碼的可維護性"
        
        result = analyzer.analyze_codebase(query, complex_test_codebase)
        
        # Should handle Chinese query and produce meaningful analysis
        assert "CODEBASE ANALYSIS COMPLETE" in result
        
        # Should contain analysis relevant to design patterns and maintainability
        relevant_keywords = [
            'pattern', 'design', 'maintain', 'architecture', 'service',
            '設計', '模式', '維護', '架構', '服務', '可維護性'
        ]
        
        found_relevant = [keyword for keyword in relevant_keywords 
                         if keyword in result.lower()]
        
        assert len(found_relevant) >= 2, f"Should contain relevant analysis, found: {found_relevant}"
        
        # Should be comprehensive
        assert len(result) > 300


# Manual test runner for development
if __name__ == "__main__":
    # Allow manual testing during development
    print("Code Analyzer Knowledge Base Sharing Integration Tests")
    print("These tests validate LLM knowledge base behavior across iterations")
    pytest.main([__file__, "-v", "-s"])
