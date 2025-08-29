# Installation Guide

This guide covers various installation methods for the AutoGen Codebase Understanding Agent.

## Quick Installation

### Using UV (Recommended)

```bash
# Install from PyPI (when available)
uv add codebase-agent

# Or install with all features
uv add "codebase-agent[dev]"
```

### Using pip

```bash
# Install from PyPI
pip install codebase-agent

# Or install with development dependencies
pip install "codebase-agent[dev]"
```

## Development Installation

### From Source (Latest)

```bash
# Clone repository
git clone https://github.com/your-org/codebase-agent.git
cd codebase-agent

# Install with UV (recommended)
uv sync --all-extras

# Or install with pip
pip install -e ".[dev]"
```

### From GitHub (Specific Version)

```bash
# Install specific release
uv add "codebase-agent @ git+https://github.com/your-org/codebase-agent.git@v0.1.0"

# Install latest from main branch
uv add "codebase-agent @ git+https://github.com/your-org/codebase-agent.git"
```

## GitHub Packages Installation

If using GitHub Packages (private repositories):

### Configure GitHub Packages Access

1. **Create Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create token with `packages:read` scope
   - Save the token securely

2. **Configure pip/uv for GitHub Packages**:
   ```bash
   # Configure for pip
   pip config set global.extra-index-url https://pypi.pkg.github.com/your-org/

   # Configure authentication
   echo "machine pypi.pkg.github.com" >> ~/.netrc
   echo "login your-github-username" >> ~/.netrc
   echo "password your-personal-access-token" >> ~/.netrc
   ```

3. **Install from GitHub Packages**:
   ```bash
   pip install --index-url https://pypi.pkg.github.com/your-org/simple/ codebase-agent
   ```

## Environment Setup

### Prerequisites

1. **Python 3.10 or higher**:
   ```bash
   python --version  # Should be 3.10+
   ```

2. **UV Package Manager** (recommended):
   ```bash
   # Install UV
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Verify installation
   uv --version
   ```

### API Configuration

1. **Create configuration file**:
   ```bash
   # Copy template
   cp .env.example .env

   # Edit with your settings
   nano .env
   ```

2. **Configure API provider**:

   **OpenAI**:
   ```env
   OPENAI_API_KEY=sk-your-openai-key
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4
   ```

   **OpenRouter**:
   ```env
   OPENAI_API_KEY=sk-or-your-openrouter-key
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_MODEL=openai/gpt-4
   ```

   **Azure OpenAI**:
   ```env
   OPENAI_API_KEY=your-azure-key
   OPENAI_BASE_URL=https://your-resource.openai.azure.com/
   OPENAI_MODEL=your-deployment-name
   AZURE_OPENAI_VERSION=2023-12-01-preview
   ```

   **Local LiteLLM**:
   ```env
   OPENAI_API_KEY=any-key
   OPENAI_BASE_URL=http://localhost:4000
   OPENAI_MODEL=gpt-4
   ```

### Verification

```bash
# Test installation
codebase-agent --version

# Verify configuration
codebase-agent setup

# Test with simple analysis
codebase-agent analyze "list all files in this directory"
```

## Docker Installation

### Using Docker Hub (when available)

```bash
# Pull image
docker pull codebase-agent:latest

# Run with volume mount
docker run -v /path/to/codebase:/workspace \
           -v /path/to/.env:/app/.env \
           codebase-agent analyze "your query"
```

### Build from Source

```bash
# Clone repository
git clone https://github.com/your-org/codebase-agent.git
cd codebase-agent

# Build image
docker build -t codebase-agent .

# Run container
docker run -v $(pwd):/workspace \
           -e OPENAI_API_KEY=your-key \
           codebase-agent analyze "your query"
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  codebase-agent:
    image: codebase-agent:latest
    volumes:
      - ./codebase:/workspace
      - ./.env:/app/.env
    environment:
      - LOG_LEVEL=INFO
    command: analyze "understand project structure"
```

Run:
```bash
docker-compose run codebase-agent
```

## Platform-Specific Installation

### macOS

```bash
# Using Homebrew (if formula available)
brew install codebase-agent

# Using MacPorts
sudo port install py311-codebase-agent

# Using UV
uv add codebase-agent
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install codebase-agent
uv add codebase-agent
```

### CentOS/RHEL/Fedora

```bash
# Install Python and pip
sudo dnf install python3 python3-pip

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install codebase-agent
uv add codebase-agent
```

### Windows

#### Using PowerShell

```powershell
# Install UV
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install codebase-agent
uv add codebase-agent
```

#### Using Windows Package Manager

```powershell
# Install UV via winget
winget install astral-sh.uv

# Install codebase-agent
uv add codebase-agent
```

#### Using Chocolatey

```powershell
# Install UV
choco install uv

# Install codebase-agent
uv add codebase-agent
```

## Virtual Environment Setup

### Using UV (Recommended)

```bash
# Create project with UV
uv init my-project
cd my-project

# Add codebase-agent dependency
uv add codebase-agent

# Activate environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Using venv

```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install codebase-agent
pip install codebase-agent
```

### Using conda

```bash
# Create conda environment
conda create -n codebase-agent python=3.11

# Activate environment
conda activate codebase-agent

# Install codebase-agent
pip install codebase-agent
```

## Troubleshooting Installation

### Common Issues

1. **Python version too old**:
   ```bash
   python --version  # Check version

   # Install newer Python with UV
   uv python install 3.11
   ```

2. **Permission errors**:
   ```bash
   # Use user install
   pip install --user codebase-agent

   # Or use UV which manages environments
   uv add codebase-agent
   ```

3. **Network/proxy issues**:
   ```bash
   # Configure proxy for pip
   pip install --proxy http://proxy.company.com:8080 codebase-agent

   # Configure proxy for UV
   export https_proxy=http://proxy.company.com:8080
   uv add codebase-agent
   ```

4. **Package not found**:
   ```bash
   # Update package index
   pip install --upgrade pip

   # Try alternative index
   pip install -i https://pypi.org/simple/ codebase-agent
   ```

### Verification Commands

```bash
# Check Python installation
python --version
which python

# Check pip installation
pip --version
pip list | grep codebase

# Check UV installation
uv --version
uv list | grep codebase

# Test codebase-agent
codebase-agent --help
codebase-agent --version
```

## Updating

### Update to Latest Version

```bash
# Using UV
uv sync --upgrade

# Using pip
pip install --upgrade codebase-agent
```

### Update from GitHub

```bash
# Pull latest changes
git pull origin main

# Reinstall
uv sync --reinstall
```

### Check for Updates

```bash
# Check current version
codebase-agent --version

# Check available versions
pip index versions codebase-agent

# Check GitHub releases
curl -s https://api.github.com/repos/your-org/codebase-agent/releases/latest | jq .tag_name
```

## Uninstallation

```bash
# Using UV
uv remove codebase-agent

# Using pip
pip uninstall codebase-agent

# Remove configuration
rm -rf ~/.codebase-agent
rm .env
```

For additional help, see the [Troubleshooting Guide](docs/troubleshooting.md) or create an issue on GitHub.
