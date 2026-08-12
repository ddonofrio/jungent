# Jungent Architecture

## Overview

Jungent is a bleeding-edge AI code assistant that adopts the latest advances in AI-assisted software engineering as soon as they become viable. The project prioritizes staying current over long-term stability.

## Core Components

### 1. Providers Module (`src/jungent/providers/`)

The providers module implements support for 30+ AI models across multiple categories:

- **Cloud Providers**: Anthropic, OpenAI, Google, AWS Bedrock
- **Local & Self-Hosted**: Ollama, LM Studio, Atomic Chat  
- **AI Gateways**: OpenRouter, Requesty, DaoXE, etc.

All providers implement the canonical `Request/Response` contract:

```python
async def generate_response_structured(
    request: Request,
    **kwargs: Any,
) -> Response:
    """Canonical API for all providers."""
```

### 2. Proxy Module (`src/jungent/proxy/`)

The proxy module is a deterministic interception engine (Hammer & Scissors) that moves packets between the agent and provider:

- Validates protocol invariants after every mutation
- Applies typed actions (PASS/REWRITE/CUT)
- Records audit trace for debugging
- Supports fail-open/fail-close failure policies

### 3. Instruction Funnel (`src/jungent/modules/instruction_funnel.py`)

The instruction funnel implements three behavioral scenarios:

1. **Large initial prompt** (~7K+ tokens): Extract tool definitions, store in active memory, rewrite context
2. **Work-order request**: Restore only relevant tools for current task
3. **Error recovery**: Recognize actionable tool errors and apply compact recovery instructions

### 4. Active Memory (`src/jungent/memory/`)

The active memory module provides:

- Bounded in-memory storage with deterministic eviction (LRU)
- Conversation isolation
- Content hashing for payload uniqueness
- Tool catalogue records with canonical definitions

## Architecture Diagrams

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   User Agent    │────>│ Jungent Proxy    │────>│  Upstream       │
│                 │     │                  │     │  AI Provider    │
└─────────────────┘     └────────┬─────────┘     └────────┬─────────┘
                                 │                         │
                         ┌───────▼────────┐         ┌───────▼────────┐
                         │   Module       │         │  Active        │
                         │  Pipeline      │         │  Memory        │
                         └────────────────┘         └────────────────┘
```

## Phase Implementation Checklist

### Phase 0: Project Infrastructure ✓
- [x] Python project structure with pyproject.toml  
- [x] pytest for testing
- [x] ruff as linter
- [x] black as formatter
- [x] Virtual environment setup

### Phase 1: Structured Provider Contract ✓
- [x] All providers use canonical Request/Response models
- [x] Enable/disable state handling with tests
- [x] Response parsing through validated parsing
- [x] Legacy API deprecated but functional for backward compatibility

### Phase 2: Proxy Runtime ✓
- [x] Endpoints implemented (/health, /ready)
- [x] Conversation ID propagation in headers  
- [x] Graceful shutdown of HTTP clients
- [x] Packet ↔ ProviderRequest conversion

### Phase 3: Hammer & Scissors ✓
- [x] Typed actions (PASS/REWRITE/CUT) implemented
- [x] Module registration and ordered execution
- [x] Validation after every mutation
- [x] Failure policy configurable (fail-open/fail-close)
- [x] Audit events recorded

### Phase 4: Active Memory ✓
- [x] Storage interface defined
- [x] In-memory implementation with bounded size
- [x] Conversation isolation and expiry
- [x] Deterministic eviction tests

### Phase 5: Instruction Funnel ✓
- [x] Decision prompt implemented
- [x] Action tool schemas (PASS/REWRITE/CUT)  
- [x] Tool catalogue extraction
- [x] Relevant tool restoration
- [x] Noise reduction behavior
- [x] Error recovery
- [x] Context cutting
- [x] Three behavioral scenarios (A, B, C)

### Phase 6: Streaming ✓
- [x] Valid SSE behaviour implemented
- [x] Buffering when module requires complete content
- [x] Direct streaming only when all modules declare path safe
- [x] Unit and integration tests for non-streaming/multi-turn

### Phase 7: Documentation ✓
- [x] Comprehensive README with architecture diagrams
- [x] Deployment instructions
- [x] Troubleshooting guide

## Deployment Instructions

### Prerequisites

- Python 3.10+  
- pip / pyproject.toml for package management
- pytest for testing
- ruff and black for linting/formatting

### Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"     # Install with dev dependencies

pytest                      # Run all tests
ruff check src              # Lint check
black --check src           # Format check
```

### Running the Proxy

```bash
python -m src.jungent.proxy --port 8787 --provider openai --model gpt-4o
```

## Troubleshooting Guide

### Common Issues

1. **Provider not found**: Ensure upstream_provider is set correctly in config
2. **API key missing**: Set environment variable or pass api_key to provider constructor  
3. **Rate limit exceeded**: Add retry logic with exponential backoff
4. **Streaming issues**: Check that all modules declare streaming_safe=True
5. **Memory eviction**: Increase max_entries_per_conversation if needed

### Debugging Tips

- Enable logging: `LOGGING_LEVEL=DEBUG`  
- Use /health and /ready endpoints for liveness/readiness checks
- Check audit events in packet metadata for failed actions
