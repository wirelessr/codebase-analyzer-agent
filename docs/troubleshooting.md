# Troubleshooting Guide

This guide provides detailed solutions for common issues you might encounter when using the AutoGen Codebase Understanding Agent.

## Quick Diagnostics

Before diving into specific issues, run these quick diagnostic commands:

```bash
# Check basic setup
codebase-agent setup

# Test with debug logging
codebase-agent --debug analyze "list all Python files in the project"

# Verify environment
uv --version
uv python list
env | grep -E "(OPENAI|MODEL|API)"
```

## Configuration Issues

### Issue: "Configuration validation failed"

**Symptoms**:
- Error message about missing or invalid configuration
- Agent fails to start or initialize
- API key validation errors

**Root Causes & Solutions**:

1. **Missing .env file**:
   ```bash
   # Copy template and edit
   cp .env.example .env
   # Edit .env with your actual values
   nano .env
   ```

2. **Invalid API key format**:
   ```bash
   # Check your API key format
   echo $OPENAI_API_KEY | wc -c  # Should be reasonable length
   
   # For OpenAI: starts with sk-
   # For OpenRouter: starts with sk-or-
   # For Azure: different format entirely
   ```

3. **Incorrect base URL**:
   ```bash
   # Test your endpoint
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        "$OPENAI_BASE_URL/models"
   
   # Common base URLs:
   # OpenAI: https://api.openai.com/v1
   # OpenRouter: https://openrouter.ai/api/v1
   # Azure: https://your-resource.openai.azure.com/
   # Local LiteLLM: http://localhost:4000
   ```

4. **Environment variable not loaded**:
   ```bash
   # Check if variables are set
   env | grep OPENAI
   
   # Load manually if needed
   export $(cat .env | xargs)
   ```

### Issue: "Model not found" or "Model access denied"

**Solutions**:

1. **Check available models**:
   ```bash
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        "$OPENAI_BASE_URL/models" | jq '.data[].id'
   ```

2. **Update model name in .env**:
   ```env
   # For OpenAI
   OPENAI_MODEL=gpt-4

   # For OpenRouter (include provider prefix)
   OPENAI_MODEL=openai/gpt-4
   OPENAI_MODEL=anthropic/claude-3-sonnet
   
   # For Azure (use deployment name)
   OPENAI_MODEL=your-gpt4-deployment
   ```

3. **Check model permissions**:
   - Verify your API key has access to the requested model
   - Check your account's model quotas and limits
   - Ensure billing is set up correctly

## Installation and Environment Issues

### Issue: "UV not found" or UV installation problems

**Solutions**:

1. **Install UV using official installer**:
   ```bash
   # macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows PowerShell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Restart terminal after installation
   ```

2. **Alternative installation methods**:
   ```bash
   # Using pip
   pip install uv
   
   # Using Homebrew (macOS)
   brew install uv
   
   # Using conda
   conda install -c conda-forge uv
   ```

3. **PATH issues**:
   ```bash
   # Check if UV is in PATH
   which uv
   uv --version
   
   # Add to PATH if needed (add to ~/.bashrc or ~/.zshrc)
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

### Issue: Python version compatibility

**Solutions**:

1. **Install compatible Python version**:
   ```bash
   # List available Python versions
   uv python list
   
   # Install specific version
   uv python install 3.11
   uv python install 3.12
   
   # Use specific Python version
   uv sync --python 3.11
   ```

2. **Check current Python version**:
   ```bash
   uv python pin 3.11  # Pin project to specific version
   uv sync              # Reinstall with correct version
   ```

### Issue: Dependency conflicts or installation failures

**Solutions**:

1. **Clear UV cache**:
   ```bash
   uv cache clean
   uv sync --reinstall
   ```

2. **Check for conflicting dependencies**:
   ```bash
   uv tree  # View dependency tree
   uv sync --resolution=highest  # Try latest compatible versions
   ```

3. **Use development dependencies**:
   ```bash
   uv sync --all-extras  # Install all optional dependencies
   uv sync --dev         # Install development dependencies
   ```

## Runtime and Performance Issues

### Issue: "Analysis timeout" or very slow analysis

**Symptoms**:
- Analysis takes more than 5-10 minutes
- Process appears to hang
- Timeout error messages

**Solutions**:

1. **Increase timeout settings**:
   ```env
   # In .env file
   AGENT_TIMEOUT=1200           # 20 minutes
   MAX_SHELL_OUTPUT_SIZE=100000 # Larger output buffer
   MODEL_TEMPERATURE=0.1        # More focused responses
   MAX_TOKENS=8000             # Higher token limit
   ```

2. **Optimize your query**:
   ```bash
   # Instead of broad queries
   codebase-agent analyze "understand the entire application"
   
   # Use specific, focused queries
   codebase-agent analyze "find authentication mechanisms in the user module"
   ```

3. **Reduce codebase scope**:
   ```bash
   # Analyze specific directory
   cd src/
   codebase-agent analyze "implement user validation in this directory"
   
   # Use .gitignore to exclude large files
   echo "node_modules/" >> .gitignore
   echo "*.log" >> .gitignore
   echo "dist/" >> .gitignore
   ```

### Issue: "Permission denied" or file access errors

**Solutions**:

1. **Check file permissions**:
   ```bash
   # Check directory permissions
   ls -la /path/to/codebase
   
   # Fix permissions if needed
   chmod -R +r /path/to/codebase
   ```

2. **Run from correct directory**:
   ```bash
   # Ensure you're in the right directory
   cd /path/to/your/project
   codebase-agent analyze "your query"
   ```

3. **Check for symlinks or mounted drives**:
   ```bash
   # Check if path is a symlink
   ls -la /path/to/codebase
   
   # For network drives, ensure proper mounting
   mount | grep /path/to/codebase
   ```

## AutoGen Framework Issues

### Issue: AutoGen initialization failures

**Solutions**:

1. **Check AutoGen installation**:
   ```bash
   uv run python -c "import autogen; print(autogen.__version__)"
   uv run python -c "from autogen import ConversableAgent; print('OK')"
   ```

2. **Reinstall AutoGen**:
   ```bash
   uv remove autogen-agentchat autogen-ext
   uv add "autogen-agentchat==0.7.4" "autogen-ext[openai]==0.7.4"
   ```

3. **Clear Python cache**:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   uv sync --reinstall
   ```

### Issue: Agent conversation errors or unexpected responses

**Solutions**:

1. **Enable debug logging**:
   ```bash
   LOG_LEVEL=DEBUG codebase-agent analyze "your query"
   ```

2. **Check conversation logs**:
   ```bash
   # Look at recent conversation logs
   ls -la logs/conversations/
   cat logs/conversations/latest.json | jq .
   ```

3. **Reduce conversation complexity**:
   ```env
   # In .env file
   MAX_CONVERSATION_ROUNDS=5  # Reduce from default 10
   MODEL_TEMPERATURE=0.0      # More deterministic responses
   ```

## API and Network Issues

### Issue: API rate limiting or quota exceeded

**Symptoms**:
- HTTP 429 errors
- "Rate limit exceeded" messages
- Slow API responses

**Solutions**:

1. **Check API usage and limits**:
   ```bash
   # For OpenAI, check dashboard: https://platform.openai.com/usage
   # For OpenRouter, check: https://openrouter.ai/credits
   ```

2. **Implement rate limiting**:
   ```env
   # Add delays between requests
   REQUEST_DELAY=1  # 1 second between requests
   ```

3. **Switch to different model**:
   ```env
   # Use less expensive models
   OPENAI_MODEL=gpt-3.5-turbo  # Instead of gpt-4
   ```

### Issue: Network connectivity problems

**Solutions**:

1. **Test basic connectivity**:
   ```bash
   # Test DNS resolution
   nslookup api.openai.com
   
   # Test HTTP connectivity
   curl -I https://api.openai.com/v1/models
   ```

2. **Check proxy settings**:
   ```bash
   # If behind corporate proxy
   export https_proxy=http://proxy.company.com:8080
   export http_proxy=http://proxy.company.com:8080
   ```

3. **Try alternative endpoints**:
   ```env
   # Switch to different provider temporarily
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_API_KEY=your-openrouter-key
   ```

## Platform-Specific Issues

### macOS Issues

1. **Gatekeeper blocking execution**:
   ```bash
   # Allow execution if blocked
   spctl --assess --verbose /path/to/executable
   xattr -rd com.apple.quarantine /path/to/codebase-agent
   ```

2. **Homebrew Python conflicts**:
   ```bash
   # Use UV's Python instead of system Python
   uv python pin 3.11
   uv sync
   ```

### Windows Issues

1. **PowerShell execution policy**:
   ```powershell
   # Enable script execution
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Path length limitations**:
   ```bash
   # Enable long paths in Windows 10/11
   # Run as Administrator:
   # New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

### Linux Issues

1. **Missing system dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install build-essential python3-dev
   
   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install python3-devel
   ```

2. **SELinux restrictions**:
   ```bash
   # Check SELinux status
   getenforce
   
   # Temporarily disable if needed
   sudo setenforce 0
   ```

## Debugging and Logging

### Enable Comprehensive Logging

1. **Maximum debug output**:
   ```bash
   LOG_LEVEL=DEBUG \
   DEBUG=true \
   codebase-agent --debug analyze "your query" 2>&1 | tee debug.log
   ```

2. **Analyze log files**:
   ```bash
   # Check main log
   tail -f logs/agent.log
   
   # Parse conversation logs
   cat logs/conversations/*.json | jq '.execution_timeline[]'
   
   # Search for errors
   grep -i error logs/agent.log
   grep -i timeout logs/agent.log
   ```

### Log Analysis

1. **Understanding log events**:
   ```bash
   # Filter by event type
   cat logs/conversations/*.json | jq '.execution_timeline[] | select(.event_type == "command_executed")'
   
   # Check agent interactions
   cat logs/conversations/*.json | jq '.execution_timeline[] | select(.agent == "code_analyzer")'
   ```

2. **Performance analysis**:
   ```bash
   # Check execution times
   cat logs/conversations/*.json | jq '.execution_stats'
   
   # Find slow operations
   grep -E "(timeout|slow|error)" logs/agent.log
   ```

## Getting Help

### Information to Include in Bug Reports

1. **Environment details**:
   ```bash
   # System information
   uname -a
   uv --version
   uv python list
   
   # Package versions
   uv tree | grep -E "(autogen|openai|click)"
   
   # Configuration (without sensitive data)
   env | grep -E "(OPENAI_BASE|OPENAI_MODEL|LOG_LEVEL)" | sed 's/API_KEY=.*/API_KEY=***/'
   ```

2. **Error reproduction**:
   ```bash
   # Minimal example
   codebase-agent --debug analyze "list Python files" > error.log 2>&1
   ```

3. **Log excerpts**:
   ```bash
   # Recent logs
   tail -100 logs/agent.log
   
   # Latest conversation
   cat logs/conversations/$(ls -t logs/conversations/ | head -1)
   ```

### Community Resources

- **GitHub Issues**: Create detailed bug reports with logs and reproduction steps
- **Documentation**: Check README.md and docs/ directory for updates
- **Examples**: Review docs/examples.md for similar use cases

### Creating Minimal Reproduction

1. **Create test project**:
   ```bash
   mkdir test-codebase
   cd test-codebase
   echo "print('hello world')" > main.py
   codebase-agent analyze "find all Python files"
   ```

2. **Test with different configurations**:
   ```bash
   # Test different models
   OPENAI_MODEL=gpt-3.5-turbo codebase-agent analyze "test query"
   
   # Test different providers
   OPENAI_BASE_URL=https://openrouter.ai/api/v1 codebase-agent analyze "test query"
   ```

This troubleshooting guide should help you resolve most common issues. If you encounter problems not covered here, please create a detailed issue report with the information gathering steps outlined above.
