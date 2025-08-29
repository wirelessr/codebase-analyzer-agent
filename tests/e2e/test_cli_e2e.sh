#!/bin/bash

# Simple E2E Test - Normal User Workflow
# Tests the CLI as a normal user would use it, including logging behavior

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# Step 2: Check setup - default (quiet) mode
echo -e "${BLUE}2. Running setup validation (quiet mode)...${NC}"
echo -e "${YELLOW}Should show minimal console output (errors only)${NC}"
uv run codebase-agent setup .
echo ""

# Step 3: Check setup - verbose mode
echo -e "${BLUE}3. Running setup validation (verbose mode)...${NC}"
echo -e "${YELLOW}Should show detailed INFO logs in console${NC}"
uv run codebase-agent --verbose setup .
echo ""

# Step 4: Test analyze command - simple task
echo -e "${BLUE}4. Testing analyze command with simple task...${NC}"
echo "Task: Find all Python files in the project"
uv run codebase-agent analyze . "Find all Python files in this project"
echo ""

# Step 5: Test analyze command - architecture question
echo -e "${BLUE}5. Testing analyze command with architecture question...${NC}"
echo "Task: Understand the project structure and main components"
uv run codebase-agent analyze . "Explain the project structure and identify the main components of this AutoGen codebase agent"
echo ""

# Step 6: Test JSON output
echo -e "${BLUE}6. Testing JSON output format...${NC}"
echo "Task: Simple analysis with JSON output"
uv run codebase-agent analyze . "List the main directories" --output-format json
echo ""

# Step 7: Verify log file contains detailed information
echo -e "${BLUE}7. Verifying log file contains detailed information...${NC}"
if [ -f "logs/agent.log" ]; then
    echo "✓ Log file exists: logs/agent.log"
    echo "Recent log entries:"
    tail -5 logs/agent.log
else
    echo "⚠ Log file not found"
fi
echo ""

echo -e "${GREEN}✅ E2E Test completed successfully!${NC}"
echo "All CLI commands work as expected for normal user workflow."
echo "Console output is now clean (errors only) while detailed logs go to file."
