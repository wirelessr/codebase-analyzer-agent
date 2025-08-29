#!/bin/bash

# Simple E2E Test - Normal User Workflow
# Tests the CLI as a normal user would use it

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${BLUE}=== AutoGen Codebase Agent E2E Test ===${NC}"
echo "Testing normal user workflow on current project: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Test CLI help
echo -e "${BLUE}1. Testing CLI help...${NC}"
uv run codebase-agent --help
echo ""

# Step 2: Check setup
echo -e "${BLUE}2. Running setup validation...${NC}"
uv run codebase-agent setup .
echo ""

# Step 3: Test analyze command - simple task
echo -e "${BLUE}3. Testing analyze command with simple task...${NC}"
echo "Task: Find all Python files in the project"
uv run codebase-agent analyze . "Find all Python files in this project"
echo ""

# Step 4: Test analyze command - architecture question
echo -e "${BLUE}4. Testing analyze command with architecture question...${NC}"
echo "Task: Understand the project structure and main components"
uv run codebase-agent analyze . "Explain the project structure and identify the main components of this AutoGen codebase agent"
echo ""

# Step 5: Test JSON output
echo -e "${BLUE}5. Testing JSON output format...${NC}"
echo "Task: Simple analysis with JSON output"
uv run codebase-agent analyze . "List the main directories" --output-format json
echo ""

echo -e "${GREEN}✅ E2E Test completed successfully!${NC}"
echo "All CLI commands work as expected for normal user workflow."
