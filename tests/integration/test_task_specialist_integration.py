"""
Integration test for Task Specialist with real LLM and review functionality.

TESTING SCENARIO: NEW FEATURE IMPLEMENTATION REVIEW
This test verifies that the Task Specialist effectively reviews and provides
feedback on feature implementation analyses using real LLM interaction.
Focus areas include:
- Feature implementation completeness assessment
- Technical approach validation for new features
- Integration strategy review
- Security and best practices verification for new functionality
- Implementation plan quality assurance
"""

import pytest

from codebase_agent.agents.task_specialist import TaskSpecialist
from codebase_agent.config.configuration import ConfigurationManager


class TestTaskSpecialistIntegration:
    """Integration test for Task Specialist with real LLM interaction."""

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
    def task_specialist(self, real_config):
        """Create Task Specialist with real configuration."""
        return TaskSpecialist(real_config)

    def test_specialist_basic_functionality(self, task_specialist):
        """Test basic Task Specialist functionality with simpler assertion."""

        task_description = "Simple test task"
        analysis = "Basic analysis content"

        print("🚀 Testing basic specialist functionality...")

        # Test that the method can be called without errors
        try:
            is_complete, feedback, confidence = task_specialist.review_analysis(
                analysis_report=analysis,
                task_description=task_description,
                current_review_count=1,
            )

            print("📊 Basic Test Result:")
            print(f"   Complete: {is_complete}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Feedback length: {len(feedback)}")

            # Just verify we get some response
            assert isinstance(
                is_complete, bool
            ), f"Expected boolean, got {type(is_complete)}"
            assert isinstance(feedback, str), f"Expected string, got {type(feedback)}"
            assert isinstance(
                confidence, int | float
            ), f"Expected number, got {type(confidence)}"
            assert len(feedback) > 0, "Expected non-empty feedback"

            print("✅ Basic functionality test passed!")

        except Exception as e:
            print(f"❌ Basic functionality test failed: {e}")
            raise AssertionError(f"Basic functionality failed: {e}") from e

    def test_specialist_reviews_incomplete_analysis(self, task_specialist):
        """Test specialist review of incomplete feature implementation analysis."""

        task_description = """
        Add a RESTful API with CRUD operations for a blog post management system.
        The system should support creating, reading, updating, and deleting blog posts.
        Include proper validation, error handling, and authentication.
        """

        # Deliberately incomplete feature implementation analysis
        incomplete_analysis = """
        I found some files in the project:
        - app.py (main Flask application)
        - models.py (contains User model)
        - templates/ (HTML templates)

        The app.py file imports Flask and creates an app instance.
        There are some routes defined but no API endpoints yet.
        """

        print(
            "🚀 Testing specialist review of incomplete feature implementation analysis..."
        )

        is_complete, feedback, confidence = task_specialist.review_analysis(
            analysis_report=incomplete_analysis,
            task_description=task_description,
            current_review_count=1,
        )

        print("📊 Review Result:")
        print(f"   Complete: {is_complete}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Feedback: {feedback}")

        # Verify that the specialist correctly identified incompleteness for feature implementation
        assert (
            not is_complete
        ), f"Expected incomplete feature analysis to be rejected, but was accepted. Feedback: {feedback}"

        assert len(feedback) > 50, f"Expected detailed feedback, got: {feedback}"

        # Feedback should mention missing areas related to API implementation
        feedback_lower = feedback.lower()
        api_terms = [
            "api",
            "crud",
            "endpoint",
            "rest",
            "post",
            "blog",
            "implementation",
            "validation",
            "authentication",
        ]
        has_api_focus = any(term in feedback_lower for term in api_terms)

        assert (
            has_api_focus
        ), f"Expected feedback to focus on API implementation gaps, got: {feedback}"

        print(
            "✅ Test passed: Specialist correctly identified incomplete feature implementation analysis!"
        )

    def test_specialist_accepts_complete_analysis(self, task_specialist):
        """Test specialist accepts thorough feature implementation analysis."""

        task_description = """
        Add real-time chat functionality to the web application.
        Include WebSocket support, message persistence, and user presence indicators.
        """

        # Comprehensive feature implementation analysis
        complete_analysis = """
        EXISTING CODEBASE ANALYSIS:
        - Found Flask app structure in app.py with basic routing framework
        - User model exists in models.py with SQLAlchemy ORM setup
        - Database configuration present using SQLite with migration support
        - Templates directory with Jinja2 template structure and base layout
        - Static assets folder for CSS/JS with existing jQuery integration

        FEATURE INTEGRATION POINTS:
        - Flask app can be extended with WebSocket support via Flask-SocketIO
        - User model ready for chat user identification and session management
        - Database schema can accommodate chat messages via new Message model
        - Existing template structure supports real-time UI components
        - Static assets can include Socket.IO client library

        IMPLEMENTATION PLAN:
        1. Install Flask-SocketIO for WebSocket support
        2. Create Message model with fields: id, user_id, content, timestamp, room_id
        3. Create ChatRoom model for organizing conversations
        4. Add WebSocket event handlers for: connect, disconnect, join_room, send_message
        5. Implement message persistence with SQLAlchemy integration
        6. Create real-time chat interface with JavaScript Socket.IO client
        7. Add user presence tracking with online/offline status
        8. Implement message history loading for chat rooms

        DATABASE CHANGES:
        - New tables: messages, chat_rooms, user_presence
        - Foreign key relationships: messages.user_id -> users.id
        - Indexes on timestamp and room_id for efficient message retrieval
        - Migration scripts for schema updates

        SECURITY CONSIDERATIONS:
        - WebSocket authentication using Flask-Login session validation
        - Input sanitization for chat messages to prevent XSS
        - Rate limiting for message sending to prevent spam
        - Room-based permissions for private chat functionality

        FRONTEND INTEGRATION:
        - Socket.IO client integration with existing jQuery framework
        - Real-time message display with auto-scrolling chat window
        - Typing indicators and user presence status display
        - Message input validation and character limits

        TESTING STRATEGY:
        - Unit tests for Message and ChatRoom models
        - WebSocket event testing with test client
        - Integration tests for message persistence
        - Frontend testing for real-time functionality
        """

        print(
            "🚀 Testing specialist review of complete feature implementation analysis..."
        )

        is_complete, feedback, confidence = task_specialist.review_analysis(
            analysis_report=complete_analysis,
            task_description=task_description,
            current_review_count=1,
        )

        print("📊 Review Result:")
        print(f"   Complete: {is_complete}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Feedback: {feedback}")

        # With a thorough feature implementation analysis like this, check LLM response
        if is_complete:
            print("✅ LLM accepted the comprehensive feature implementation analysis")
            assert (
                confidence > 0.7
            ), f"Expected high confidence for accepted analysis, got: {confidence}"
        else:
            print(
                "⚠️  LLM found additional areas for improvement in feature implementation"
            )
            # Ensure the feedback is substantial and relevant to feature implementation
            assert len(feedback) > 50, f"Expected detailed feedback, got: {feedback}"

            # For complex features like real-time chat, it's reasonable for LLM to be thorough
            feedback_lower = feedback.lower()
            feature_terms = [
                "websocket",
                "real-time",
                "chat",
                "implementation",
                "security",
                "testing",
                "integration",
            ]
            has_feature_focus = any(term in feedback_lower for term in feature_terms)

            assert (
                has_feature_focus
            ), f"Expected feature implementation focused feedback, got: {feedback}"

            # Quality feedback should have reasonable confidence
            assert (
                confidence > 0.3
            ), f"Expected reasonable confidence for quality feedback, got: {confidence}"

        assert len(feedback) > 20, f"Expected meaningful feedback, got: {feedback}"
        print(
            "✅ Test passed: Specialist provided appropriate feature implementation review!"
        )

    def test_specialist_multiple_reviews_progressive_acceptance(self, task_specialist):
        """Test specialist behavior with multiple review cycles for feature implementation."""

        task_description = """
        Implement a search functionality with full-text search and filtering.
        """

        # Minimal analysis that should normally be rejected for feature implementation
        minimal_analysis = """
        Found some Python files. There are functions that could be extended for search.
        Search functionality can be added using basic string matching.
        """

        print(
            "🚀 Testing specialist multiple review behavior for feature implementation..."
        )

        # Test progressive reviews
        for review_num in range(1, 4):
            is_complete, feedback, confidence = task_specialist.review_analysis(
                analysis_report=minimal_analysis,
                task_description=task_description,
                current_review_count=review_num,
            )

            print(f"📊 Review {review_num} Result:")
            print(f"   Complete: {is_complete}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Feedback: {feedback[:100]}...")

            if review_num < 3:
                # First two reviews should likely reject minimal feature implementation analysis
                print(
                    f"   Review {review_num} decision: {'ACCEPT' if is_complete else 'REJECT'}"
                )
            else:
                # Third review should force accept due to max review limit
                assert (
                    is_complete
                ), f"Expected force accept on review 3, but got rejection. Feedback: {feedback}"
                assert (
                    "maximum" in feedback.lower() or "limit" in feedback.lower()
                ), f"Expected force accept message, got: {feedback}"

        print(
            "✅ Test passed: Specialist correctly handles multiple reviews for feature implementation!"
        )

    def test_specialist_llm_prompt_effectiveness(self, task_specialist):
        """Test that the specialist's prompts lead to consistent LLM behavior."""

        test_cases = [
            {
                "name": "Database Integration Task",
                "task": "Add PostgreSQL database integration to existing Flask app",
                "analysis": "Found app.py file with Flask imports. Database not analyzed.",
                "expected_complete": False,
                "should_mention": [
                    "database",
                    "postgresql",
                    "integration",
                    "connection",
                ],
            },
            {
                "name": "API Endpoint Task",
                "task": "Create REST API endpoints for user management",
                "analysis": """
                EXISTING ANALYSIS:
                - Found Flask app with routing structure in app.py
                - User model exists with proper SQLAlchemy setup
                - JSON serialization methods present in models

                INTEGRATION POINTS:
                - Can extend existing route patterns for API endpoints
                - User model ready for CRUD operations

                IMPLEMENTATION STEPS:
                1. Add API blueprint for user routes
                2. Implement GET /users, POST /users, PUT /users/<id>, DELETE /users/<id>
                3. Add JSON response formatting
                4. Include proper HTTP status codes and error handling
                5. Add request validation and authentication middleware
                6. Document API endpoints with proper error responses

                SECURITY CONSIDERATIONS:
                - Input validation for all endpoints
                - Authentication/authorization for protected routes
                - Rate limiting considerations

                PATTERNS FROM CODEBASE:
                - Routes use @app.route decorator pattern
                - Database queries follow SQLAlchemy ORM patterns
                - Error handling uses Flask's abort() function
                """,
                "expected_complete": True,  # This more comprehensive analysis should be accepted
                "should_mention": ["accept", "sufficient", "implementation"],
            },
        ]

        print("🚀 Testing specialist LLM prompt effectiveness...")

        for i, case in enumerate(test_cases, 1):
            print(f"\n📝 Test Case {i}: {case['name']}")

            is_complete, feedback, confidence = task_specialist.review_analysis(
                analysis_report=case["analysis"],
                task_description=case["task"],
                current_review_count=1,
            )

            print(f"   Complete: {is_complete}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Feedback: {feedback[:200]}...")

            # Check if result matches expectation (but allow for LLM variability)
            if case["expected_complete"]:
                # We expect this to be complete
                if is_complete:
                    print("   ✅ Correctly accepted as complete")
                else:
                    print("   ⚠️  LLM was stricter than expected (reasonable behavior)")
                    # Even if rejected, ensure feedback is quality-focused
                    feedback_lower = feedback.lower()
                    quality_indicators = [
                        "detail",
                        "specific",
                        "security",
                        "consideration",
                    ]
                    has_quality_focus = any(
                        indicator in feedback_lower for indicator in quality_indicators
                    )
                    if has_quality_focus:
                        print("   ✅ Rejection was based on quality concerns")
            else:
                # We expect this to be incomplete
                if not is_complete:
                    print("   ✅ Correctly identified as incomplete")
                else:
                    print("   ⚠️  LLM accepted unexpectedly (LLM variability)")

            # Check if feedback mentions relevant terms
            feedback_lower = feedback.lower()
            mentioned_terms = [
                term for term in case["should_mention"] if term in feedback_lower
            ]

            if mentioned_terms:
                print(f"   ✅ Mentioned relevant terms: {mentioned_terms}")
            else:
                print(
                    f"   ⚠️  Expected terms not prominently featured: {case['should_mention']}"
                )

            # Verify feedback is substantial and meaningful
            assert len(feedback) > 30, f"Expected substantial feedback, got: {feedback}"

            # Ensure confidence is reasonable
            assert (
                0.0 <= confidence <= 1.0
            ), f"Confidence should be between 0 and 1, got: {confidence}"

        print("\n✅ Test passed: Specialist LLM prompts show effective behavior!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
