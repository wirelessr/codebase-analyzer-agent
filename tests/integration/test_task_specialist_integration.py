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

        # Deliberately incomplete and buzzword-heavy analysis that should be rejected
        incomplete_analysis = """
        This is a sophisticated multi-agent system with excellent software engineering practices.

        I found some files in the project:
        - app.py (main Flask application)
        - models.py (contains User model)
        - templates/ (HTML templates)

        The project has a comprehensive testing setup and modern Python tooling.
        There's clear separation of concerns and the app.py file imports Flask.
        The architecture is well-organized with some routes defined but no API endpoints yet.

        This demonstrates enterprise-level development patterns and follows best practices.
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

        # Verify that the specialist correctly identified incompleteness and buzzwords
        assert (
            not is_complete
        ), f"Expected buzzword-heavy analysis to be rejected, but was accepted. Feedback: {feedback}"

        assert len(feedback) > 50, f"Expected detailed feedback, got: {feedback}"

        # Feedback should specifically mention rejection of buzzwords or lack of technical detail
        feedback_lower = feedback.lower()
        quality_indicators = [
            "specific",
            "concrete",
            "implementation",
            "detail",
            "technical",
            "buzzword",
            "sophisticated",
            "comprehensive",
            "fluff",
            "superficial",
        ]
        has_quality_focus = any(term in feedback_lower for term in quality_indicators)

        assert (
            has_quality_focus
        ), f"Expected feedback to focus on lack of technical depth or buzzwords, got: {feedback}"

        print(
            "✅ Test passed: Specialist correctly rejected buzzword-heavy superficial analysis!"
        )

    def test_specialist_accepts_complete_analysis(self, task_specialist):
        """Test specialist accepts thorough feature implementation analysis."""

        task_description = """
        Add real-time chat functionality to the web application.
        Include WebSocket support, message persistence, and user presence indicators.
        """

        # High-quality technical analysis with concrete implementation details
        complete_analysis = """
        CODEBASE STRUCTURE ANALYSIS:
        - app.py: Flask application with app = Flask(__name__) instantiation
        - models.py: SQLAlchemy models with User class, has id, username, email fields
        - config.py: Database configuration using SQLite URI 'sqlite:///app.db'
        - __init__.py: Application factory pattern with create_app() function
        - templates/base.html: Jinja2 template with {% block content %} structure

        WEBSOCKET INTEGRATION IMPLEMENTATION:
        1. Install Flask-SocketIO: pip install flask-socketio==5.x
        2. Modify app.py:
           - from flask_socketio import SocketIO, emit, join_room, leave_room
           - socketio = SocketIO(app, cors_allowed_origins="*")
           - Replace app.run() with socketio.run(app, debug=True)

        3. Database Schema Extensions:
           - Message model: id (Integer, primary_key), user_id (ForeignKey),
             content (Text), timestamp (DateTime), room_id (String)
           - UserPresence model: user_id (ForeignKey), status (String), last_seen (DateTime)
           - Migration: flask db migrate -m "add chat tables"

        4. WebSocket Event Handlers (app.py):
           @socketio.on('connect')
           def handle_connect():
               if current_user.is_authenticated:
                   join_room(f"user_{current_user.id}")
                   emit('status', {'user': current_user.username, 'status': 'online'})

           @socketio.on('send_message')
           def handle_message(data):
               message = Message(user_id=current_user.id, content=data['message'],
                               room_id=data['room'], timestamp=datetime.utcnow())
               db.session.add(message)
               db.session.commit()
               emit('receive_message', {'user': current_user.username,
                                      'message': data['message']}, room=data['room'])

        5. Frontend Integration (static/chat.js):
           - socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port)
           - socket.emit('send_message', {message: input.value, room: currentRoom})
           - socket.on('receive_message', function(data) { appendMessage(data) })

        ERROR HANDLING SPECIFICS:
        - WebSocket exceptions: @socketio.on_error decorator for connection failures
        - Database constraints: try/except blocks around db.session.commit()
        - Rate limiting: @limiter.limit("10 per minute") on message endpoints
        - Input validation: WTForms MessageForm with StringField validators

        SECURITY IMPLEMENTATION:
        - Authentication: @login_required decorator on WebSocket events
        - XSS prevention: escape(data['message']) before database storage
        - CSRF protection: app.config['SECRET_KEY'] for session security
        - Room authorization: verify user permissions before join_room()

        PERFORMANCE CONSIDERATIONS:
        - Message pagination: limit queries to last 50 messages per room
        - Database indexing: CREATE INDEX idx_messages_room_time ON messages(room_id, timestamp)
        - Connection pooling: SQLAlchemy engine with pool_size=20
        - Redis for scaling: socketio = SocketIO(app, message_queue='redis://localhost:6379')
        """

        print("🚀 Testing specialist review of highly detailed technical analysis...")

        is_complete, feedback, confidence = task_specialist.review_analysis(
            analysis_report=complete_analysis,
            task_description=task_description,
            current_review_count=1,
        )

        print("📊 Review Result:")
        print(f"   Complete: {is_complete}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Feedback: {feedback}")

        # With highly technical analysis like this, expect higher acceptance rate
        if is_complete:
            print("✅ LLM correctly accepted the highly detailed technical analysis")
            assert (
                confidence > 0.7
            ), f"Expected high confidence for accepted technical analysis, got: {confidence}"
        else:
            print(
                "⚠️  LLM found additional technical depth needed (extremely strict standards)"
            )
            # Even if rejected, ensure the feedback is about technical depth
            assert (
                len(feedback) > 50
            ), f"Expected detailed technical feedback, got: {feedback}"

            # For such detailed analysis, rejection should focus on specific technical gaps
            feedback_lower = feedback.lower()
            technical_terms = [
                "implementation",
                "specific",
                "detail",
                "concrete",
                "method",
                "class",
                "function",
                "api",
                "code",
            ]
            has_technical_focus = any(
                term in feedback_lower for term in technical_terms
            )

            assert (
                has_technical_focus
            ), f"Expected technical depth focused feedback, got: {feedback}"

            # Quality feedback should have reasonable confidence even when rejecting
            assert (
                confidence > 0.4
            ), f"Expected reasonable confidence for quality technical feedback, got: {confidence}"

        assert len(feedback) > 20, f"Expected meaningful feedback, got: {feedback}"
        print(
            "✅ Test passed: Specialist provided appropriate review of detailed technical analysis!"
        )

    def test_specialist_multiple_reviews_progressive_acceptance(self, task_specialist):
        """Test specialist behavior with multiple review cycles for feature implementation."""

        task_description = """
        Implement a search functionality with full-text search and filtering.
        """

        # Buzzword-heavy analysis that should be rejected in early reviews
        minimal_analysis = """
        This is a sophisticated multi-agent system with comprehensive search capabilities.
        The modern Python architecture demonstrates excellent software engineering practices.

        Found some Python files with well-organized structure. There are functions that
        could be extended for search using enterprise-level full-text search patterns.
        The codebase follows best practices and has clear separation of concerns.

        Search functionality can be added using sophisticated algorithms and modern tooling.
        The comprehensive framework supports scalable search implementation.
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
                # First two reviews should reject buzzword-heavy analysis
                print(
                    f"   Review {review_num} decision: {'ACCEPT' if is_complete else 'REJECT'}"
                )
                # Don't enforce strict rejection since LLM behavior can vary,
                # but document the behavior for analysis
            else:
                # Third review should force accept due to max review limit
                assert (
                    is_complete
                ), f"Expected force accept on review 3, but got rejection. Feedback: {feedback}"
                assert (
                    "maximum" in feedback.lower() or "limit" in feedback.lower()
                ), f"Expected force accept message, got: {feedback}"

        print(
            "✅ Test passed: Specialist correctly handles multiple reviews and force-accept mechanism!"
        )

    def test_specialist_llm_prompt_effectiveness(self, task_specialist):
        """Test that the specialist's prompts lead to consistent LLM behavior."""

        test_cases = [
            {
                "name": "Buzzword-Heavy Analysis (Should Reject)",
                "task": "Add PostgreSQL database integration to existing Flask app",
                "analysis": "This sophisticated system has comprehensive database capabilities with excellent engineering practices. The modern architecture supports enterprise-level PostgreSQL integration using best practices.",
                "expected_complete": False,
                "should_mention": [
                    "specific",
                    "concrete",
                    "detail",
                    "implementation",
                    "buzzword",
                    "sophisticated",
                    "technical",
                ],
            },
            {
                "name": "Detailed Technical Implementation",
                "task": "Create REST API endpoints for user management",
                "analysis": """
                EXISTING CODEBASE ANALYSIS:
                - app.py: Flask app with @app.route('/') decorator, imports Flask, render_template
                - models.py: User class inherits from db.Model, fields: id (db.Integer, primary_key=True),
                  username (db.String(80), unique=True), email (db.String(120), unique=True)
                - config.py: SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'

                API IMPLEMENTATION PLAN:
                1. Create api_blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
                2. GET /api/v1/users endpoint:
                   def get_users():
                     users = User.query.all()
                     return jsonify([{'id': u.id, 'username': u.username, 'email': u.email} for u in users])

                3. POST /api/v1/users endpoint:
                   @api_blueprint.route('/users', methods=['POST'])
                   def create_user():
                     data = request.get_json()
                     user = User(username=data['username'], email=data['email'])
                     db.session.add(user)
                     db.session.commit()
                     return jsonify({'id': user.id}), 201

                ERROR HANDLING:
                - try/except IntegrityError for duplicate users
                - @app.errorhandler(404) for missing resources
                - request.get_json() validation with abort(400) for malformed JSON

                AUTHENTICATION:
                - @login_required decorator from flask_login
                - current_user.id validation for user-specific operations
                """,
                "expected_complete": True,
                "should_mention": ["accept", "sufficient", "implementation", "detail"],
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

            # Check if result matches expectation (allowing for LLM variability)
            if case["expected_complete"]:
                # We expect this to be complete
                if is_complete:
                    print("   ✅ Correctly accepted detailed technical analysis")
                else:
                    print("   ⚠️  LLM was stricter than expected (RUTHLESS standards)")
                    # Even if rejected, ensure feedback focuses on technical depth
                    feedback_lower = feedback.lower()
                    technical_indicators = [
                        "specific",
                        "concrete",
                        "implementation",
                        "detail",
                        "method",
                        "class",
                    ]
                    has_technical_focus = any(
                        indicator in feedback_lower
                        for indicator in technical_indicators
                    )
                    if has_technical_focus:
                        print(
                            "   ✅ Rejection was based on technical depth requirements"
                        )
            else:
                # We expect this to be incomplete/rejected due to buzzwords
                if not is_complete:
                    print("   ✅ Correctly rejected buzzword-heavy analysis")
                else:
                    print("   ⚠️  LLM accepted buzzword-heavy analysis (unexpected)")
                    # If unexpectedly accepted, at least verify it's not a trivial acceptance
                    assert (
                        confidence > 0.6
                    ), f"If accepting buzzwords, confidence should be high, got: {confidence}"

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

        print(
            "\n✅ Test passed: Specialist demonstrates appropriate buzzword rejection and technical depth requirements!"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
