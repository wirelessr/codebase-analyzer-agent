"""
Integration tests for Agent Manager.

TESTING SCENARIO: NEW FEATURE IMPLEMENTATION PLANNING (Go Language)
Tests the real interaction between AgentManager and actual agent implementations
with real LLM calls focused on planning and implementing new features for Go web APIs.
This includes:
-        result, statistics = manager.process_query_with_review_cycle(query, temp_codebase)

        print("📊 Feature planning completed!")
        print(f"📋 Result length: {len(result)} chars")
        print(f"📄 Result preview: {result[:300]}...")
        print(f"🔢 Statistics: {statistics}")

        # Verify that we got a real feature planning response
        assert (
            len(result) > 100
        ), f"Expected substantial feature planning result, got {len(result)} chars"
        assert (
            "jwt" in result.lower()
            or "authentication" in result.lower()
            or "middleware" in result.lower()
        )
        # Verify statistics are returned
        assert isinstance(statistics, dict)
        assert "total_review_cycles" in statisticsature requirement analysis and planning
- Go microservice implementation strategy development
- Database integration point identification for Go applications
- Go database schema and migration planning
- Go REST API design and endpoint planning
- Security considerations for Go web services and concurrent programming
"""

import tempfile
from pathlib import Path

import pytest

from codebase_agent.agents.manager import AgentManager
from codebase_agent.config.configuration import ConfigurationManager


class TestAgentManagerIntegration:
    """Integration test cases for AgentManager with real LLM calls."""

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
    def temp_codebase(self):
        """Create a temporary Go web API codebase for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a realistic Go web API project structure
            project_path = Path(temp_dir)

            # Create go.mod
            (project_path / "go.mod").write_text(
                """module user-api

go 1.19

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.7
    github.com/golang-jwt/jwt/v4 v4.4.3
)
"""
            )

            # Create main.go
            (project_path / "main.go").write_text(
                """package main

import (
    "log"
    "user-api/internal/handlers"
    "user-api/internal/database"

    "github.com/gin-gonic/gin"
)

func main() {
    // Initialize database
    db, err := database.Connect()
    if err != nil {
        log.Fatal("Failed to connect to database:", err)
    }
    defer db.Close()

    // Initialize Gin router
    r := gin.Default()

    // Setup routes
    api := r.Group("/api/v1")
    {
        api.POST("/auth/login", handlers.Login)
        api.POST("/auth/register", handlers.Register)
        // TODO: Add JWT middleware for protected routes
        api.GET("/users", handlers.GetUsers)
        api.POST("/users", handlers.CreateUser)
    }

    log.Println("Server starting on :8080")
    r.Run(":8080")
}
"""
            )

            # Create internal directory structure
            internal_path = project_path / "internal"
            internal_path.mkdir()

            # Create models.go
            (internal_path / "models.go").write_text(
                """package internal

import (
    "time"
)

type User struct {
    ID       int       `json:"id" db:"id"`
    Username string    `json:"username" db:"username"`
    Email    string    `json:"email" db:"email"`
    Password string    `json:"-" db:"password_hash"`
    IsActive bool      `json:"is_active" db:"is_active"`
    Created  time.Time `json:"created_at" db:"created_at"`
}

type LoginRequest struct {
    Username string `json:"username" binding:"required"`
    Password string `json:"password" binding:"required"`
}

type RegisterRequest struct {
    Username string `json:"username" binding:"required"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8"`
}
"""
            )

            # Create handlers directory
            handlers_path = internal_path / "handlers"
            handlers_path.mkdir()

            # Create auth handlers
            (handlers_path / "auth.go").write_text(
                """package handlers

import (
    "net/http"

    "github.com/gin-gonic/gin"
)

func Login(c *gin.Context) {
    // TODO: Implement JWT authentication
    c.JSON(http.StatusNotImplemented, gin.H{
        "error": "Login not implemented yet",
    })
}

func Register(c *gin.Context) {
    // TODO: Implement user registration with password hashing
    c.JSON(http.StatusNotImplemented, gin.H{
        "error": "Registration not implemented yet",
    })
}
"""
            )

            # Create user handlers
            (handlers_path / "users.go").write_text(
                """package handlers

import (
    "net/http"

    "github.com/gin-gonic/gin"
)

func GetUsers(c *gin.Context) {
    // TODO: Implement user listing with pagination
    c.JSON(http.StatusNotImplemented, gin.H{
        "error": "User listing not implemented yet",
    })
}

func CreateUser(c *gin.Context) {
    // TODO: Implement user creation
    c.JSON(http.StatusNotImplemented, gin.H{
        "error": "User creation not implemented yet",
    })
}
"""
            )

            # Create database package
            db_path = internal_path / "database"
            db_path.mkdir()

            (db_path / "connection.go").write_text(
                """package database

import (
    "database/sql"
    "os"

    _ "github.com/lib/pq"
)

func Connect() (*sql.DB, error) {
    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        dbURL = "postgres://user:password@localhost/userdb?sslmode=disable"
    }

    db, err := sql.Open("postgres", dbURL)
    if err != nil {
        return nil, err
    }

    // Test the connection
    if err := db.Ping(); err != nil {
        return nil, err
    }

    return db, nil
}
"""
            )

            # Create README
            (project_path / "README.md").write_text(
                """# Go User API

A RESTful API for user management built with Go and Gin framework.

## Features
- User registration and authentication
- JWT-based authentication (planned)
- PostgreSQL database integration
- RESTful API endpoints

## Current API Endpoints
- POST /api/v1/auth/login - User login
- POST /api/v1/auth/register - User registration
- GET /api/v1/users - List users
- POST /api/v1/users - Create user

## TODO Features
- Implement JWT authentication middleware
- Add password hashing with bcrypt
- Implement user roles and permissions
- Add input validation and sanitization
- Add rate limiting
- Add logging and monitoring
- Implement user profile management
- Add email verification
- Add password reset functionality

## Database Schema
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
"""
            )

            yield str(project_path)

    @pytest.fixture
    def config_manager_real(self):
        """Create a real configuration manager."""
        try:
            config_manager = ConfigurationManager()
            config_manager.load_environment()
            return config_manager
        except Exception as e:
            pytest.skip(f"Could not configure LLM: {e}")

    def test_end_to_end_analysis_with_real_llm(
        self, config_manager_real, temp_codebase
    ):
        """Test complete feature planning flow with real LLM calls."""
        print("🚀 Starting end-to-end feature planning with real LLM...")
        print(f"📁 Test codebase: {temp_codebase}")

        # Create and initialize manager with real agents
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()

        # Execute real feature planning analysis
        query = "I want to add JWT-based authentication and user role management to this Go API. Plan the complete implementation including security considerations, database schema changes, middleware design, and API endpoint modifications."
        print(f"🔍 Feature Planning Query: {query}")

        result = manager.process_query_with_review_cycle(query, temp_codebase)

        print("📊 Feature planning completed!")
        print(f"📋 Result length: {len(result)} chars")
        print(f"📄 Result preview: {result[:300]}...")

        # Verify that we got a real feature planning response
        assert (
            len(result) > 100
        ), f"Expected substantial feature planning result, got {len(result)} chars"
        assert (
            "jwt" in result.lower()
            or "authentication" in result.lower()
            or "middleware" in result.lower()
        )

        # Verify structure of response for feature planning
        assert "# Codebase Analysis Results" in result
        assert "## Task:" in result
        assert "## Analysis:" in result

        # Check for feature planning specific content
        planning_terms = [
            "implementation",
            "integration",
            "security",
            "database",
            "plan",
            "step",
        ]
        result_lower = result.lower()
        found_planning_terms = [term for term in planning_terms if term in result_lower]
        assert (
            len(found_planning_terms) >= 3
        ), f"Expected feature planning terms, found: {found_planning_terms}"

    def test_review_cycle_with_real_llm(self, config_manager_real, temp_codebase):
        """Test that review cycles work for complex feature implementation planning."""
        print("🔄 Testing review cycle for feature implementation planning...")

        # Create manager
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()

        # Use a complex feature that requires detailed planning and multiple review cycles
        query = "Add a comprehensive user profile management system with avatar upload, user preferences storage, and role-based access control (RBAC) to this Go API. Include database schema design, file upload handling with Go, middleware for authorization, and RESTful API endpoints."
        print(f"🔍 Complex Feature Query: {query}")

        result, statistics = manager.process_query_with_review_cycle(
            query, temp_codebase
        )

        print("📊 Feature implementation planning completed!")
        print(f"📋 Result length: {len(result)} chars")
        print(
            f"🔍 Contains review info: {'Specialist Review' in result or 'Note:' in result}"
        )
        print(f"🔢 Statistics: {statistics}")

        # Verify comprehensive feature planning response
        assert len(result) > 200

        # Check for feature implementation planning terms
        implementation_terms = [
            "database",
            "schema",
            "api",
            "endpoint",
            "upload",
            "middleware",
            "rbac",
            "authorization",
            "profile",
            "gin",
        ]
        result_lower = result.lower()
        found_terms = [term for term in implementation_terms if term in result_lower]
        assert (
            len(found_terms) >= 4
        ), f"Expected feature implementation terms, found: {found_terms}"

        # Verify statistics are returned
        assert isinstance(statistics, dict)
        assert "total_review_cycles" in statistics

    def test_initialization_with_real_config(self, config_manager_real):
        """Test that manager can initialize with real configuration."""
        print("⚙️ Testing initialization with real config...")

        manager = AgentManager(config_manager_real)

        # Should not raise exceptions
        manager.initialize_agents()

        # Verify agents were created
        assert manager.code_analyzer is not None
        assert manager.task_specialist is not None
        assert manager.get_agent("code_analyzer") is not None
        assert manager.get_agent("task_specialist") is not None

        print("✅ Initialization successful!")

    def test_agent_coordination_behavior(self, config_manager_real, temp_codebase):
        """Test that agents coordinate effectively for feature implementation planning."""
        print("🤝 Testing agent coordination for feature planning...")

        manager = AgentManager(config_manager_real)
        manager.initialize_agents()

        # Use a feature planning query that requires coordination between analysis and task specialists
        query = "I need to add email notification functionality to this Go API. Analyze current structure and plan the implementation including SMTP service integration, notification templates with Go's template package, and asynchronous job processing for email sending."
        print(f"🔍 Feature Coordination Query: {query}")

        result = manager.process_query_with_review_cycle(query, temp_codebase)

        print("📊 Agent coordination test completed!")
        print(f"📋 Result length: {len(result)} chars")

        # Should have analyzed the existing structure and planned new feature
        assert len(result) > 50

        # Should mention existing files and feature planning elements
        assert any(
            filename in result
            for filename in ["main.go", "go.mod", "README.md", "handlers", "models.go"]
        )

        # Should have the manager's response structure
        assert "# Codebase Analysis Results" in result

        # Should contain feature planning elements
        feature_terms = [
            "email",
            "notification",
            "smtp",
            "template",
            "goroutine",
            "integration",
            "implementation",
            "async",
        ]
        result_lower = result.lower()
        found_feature_terms = [term for term in feature_terms if term in result_lower]
        assert (
            len(found_feature_terms) >= 2
        ), f"Expected feature planning coordination, found: {found_feature_terms}"
