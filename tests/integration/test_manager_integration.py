"""
Integration tests for Agent Manager.

Tests the real interaction between AgentManager and actual agent implementations with real LLM calls.
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
        """Test complete analysis flow with real LLM calls."""
        print("🚀 Starting end-to-end analysis with real LLM...")
        print(f"📁 Test codebase: {temp_codebase}")
        
        # Create and initialize manager with real agents
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()
        
        # Execute real analysis
        query = "analyze the current authentication system and suggest how to implement OAuth"
        print(f"🔍 Query: {query}")
        
        result = manager.process_query_with_review_cycle(query, temp_codebase)
        
        print(f"📊 Analysis completed!")
        print(f"📋 Result length: {len(result)} chars")
        print(f"📄 Result preview: {result[:300]}...")
        
        # Verify that we got a real response
        assert len(result) > 100, f"Expected substantial analysis result, got {len(result)} chars"
        assert "authentication" in result.lower()
        
        # Verify structure of response
        assert "# Codebase Analysis Results" in result
        assert "## Task:" in result
        assert "## Analysis:" in result
    
    def test_review_cycle_with_real_llm(self, config_manager_real, temp_codebase):
        """Test that review cycles work with real LLM responses."""
        print("🔄 Testing review cycle with real LLM...")
        
        # Create manager
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()
        
        # Use a task that might require multiple review cycles
        query = "create a detailed implementation plan for adding JWT-based authentication to this Flask app"
        print(f"🔍 Query: {query}")
        
        result = manager.process_query_with_review_cycle(query, temp_codebase)
        
        print(f"📊 Review cycle completed!")
        print(f"📋 Result length: {len(result)} chars")
        print(f"🔍 Contains review info: {'Specialist Review' in result or 'Note:' in result}")
        
        # Verify comprehensive response
        assert len(result) > 200
        assert any(keyword in result.lower() for keyword in ["jwt", "token", "authentication", "implementation"])
    
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
        """Test that agents actually coordinate through the manager."""
        print("🤝 Testing agent coordination behavior...")
        
        manager = AgentManager(config_manager_real)
        manager.initialize_agents()
        
        # Use a simple query to focus on coordination behavior
        query = "what files are in this project and what do they do?"
        print(f"🔍 Simple query: {query}")
        
        result = manager.process_query_with_review_cycle(query, temp_codebase)
        
        print(f"📊 Coordination test completed!")
        print(f"📋 Result length: {len(result)} chars")
        
        # Should have analyzed the files we created
        assert len(result) > 50
        assert any(filename in result for filename in ["main.py", "models.py", "README.md"])
        
        # Should have the manager's response structure
        assert "# Codebase Analysis Results" in result
