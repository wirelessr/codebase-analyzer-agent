"""
Integration tests for Agent Manager.

TESTING SCENARIO: NEW FEATURE IMPLEMENTATION PLANNING
Tests the real interaction between AgentManager and actual agent implementations 
with real LLM calls focused on planning and implementing new features.
This includes:
- Feature requirement analysis and planning
- Implementation strategy development
- Integration point identification
- Database schema changes planning
- API design and endpoint planning
- Security consideration for new features
"""
import pytest
import tempfile
from pathlib import Path

from src.codebase_agent.agents.manager import AgentManager
from src.codebase_agent.config.configuration import ConfigurationManager


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
        """Create a temporary codebase for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a realistic Python project structure
            project_path = Path(temp_dir)
            
            # Create main.py
            (project_path / "main.py").write_text("""
def main():
    print("Hello, World!")
    user = authenticate_user("test", "password")
    if user:
        print(f"Welcome, {user.username}!")

def authenticate_user(username, password):
    # TODO: Implement proper authentication
    return None

if __name__ == "__main__":
    main()
""")
            
            # Create a simple models.py
            (project_path / "models.py").write_text("""
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
        self.is_active = True
    
    def save(self):
        # TODO: Implement database save
        pass
""")
            
            # Create requirements.txt
            (project_path / "requirements.txt").write_text("flask==2.0.1\nrequests==2.25.1\n")
            
            # Create a simple README
            (project_path / "README.md").write_text("""
# Simple Web App

This is a basic web application with user authentication.

## Features
- User management
- Basic authentication (not implemented yet)

## TODO
- Implement OAuth authentication
- Add user roles and permissions
""")
            
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
    
    def test_end_to_end_analysis_with_real_llm(self, config_manager_real, temp_codebase):
        """Test complete feature planning flow with real LLM calls."""
        print("🚀 Starting end-to-end feature planning with real LLM...")
        print(f"📁 Test codebase: {temp_codebase}")
        
        # Create and initialize manager with real agents
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()
        
        # Execute real feature planning analysis
        query = "I want to add OAuth 2.0 authentication to this Flask application. Plan the complete implementation including security considerations, database changes, and integration points."
        print(f"🔍 Feature Planning Query: {query}")
        
        result = manager.process_query_with_review_cycle(query, temp_codebase)
        
        print(f"📊 Feature planning completed!")
        print(f"📋 Result length: {len(result)} chars")
        print(f"📄 Result preview: {result[:300]}...")
        
        # Verify that we got a real feature planning response
        assert len(result) > 100, f"Expected substantial feature planning result, got {len(result)} chars"
        assert "oauth" in result.lower() or "authentication" in result.lower()
        
        # Verify structure of response for feature planning
        assert "# Codebase Analysis Results" in result
        assert "## Task:" in result
        assert "## Analysis:" in result
        
        # Check for feature planning specific content
        planning_terms = ['implementation', 'integration', 'security', 'database', 'plan', 'step']
        result_lower = result.lower()
        found_planning_terms = [term for term in planning_terms if term in result_lower]
        assert len(found_planning_terms) >= 3, f"Expected feature planning terms, found: {found_planning_terms}"
    
    def test_review_cycle_with_real_llm(self, config_manager_real, temp_codebase):
        """Test that review cycles work for complex feature implementation planning."""
        print("🔄 Testing review cycle for feature implementation planning...")
        
        # Create manager
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()
        
        # Use a complex feature that requires detailed planning and multiple review cycles
        query = "Add a comprehensive user profile management system with avatar upload, preferences storage, and role-based permissions. Include database schema design and API endpoints."
        print(f"🔍 Complex Feature Query: {query}")
        
        result = manager.process_query_with_review_cycle(query, temp_codebase)
        
        print(f"📊 Feature implementation planning completed!")
        print(f"📋 Result length: {len(result)} chars")
        print(f"🔍 Contains review info: {'Specialist Review' in result or 'Note:' in result}")
        
        # Verify comprehensive feature planning response
        assert len(result) > 200
        
        # Check for feature implementation planning terms
        implementation_terms = ['database', 'schema', 'api', 'endpoint', 'upload', 'permission', 'role', 'profile']
        result_lower = result.lower()
        found_terms = [term for term in implementation_terms if term in result_lower]
        assert len(found_terms) >= 4, f"Expected feature implementation terms, found: {found_terms}"
    
    def test_initialization_with_real_config(self, config_manager_real):
        """Test that manager can initialize with real configuration."""
        print("⚙️ Testing initialization with real config...")
        
        manager = AgentManager(config_manager_real)
        
        # Should not raise exceptions
        manager.initialize_agents()
        
        # Verify agents were created
        assert manager.code_analyzer is not None
        assert manager.task_specialist is not None
        assert manager.get_agent('code_analyzer') is not None
        assert manager.get_agent('task_specialist') is not None
        
        print("✅ Initialization successful!")
    
    def test_agent_coordination_behavior(self, config_manager_real, temp_codebase):
        """Test that agents coordinate effectively for feature implementation planning."""
        print("🤝 Testing agent coordination for feature planning...")
        
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()
        
        # Use a feature planning query that requires coordination between analysis and task specialists
        query = "I need to add email notification functionality to this app. Analyze current structure and plan the implementation including email service integration and notification templates."
        print(f"🔍 Feature Coordination Query: {query}")
        
        result = manager.process_query_with_review_cycle(query, temp_codebase)
        
        print(f"📊 Agent coordination test completed!")
        print(f"📋 Result length: {len(result)} chars")
        
        # Should have analyzed the existing structure and planned new feature
        assert len(result) > 50
        
        # Should mention existing files and feature planning elements
        assert any(filename in result for filename in ["main.py", "models.py", "README.md"])
        
        # Should have the manager's response structure
        assert "# Codebase Analysis Results" in result
        
        # Should contain feature planning elements
        feature_terms = ['email', 'notification', 'service', 'template', 'integration', 'implementation']
        result_lower = result.lower()
        found_feature_terms = [term for term in feature_terms if term in result_lower]
        assert len(found_feature_terms) >= 2, f"Expected feature planning coordination, found: {found_feature_terms}"
