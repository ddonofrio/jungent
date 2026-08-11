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

### Mandatory Change Requirements

Every implementation change must satisfy all of the following requirements before it is considered complete:

1. **Implement or update automated tests.** New behaviour, bug fixes, edge cases, and regressions must be covered by tests at the appropriate level. A change that alters executable behaviour without corresponding test coverage is incomplete.
2. **Run the relevant quality checks.** At minimum, run the affected test suite and the configured linting and formatting checks. Report any check that could not be run and why.
3. **Update documentation.** Any change to behaviour, public interfaces, configuration, architecture, setup, or operator workflows must update the relevant documentation in the same change. Documentation-only updates do not require new tests unless they modify executable examples or validation tooling.
4. **Keep examples executable.** Commands, configuration snippets, API examples, and documented model or provider capabilities must match the implemented code and supported versions.
5. **Do not weaken verification to make a change pass.** Tests may only be removed or relaxed when the underlying requirement has intentionally changed, and that change must be documented.

### Definition of Done

A task is complete only when its implementation, automated tests, and documentation agree; all relevant checks pass; and no generated files, credentials, caches, build artefacts, or local environment files are included in the change.

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
