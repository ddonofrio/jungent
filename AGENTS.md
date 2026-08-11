# Jungent AI Agents Documentation

## Session: Initial Setup (August 11, 2026)

### Project Overview
Jungent is a bleeding-edge AI code assistant that adopts the latest advances in AI-assisted software engineering as soon as they become viable. The project prioritizes staying current over long-term stability.

### Key Principles
1. **Always current** - Adopt meaningful advances quickly
2. **Quality is engineered** - Trust comes from verification, not age
3. **Replace without nostalgia** - No component is permanent when a better one exists
4. **Measure real capability** - Prefer reproducible results over marketing claims
5. **Move fast without guessing** - Rapid change must remain observable, testable, and reversible

### Current Session Tasks

#### Task #1: Setup project infrastructure ✓
- Python project structure
- pytest for testing
- ruff as linter
- black as formatter
- Virtual environment setup

#### Task #2: Create AGENTS.md documentation (in progress)
This file documents important information from developer sessions.

### Language Policy
- **All code and documentation must be in English**, regardless of the language used in communication.

### Tech Stack
- **Language**: Python
- **Testing**: pytest
- **Linting**: ruff (or flake8)
- **Formatting**: black
- **Package Management**: pip / pyproject.toml

### Project Structure (Planned)
```
jungent/
├── src/
│   └── jungent/
│       └── providers/
├── tests/
├── docs/
├── pyproject.toml
├── AGENTS.md
└── README.md
```

### AI Providers Module (Next Task)
Based on Kilo's AI Providers system:
- Support for 30+ providers across categories:
  - Cloud Providers (Anthropic, OpenAI, Google, AWS, etc.)
  - Local & Self-Hosted (Ollama, LM Studio, Atomic Chat, etc.)
  - AI Gateways (OpenRouter, Requesty, DaoXE, etc.)
- Configuration via provider IDs
- Support for `enabled_providers` and `disabled_providers` in config

### Configuration Files
- `pyproject.toml` - Project dependencies and tool configurations
- `pytest.ini` - pytest configuration
- `.ruff.toml` or `[ruff]` section in pyproject.toml - ruff configuration

### Notes
- Never use cmd.exe syntax (`%VAR%`) in PowerShell commands
- Use `$env:VARNAME` for environment variables in PowerShell
- Replace `&&` with `;` for command chaining in PowerShell
- Long-running commands should be run manually, not via automation