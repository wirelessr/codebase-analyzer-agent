# AutoGen Codebase Understanding Agent

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
# Check configuration and dependencies
codebase-agent setup

# Or if using uv:
uv run codebase-agent setup
```

## Usage

### Basic Analysis

Analyze your codebase for specific tasks:

```bash
# Analyze for authentication implementation
codebase-agent analyze "implement OAuth user authentication"

# Analyze for payment processing
codebase-agent analyze "add payment processing with Stripe"

# General codebase overview
codebase-agent analyze "understand the project structure and main components"
```

### Advanced Usage

```bash
# Specify working directory
codebase-agent analyze "implement user authentication" --directory /path/to/project

# Enable debug logging
codebase-agent --debug analyze "add database migration system"

# Use different model
OPENAI_MODEL=gpt-3.5-turbo codebase-agent analyze "optimize database queries"
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
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_configuration.py
```

### Code Quality

```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src
```

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

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Verify your API key is correct and has sufficient credits
   - Check that the base URL matches your API provider

2. **UV Installation Issues**
   - Ensure UV is installed and in your PATH
   - Try using pip as alternative: `pip install -e .`

3. **Permission Errors**
   - Ensure the working directory is accessible
   - Check file permissions for the codebase being analyzed

4. **Timeout Errors**
   - Increase `AGENT_TIMEOUT` for large codebases
   - Use more specific queries to reduce analysis scope

### Debug Mode

Enable debug logging for detailed information:

```bash
# Environment variable
DEBUG=true codebase-agent analyze "your query"

# Command line flag
codebase-agent --debug analyze "your query"
```

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
