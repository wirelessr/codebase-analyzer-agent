"""
Integration test for Code Analyzer with real LLM and tool calls.

TESTING SCENARIO: ARCHITECTURE ANALYSIS (Node.js Express Project)
This test focuses on analyzing codebase architecture and system structure
using real LLM interaction and shell tool execution. It verifies that
the Code Analyzer can effectively understand and describe:
- Project structure and organization (Node.js/Express patterns)
- Component relationships and dependencies (npm modules, middleware)
- Module architecture and design patterns (MVC, middleware patterns)
- System-level design decisions (Express routing, async patterns)
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from codebase_agent.agents.code_analyzer import CodeAnalyzer
from codebase_agent.config.configuration import ConfigurationManager


class TrackingShellTool:
    """Shell tool that tracks calls while executing real commands."""

    def __init__(self, working_dir):
        self.working_dir = working_dir
        self.calls = []

    def execute_command(self, command: str) -> str:
        """Execute command and track the call.

        Args:
            command: The shell command to execute

        Returns:
            Command output as a string
        """
        self.calls.append(command)
        print(f"🔧 Shell tool called: {command}")

        try:
            original_cwd = os.getcwd()
            os.chdir(self.working_dir)

            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=10
            )

            os.chdir(original_cwd)

            if result.returncode == 0:
                output = result.stdout or "Command executed successfully"
                print(f"✅ Command output: {output[:100]}...")
                return output
            else:
                error_msg = f"Command failed: {result.stderr}"
                print(f"❌ Command error: {error_msg}")
                return error_msg

        except Exception as e:
            error_msg = f"Exception executing command: {str(e)}"
            print(f"💥 Exception: {error_msg}")
            return error_msg


class TestCodeAnalyzerIntegration:
    """Integration test for Code Analyzer with real LLM interaction."""

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
    def test_codebase(self):
        """Create a comprehensive Node.js Express test codebase to verify smart analysis strategies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "express_api_project"
            project_dir.mkdir()

            # Create package.json - project configuration
            (project_dir / "package.json").write_text(
                """{
  "name": "express-api-server",
  "version": "1.0.0",
  "description": "RESTful API server with Express.js",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "lint": "eslint ."
  },
  "dependencies": {
    "express": "^4.18.0",
    "mongoose": "^6.3.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^8.5.1",
    "cors": "^2.8.5",
    "helmet": "^5.1.0",
    "dotenv": "^16.0.0",
    "express-rate-limit": "^6.3.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.16",
    "jest": "^28.1.0",
    "eslint": "^8.17.0"
  },
  "keywords": ["api", "express", "mongodb", "jwt", "rest"],
  "author": "Test Developer",
  "license": "MIT"
}"""
            )

            # Create server.js - main entry point
            (project_dir / "server.js").write_text(
                """const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const { errorHandler, notFound } = require('./middleware/errorMiddleware');
const { logger } = require('./utils/logger');

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || 'http://localhost:3000',
    credentials: true
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP'
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/apidb', {
    useNewUrlParser: true,
    useUnifiedTopology: true
})
.then(() => logger.info('MongoDB connected successfully'))
.catch(err => logger.error('MongoDB connection error:', err));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'OK',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        environment: process.env.NODE_ENV || 'development'
    });
});

// Error handling middleware (must be last)
app.use(notFound);
app.use(errorHandler);

app.listen(PORT, () => {
    logger.info(`Server running on port ${PORT} in ${process.env.NODE_ENV || 'development'} mode`);
});

module.exports = app;
"""
            )

            # Create README.md
            (project_dir / "README.md").write_text(
                """# Express API Server

A RESTful API server built with Express.js and MongoDB.

## Features

- User authentication with JWT
- MongoDB integration with Mongoose
- Input validation and sanitization
- Error handling middleware
- Request rate limiting
- Security headers with Helmet
- Comprehensive logging system

## Architecture

- **server.js** - Main application entry point and middleware setup
- **routes/** - API route handlers organized by resource
- **models/** - Mongoose data models and schemas
- **middleware/** - Custom middleware functions
- **utils/** - Utility functions and helpers

## Quick Start

1. Install dependencies: `npm install`
2. Copy `.env.example` to `.env` and configure
3. Start development server: `npm run dev`

## API Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/users` - Get users (authenticated)
- `GET /health` - Health check endpoint
"""
            )

            yield str(project_dir)

    def test_analyzer_smart_code_reading_strategies(self, real_config, test_codebase):
        """Test smart code reading strategies with Node.js Express project - file structure mapping, targeted reading, cross-file analysis."""

        # Enable debug logging to see LLM responses
        import logging

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("codebase_agent.agents.code_analyzer")
        logger.setLevel(logging.DEBUG)

        tracking_tool = TrackingShellTool(test_codebase)
        analyzer = CodeAnalyzer(real_config, tracking_tool)

        # Test comprehensive analysis that should trigger smart reading strategies
        query = "Analyze this Node.js Express API project comprehensively. I need to understand: 1) The server architecture and middleware setup, 2) How authentication and security is implemented, 3) The API routing structure and endpoints, 4) Database integration and data models."

        print("🚀 Starting Node.js Express smart code reading strategy test...")
        print(f"📁 Test codebase: {test_codebase}")
        print(f"🔍 Query: {query}")

        # Run the full analyze_codebase flow
        result = analyzer.analyze_codebase(query, test_codebase)

        print("📝 Analysis result:")
        print(result[:500] + "..." if len(result) > 500 else result)

        # Verify that smart reading strategies were used
        commands = tracking_tool.calls
        print(f"📋 Commands executed ({len(commands)}):")
        for i, cmd in enumerate(commands, 1):
            print(f"  {i}. {cmd}")

        # Assertions for Node.js-specific smart analysis
        assert len(commands) > 0, "Expected shell commands to be executed"
        assert result, "Expected non-empty analysis result"

        # Verify discovery of Node.js project structure
        has_package_json_discovery = any("package.json" in cmd for cmd in commands)
        assert has_package_json_discovery, "Expected discovery of package.json"

        # Verify file reading strategies
        has_file_reading = any(
            "cat" in cmd or "head" in cmd or "tail" in cmd for cmd in commands
        )
        assert has_file_reading, "Expected file reading commands"

        # Verify Node.js specific pattern recognition
        assert (
            "express" in result.lower() or "node" in result.lower()
        ), "Expected Node.js/Express recognition"

        print("✅ Smart code reading strategy test completed successfully!")

    def test_analyzer_file_size_adaptive_strategy(self, real_config, test_codebase):
        """Test file size adaptive reading strategy with Node.js project."""

        tracking_tool = TrackingShellTool(test_codebase)
        analyzer = CodeAnalyzer(real_config, tracking_tool)

        query = "Analyze the main server file and explain the Express.js middleware chain and routing setup."

        print("🚀 Testing file size adaptive strategy...")

        result = analyzer.analyze_codebase(query, test_codebase)

        commands = tracking_tool.calls
        print(f"📋 Commands executed for adaptive strategy ({len(commands)}):")
        for i, cmd in enumerate(commands, 1):
            print(f"  {i}. {cmd}")

        # Verify adaptive file reading strategies (more flexible approach)
        has_file_analysis = any(
            any(cmd_part in cmd for cmd_part in ["wc -l", "file ", "stat ", "ls -l"])
            for cmd in commands
        )
        assert has_file_analysis, f"Expected file analysis commands, got: {commands}"

        has_content_reading = any(
            "cat" in cmd or "head" in cmd or "tail" in cmd for cmd in commands
        )
        assert (
            has_content_reading
        ), f"Expected content reading commands, got: {commands}"

        # Verify Node.js middleware understanding
        assert (
            "middleware" in result.lower() or "express" in result.lower()
        ), "Expected Express.js middleware understanding"

        print("✅ File size adaptive strategy test completed!")
