---
name: setup-tooluniverse
description: Install and configure ToolUniverse with MCP integration for Cursor or Claude Desktop. Handles environment detection, installation methods (pip/uv), MCP configuration, compact mode setup, API key configuration, and validation testing. Use when setting up ToolUniverse, configuring MCP servers, troubleshooting installation issues, or when user mentions installing ToolUniverse or setting up scientific tools.
---

# Setup ToolUniverse

This skill guides you through installing and configuring ToolUniverse with MCP (Model Context Protocol) integration for Cursor or Claude Desktop.

## Critical Context Warning

⚠️ **ToolUniverse has 764+ tools** which will cause context window overflow if all exposed directly. **Always use compact mode** unless the user explicitly requests otherwise.

**Compact mode** exposes only 5 core tools (list_tools, grep_tools, get_tool_info, execute_tool, find_tools) while keeping all 764+ tools accessible via execute_tool.

## Discovery Phase

Before installation, gather:

1. **Target application**: Cursor or Claude Desktop?
2. **Python version**: Run `python3 --version` (requires >=3.10, <3.14)
3. **Package manager preference**: pip or uv?
4. **Installation type**: 
   - PyPI (stable): `pip install tooluniverse`
   - Development (local): `pip install -e /path/to/ToolUniverse`
5. **Tool categories** (optional): Load specific categories or all tools?

Use the provided validation script to check prerequisites: `python scripts/check_prerequisites.py`

## Installation Workflow

### Step 1: Verify Prerequisites

```bash
# Check Python version (must be 3.10-3.13)
python3 --version

# Check pip
python3 -m pip --version

# Check uv (optional but recommended)
which uv || echo "uv not installed"
```

**If uv not installed** (recommended for MCP):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Install ToolUniverse

**Option A: Using pip (standard)**
```bash
pip install tooluniverse
```

**Option B: Using uv (recommended for MCP)**
```bash
# Create dedicated directory
mkdir -p ~/tooluniverse-env
cd ~/tooluniverse-env

# Install with uv
uv pip install tooluniverse
```

**Option C: Development installation**
```bash
cd /path/to/ToolUniverse-main
pip install -e .
```

### Step 3: Verify Installation

Run the validation script:
```bash
python scripts/verify_installation.py
```

Or manually test:
```python
from tooluniverse import ToolUniverse
tu = ToolUniverse()
print(f"ToolUniverse version: {tu.__version__}")
```

### Step 4: Configure MCP Integration

#### For Cursor (mcp.json)

Location: `~/Library/Application Support/Cursor/User/mcp.json` (macOS)

**Method 1: Using installed tooluniverse command (Recommended)**
```json
{
  "mcpServers": {
    "tooluniverse": {
      "command": "tooluniverse-smcp-stdio",
      "args": ["--compact-mode"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

**Method 2: Using uv with working directory**
```json
{
  "mcpServers": {
    "tooluniverse": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/tooluniverse-env",
        "run",
        "tooluniverse-smcp-stdio",
        "--compact-mode"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### For Claude Desktop

Open Claude Desktop → Settings → Developer → Edit Config

Use the same JSON configuration as above.

### Step 5: Optional - Configure API Keys

Some tools require API keys. Create `.env` file:

```bash
# In your project directory or ~/.cursor/
cat > .env << 'EOF'
# Optional: LLM API keys for agentic tools
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here

# Optional: UMLS API key for medical terminology
UMLS_API_KEY=your_key_here
EOF
```

**Note**: Most tools work without API keys. Only specialized features require them.

### Step 6: Test MCP Integration

Run the test script:
```bash
python scripts/test_mcp_connection.py
```

Or manually restart Cursor/Claude Desktop and verify:
- Look for "tooluniverse" in MCP servers list
- Try calling: `list_tools` or `grep_tools` with keyword "protein"

## Common Issues & Solutions

### Issue 1: Python Version Incompatibility

**Symptom**: `requires-python = ">=3.10"` error

**Solution**:
```bash
# Check version
python3 --version

# If < 3.10 or >= 3.14, install compatible Python
# macOS with Homebrew:
brew install python@3.12

# Then use specific version:
python3.12 -m pip install tooluniverse
```

### Issue 2: Command Not Found (tooluniverse-smcp-stdio)

**Symptom**: `tooluniverse-smcp-stdio: command not found`

**Solution**:
```bash
# Verify installation location
pip show tooluniverse

# Check if scripts directory is in PATH
which tooluniverse-smcp-stdio

# If not found, use full path or reinstall:
pip install --force-reinstall tooluniverse
```

### Issue 3: Context Window Overflow

**Symptom**: MCP server loads but Cursor/Claude becomes slow or errors

**Solution**: **Enable compact mode** (should already be set):
- Verify `--compact-mode` is in args
- Restart application
- Check you're using stdio command, not HTTP server

### Issue 4: uv Directory Not Found

**Symptom**: `directory /path/to/tooluniverse-env not found`

**Solution**:
```bash
# Create directory and install
mkdir -p ~/tooluniverse-env
cd ~/tooluniverse-env
uv pip install tooluniverse

# Update mcp.json with correct absolute path
```

### Issue 5: Import Errors for Specific Tools

**Symptom**: Some tools fail with `ModuleNotFoundError`

**Solution**: Install optional dependencies:
```bash
# For single-cell tools
pip install tooluniverse[singlecell]

# For ML/embedding tools
pip install tooluniverse[ml,embedding]

# For visualization tools
pip install tooluniverse[visualization]

# For all features
pip install tooluniverse[all]
```

### Issue 6: MCP Server Won't Start

**Symptom**: No tooluniverse server appears in Cursor/Claude

**Diagnostic steps**:
1. Test command directly:
   ```bash
   tooluniverse-smcp-stdio --compact-mode
   # Should start without errors (Ctrl+C to exit)
   ```

2. Check JSON syntax in mcp.json (no trailing commas, proper quotes)

3. View Cursor logs:
   - macOS: `~/Library/Application Support/Cursor/logs/`
   - Look for MCP-related errors

4. Verify file permissions on mcp.json

## Advanced Configuration

### Loading Specific Tool Categories

Instead of compact mode, load only specific categories:

```json
{
  "mcpServers": {
    "tooluniverse": {
      "command": "tooluniverse-smcp-stdio",
      "args": [
        "--categories", "uniprot", "ChEMBL", "opentarget", "pdb"
      ]
    }
  }
}
```

**Warning**: Still may cause context issues with multiple categories.

### Environment-Specific Configuration

Set working directory for project-specific setup:

```json
{
  "mcpServers": {
    "tooluniverse": {
      "command": "tooluniverse-smcp-stdio",
      "args": ["--compact-mode"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "TOOLUNIVERSE_CACHE_DIR": "/path/to/project/.cache/tooluniverse"
      }
    }
  }
}
```

## Post-Installation Verification

Use the comprehensive test script:
```bash
python scripts/test_mcp_connection.py
```

This tests:
- ✓ ToolUniverse import
- ✓ Version check
- ✓ Tool loading
- ✓ Basic tool execution
- ✓ MCP command availability

## Setup Checklist

Complete setup verification:

```
- [ ] Python version 3.10-3.13 installed
- [ ] pip or uv available
- [ ] ToolUniverse installed (verify with: pip show tooluniverse)
- [ ] MCP config file created (mcp.json)
- [ ] Compact mode enabled in config
- [ ] Application restarted (Cursor or Claude Desktop)
- [ ] MCP server appears in server list
- [ ] Can execute test query (list_tools or grep_tools)
- [ ] Optional: API keys configured (if needed)
```

## Quick Validation

Run this one-liner to verify setup:

```python
python3 -c "from tooluniverse import ToolUniverse; tu = ToolUniverse(); tu.load_tools(); print(f'✓ Loaded {len(tu.tools)} tools')"
```

Expected output: `✓ Loaded 764 tools` (or similar number)

## Troubleshooting Script

For persistent issues, run diagnostic:

```bash
python scripts/diagnose_setup.py
```

This generates a report with:
- System information
- Python environment details
- Installation status
- Configuration validation
- Common issue detection

## Additional Resources

- Installation guide: See [INSTALL.md](INSTALL.md) for detailed installation options
- MCP configuration: See [MCP_CONFIG.md](MCP_CONFIG.md) for advanced configurations
- Tool categories: Run `python scripts/list_tool_categories.py` to see available categories

## Notes

- **Always prefer compact mode** to avoid context overflow
- uv is recommended for isolation but not required
- Most tools work without API keys
- Installation takes ~2-5 minutes depending on dependencies
- First tool load may take 10-30 seconds (subsequent loads are faster)
