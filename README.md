# AutoGen Codebase Understanding Agent

[![CI](https://github.com/wirelessr/codebase-analyzer-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/wirelessr/codebase-analyzer-agent/actions/workflows/ci.yml) [![codecov](https://codecov.io/gh/wirelessr/codebase-analyzer-agent/graph/badge.svg?token=CouWO5O69U)](https://codecov.io/gh/wirelessr/codebase-analyzer-agent)

An intelligent agent system built with Microsoft AutoGen framework that analyzes, understands, and provides insights about codebases through multi-agent collaboration and shell-based exploration.

## Features

- **Multi-Agent Architecture**: Specialized agents for code analysis and task management using AutoGen framework
- **Intelligent Codebase Analysis**: Smart exploration using shell commands (find, grep, cat) for targeted insights
- **Task-Specific Analysis**: Focused analysis based on user queries (e.g., "implement OAuth authentication")
- **OpenAI-Compatible APIs**: Support for OpenAI, OpenRouter, LiteLLM, and other compatible services
- **Secure Shell Execution**: Controlled command execution with safety constraints
- **UV Package Management**: Fast and reliable Python dependency management

## Prerequisites

- Python 3.10 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended for dependency management)

### Installing UV

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: using pip
pip install uv
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd codebase-agent
```

### 2. Install Dependencies

Using UV (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -e .
```

For development:
```bash
uv sync --extra dev

# Optional: Install type checking tools
uv sync --extra typing
```

### 3. Configure Environment

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your API configuration:
   ```bash
   # For OpenAI
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4

   # For OpenRouter (alternative)
   # OPENAI_API_KEY=your_openrouter_api_key_here
   # OPENAI_BASE_URL=https://openrouter.ai/api/v1
   # OPENAI_MODEL=openai/gpt-4
   ```

### 4. Verify Setup

```bash
# Check configuration and dependencies (requires codebase path)
codebase-agent setup .

# Or if using uv:
uv run codebase-agent setup .

# Test API connectivity
uv run codebase-agent setup . --check-api
```

## Usage

### Basic Analysis

Analyze your codebase for specific tasks:

```bash
# Analyze for authentication implementation
codebase-agent analyze . "implement OAuth user authentication"

# Analyze for payment processing
codebase-agent analyze . "add payment processing with Stripe"

# General codebase overview
codebase-agent analyze . "understand the project structure and main components"

# Or if using uv:
uv run codebase-agent analyze . "implement OAuth user authentication"
```

### Advanced Usage

```bash
# Specify different codebase path
codebase-agent analyze /path/to/project "implement user authentication"

# Specify working directory (different from codebase path)
codebase-agent analyze ./my-project "add database migration system" --working-dir /tmp/workspace

# Enable debug logging
codebase-agent --verbose analyze . "add database migration system"

# Use different model
OPENAI_MODEL=gpt-3.5-turbo codebase-agent analyze . "optimize database queries"

# JSON output format
codebase-agent analyze . "analyze authentication patterns" --output-format json
```

## How It Works

The system uses a multi-agent approach:

1. **Code Analyzer Agent**: Technical expert that explores the codebase using shell commands
2. **Task Specialist Agent**: Project manager that reviews analysis completeness and provides feedback
3. **Shell Tool**: Secure interface for executing read-only commands like `find`, `grep`, `cat`

The agents collaborate through AutoGen's conversation framework to provide comprehensive analysis:

- **Progressive Analysis**: Multi-round exploration starting with targeted searches
- **Self-Assessment**: Agents evaluate their own completeness and continue until satisfied
- **Peer Review**: Task specialist reviews technical analysis for completeness
- **Convergence Logic**: Maximum 3 review cycles before final response

## Supported APIs

Configure any OpenAI-compatible API:

### OpenAI Direct
```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

### OpenRouter
```env
OPENAI_API_KEY=sk-or-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4
```

### LiteLLM Proxy
```env
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=http://localhost:4000
OPENAI_MODEL=gpt-4
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --extra dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=codebase_agent --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_configuration.py

# Run integration tests only
uv run pytest -m integration

# Run unit tests only
uv run pytest -m unit
```

### Code Quality

```bash
# Format code
uv run black codebase_agent tests

# Lint code
uv run ruff check codebase_agent tests

# Fix linting issues automatically
uv run ruff check --fix codebase_agent tests
```

#### Optional Type Checking

Type checking with mypy is configured but not currently enforced in CI:

```bash
# Install type checking dependencies
uv sync --extra typing

# Run type checking (will show type annotation gaps)
uv run mypy codebase_agent
```

> **Note**: The codebase currently has incomplete type annotations. Type checking is available for development but not required for contributions.

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `OPENAI_API_KEY` | API key for OpenAI-compatible service | Required |
| `OPENAI_BASE_URL` | Base URL for API endpoint | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Model to use for analysis | `gpt-4` |
| `AGENT_TIMEOUT` | Timeout for agent operations (seconds) | `300` |
| `MAX_SHELL_OUTPUT_SIZE` | Maximum output size for shell commands | `10000` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `MODEL_TEMPERATURE` | LLM temperature (0.0-1.0) | `0.1` |
| `MAX_TOKENS` | Maximum tokens for responses | `4000` |

## Example Scenarios

### 1. Implementing Authentication

```bash
# Analyze existing authentication patterns
codebase-agent analyze . "implement OAuth2 authentication for user login"
```

**Expected Analysis:**
- Identifies existing user models and authentication middleware
- Locates configuration files and security settings
- Suggests integration points for OAuth2 providers
- Provides step-by-step implementation guidance

### 2. Adding API Endpoints

```bash
# Analyze for REST API development
codebase-agent analyze . "add REST API endpoints for user management"
```

**Expected Analysis:**
- Discovers existing API routing patterns
- Identifies database models and validation logic
- Suggests endpoint structure following project conventions
- Recommends appropriate HTTP status codes and response formats

### 3. Database Integration

```bash
# Analyze database architecture
codebase-agent analyze . "add database migration system for user profiles"
```

**Expected Analysis:**
- Examines existing database configuration and ORM usage
- Identifies migration patterns and schema management
- Suggests migration file structure and naming conventions
- Provides guidance on data type selection and constraints

### 4. Frontend Integration

```bash
# Analyze frontend-backend integration
codebase-agent analyze . "connect React frontend to authentication API"
```

**Expected Analysis:**
- Identifies API client patterns and state management
- Locates authentication flow components
- Suggests integration patterns for token management
- Provides guidance on error handling and user feedback

### 5. Testing Strategy

```bash
# Analyze testing infrastructure
codebase-agent analyze . "add comprehensive tests for payment processing"
```

**Expected Analysis:**
- Examines existing test patterns and frameworks
- Identifies testing utilities and mock patterns
- Suggests test coverage for business logic
- Provides guidance on integration and unit test separation

## Troubleshooting

### Common Issues

#### 1. API Key and Configuration Issues

**Problem**: "Configuration validation failed" or "API key invalid"

**Solutions**:
- Verify your API key is correct and has sufficient credits/quota
- Check that the base URL matches your API provider exactly
- Ensure no extra spaces or characters in your `.env` file
- Test your API key with a simple curl command:
  ```bash
  curl -H "Authorization: Bearer $OPENAI_API_KEY" \
       -H "Content-Type: application/json" \
       "$OPENAI_BASE_URL/models"
  ```

**For OpenRouter**:
- Use format: `sk-or-v1-...` for API keys
- Base URL should be: `https://openrouter.ai/api/v1`
- Check [OpenRouter documentation](https://openrouter.ai/docs) for model names

**For Local LiteLLM**:
- Start LiteLLM proxy: `litellm --model gpt-4 --port 4000`
- Use `http://localhost:4000` as base URL
- API key can be any non-empty string for local usage

#### 2. UV and Python Environment Issues

**Problem**: "UV not found" or "Python version mismatch"

**Solutions**:
- Install UV using the official installer:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Restart your terminal after UV installation
- Check UV is in PATH: `uv --version`
- Alternative installation using pip: `pip install uv`
- For Python version issues, install correct version:
  ```bash
  uv python install 3.11
  uv sync
  ```

#### 3. Permission and File Access Errors

**Problem**: "Permission denied" or "Cannot access directory"

**Solutions**:
- Ensure the target directory is readable: `ls -la /path/to/codebase`
- Run with appropriate permissions (avoid sudo unless necessary)
- Check if directory is on a mounted drive with access restrictions
- For network drives, ensure proper mount permissions
- Verify the path exists and is a directory: `cd /path/to/codebase`

#### 4. Analysis Timeout and Performance Issues

**Problem**: "Analysis timeout" or "Taking too long"

**Solutions**:
- Increase timeout in environment variables:
  ```bash
  export AGENT_TIMEOUT=600  # 10 minutes
  export MAX_SHELL_OUTPUT_SIZE=50000
  ```
- Use more specific queries to reduce scope:
  - Instead of: "analyze the entire codebase"
  - Use: "analyze authentication modules in the user management system"
- For very large codebases (>50k files), consider:
  - Analyzing specific subdirectories
  - Using `.gitignore` patterns to exclude build artifacts
  - Focusing on source code directories only

#### 5. AutoGen Framework Issues

**Problem**: "AutoGen initialization failed" or "Agent conversation errors"

**Solutions**:
- Update to latest AutoGen version: `uv sync`
- Check for conflicting dependencies: `uv tree`
- Clear Python cache: `find . -name "*.pyc" -delete`
- Verify AutoGen installation:
  ```python
  python -c "import autogen; print(autogen.__version__)"
  ```
- For conversation flow issues, check logs in `logs/` directory

#### 6. Model and Token Limit Issues

**Problem**: "Token limit exceeded" or "Model not found"

**Solutions**:
- Reduce analysis scope with more specific queries
- Use models with higher token limits (e.g., GPT-4 Turbo)
- Check available models for your API provider:
  ```bash
  curl -H "Authorization: Bearer $OPENAI_API_KEY" \
       "$OPENAI_BASE_URL/models"
  ```
- Adjust token limits in environment:
  ```bash
  export MAX_TOKENS=8000
  export MODEL_TEMPERATURE=0.1
  ```

### Debug Mode and Logging

Enable comprehensive debug logging:

```bash
# Environment variable method
LOG_LEVEL=DEBUG codebase-agent analyze . "your query"

# Command line flag method
codebase-agent --verbose analyze . "your query"

# Save debug output to file
codebase-agent --verbose analyze . "your query" 2>&1 | tee debug.log
```

**Log File Locations**:
- Main logs: `logs/agent.log`
- Conversation logs: `logs/conversations/`
- Error logs: Check stderr output

**Understanding Log Output**:
- `iteration_start`: Beginning of analysis round
- `command_executed`: Shell command results
- `knowledge_update`: Agent learning progression
- `review_complete`: Task specialist feedback
- `convergence_decision`: Analysis completion logic

### Getting Help

1. **Check logs first**: Enable debug mode and review log output
2. **Verify configuration**: Run `codebase-agent setup .` to validate
3. **Test with simple query**: Try `codebase-agent analyze . "list all Python files"` to verify basic functionality
4. **Update dependencies**: Run `uv sync` to ensure latest versions
5. **Create minimal reproduction**: Test with a simple project structure

If issues persist, create an issue with:
- Your environment details (`uv python list`, `uv --version`)
- Complete error messages and log output
- Minimal example that reproduces the issue
- Your `.env` configuration (without sensitive data)

## Documentation

- **[Installation Guide](docs/installation.md)**: Comprehensive installation instructions for all platforms
- **[Example Use Cases](docs/examples.md)**: Detailed examples for common development scenarios
- **[Troubleshooting Guide](docs/troubleshooting.md)**: Solutions for common issues and problems

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `uv run pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- Create an issue for bug reports or feature requests
- Check the documentation for configuration and usage details
- Review the logs with debug mode enabled for troubleshooting
