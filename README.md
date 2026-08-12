# Jungent

**Jungent gives your agent wings.**

Jungent is a code assistant built around one uncompromising idea: use cutting-edge technology all the time.

Most coding agents are designed around stability. Their foundations, models, tools, and orchestration layers inevitably age while the field moves forward. Jungent takes the opposite approach. It is designed to adopt the latest useful advances in AI-assisted software engineering as soon as they become viable.

## Why Jungent?

AI engineering is evolving too quickly for a conventional release model. New models, inference techniques, agent architectures, context-management strategies, tool protocols, and evaluation methods appear constantly. Jungent exists to turn those advances into a working code assistant without waiting for them to become yesterday's safe default.

The name combines **young** with **agent**: an agent whose technology never grows old.

## Project Stage: Bleeding Edge

Jungent is intentionally classified as **bleeding edge**.

This is not a temporary phase on the way to a frozen stable branch. The project will evolve too quickly for long-term stabilization to be its primary goal. Components may be replaced whenever a materially better approach becomes available, and the architecture will remain open to continuous change.

Bleeding edge, however, does not mean careless. Jungent applies senior-level quality engineering and AI expertise to control the risks created by rapid evolution. Every significant change is expected to pass automated testing, regression analysis, capability evaluation, and practical validation before it becomes part of the trusted working system.

## The Promise

Jungent aims to offer access to the newest effective technology while earning the same operational confidence developers place in the stable releases of established coding agents such as **OpenAI Codex**, **Anthropic Claude Code**, and **Google Gemini CLI**.

That confidence will be built through evidence rather than release labels:

- Continuous functional, integration, and regression testing
- Model and agent capability evaluations
- Reproducible benchmarks for critical workflows
- Explicit tracking of behavioural and performance changes
- Fast rollback when a new component fails to meet its quality threshold
- Human validation informed by extensive QA and AI engineering experience

## Core Principles

1. **Always current.** Adopt meaningful advances quickly.
2. **Quality is engineered.** Trust comes from verification, not from age.
3. **Replace without nostalgia.** No component is permanent when a better one exists.
4. **Measure real capability.** Prefer reproducible results over marketing claims.
5. **Move fast without guessing.** Rapid change must remain observable, testable, and reversible.

## Status

Jungent is under active development. Interfaces, dependencies, behaviours, and internal architecture may change frequently as the project follows the frontier of AI-assisted software engineering.

## Proxy Mode

**Jungent gives your agent wings.**

Proxy Mode lets a coding agent use a configured AI provider through a local, protocol-compatible proxy while Jungent improves the information exchanged in both directions.

The implementation must address these baseline findings before or as part of the MVP:

- pytest -q passes: 89 tests.
- ruff check . fails with four findings, and the Ruff configuration uses deprecated top-level lint keys.
- black --check . reports six files that require formatting.
- Generated __pycache__, .pyc, and src/jungent.egg-info files are tracked. Add a .gitignore and remove generated artefacts from version control.
- Both LICENSE and LICENSE.txt contain the GPLv3 text. Retain one canonical license file.
- Documentation claims support for more than 30 providers although only three adapters exist.
- The documented Anthropic example uses a model identifier rejected by the implementation.
- The documentation declares list_models as asynchronous, while the code implements it synchronously.
- check_health and is_api_key_valid do not contact the provider and therefore do not validate connectivity or credentials as their names and documentation imply.
- Provider response parsing bypasses the existing safe parsing helper.
- ProviderConfig.enable_provider and ProviderRegistry.enable_provider do not correctly reconcile an existing allowlist or denylist in every case.
- The current prompt: str -> response: str provider contract cannot preserve message history, tool calls, tool results, structured content, usage, finish reasons, unknown protocol fields, or streaming. It must not be used as the proxy transport contract.
- There is no executable server, CLI entry point, CI workflow, integration-test layer, or end-to-end proxy test.

The implementation sequence:

### Phase 0: Make the baseline trustworthy

- Add .gitignore; untrack caches, bytecode, egg metadata, and other generated files.
- Remove the duplicate license filename while preserving GPLv3.
- Fix all Ruff and Black failures and migrate Ruff settings to [tool.ruff.lint].
- Correct provider documentation so that it matches the three implemented adapters and exact synchronous/asynchronous interfaces.
- Fix provider enable/disable state handling and add regression tests.
- Route all provider response parsing through validated parsing.
- Add CI for supported Python versions running tests, Ruff, and Black.

### Phase 1: Structured provider contract

- Add canonical message, tool, request, response, usage, and streaming models.
- Refactor the three providers to translate between canonical and native formats.
- Preserve the old string API only as a compatibility shim with deprecation documentation.
- Add provider contract tests with recorded synthetic fixtures and no live credentials.

### Phase 2: Proxy runtime

- Add configuration, CLI entry point, server lifecycle, health/readiness endpoints, conversation identity, request limits, structured errors, and graceful HTTP-client shutdown.
- Implement OpenAI-compatible ingress and response encoding.
- Add stub-upstream integration tests for normal text and multi-turn tool calls.

### Phase 3: Hammer & Scissors

- Implement packet envelopes, module registration, ordered execution, typed actions, validation, failure policy, audit events, and recursion bypass for internal calls.
- Add unit and integration tests for every direction and action.

### Phase 4: Active memory

- Implement the storage interface, bounded in-memory adapter, conversation isolation, expiry, and tool-catalogue records.
- Add deterministic tests for isolation, hashing, replacement, and eviction.

### Phase 5: Instruction Funnel

- Implement the fixed decision prompt, action tool schemas, classification, tool extraction, relevance selection, noise reduction, error recovery, and context cutting.
- Add deterministic decision-provider fixtures and the three required behavioural scenarios.

### Phase 6: Streaming and hardening

- Implement valid SSE behaviour. Buffer when a module requires complete content; stream directly only when every active module declares the path safe.
- Add disconnect cancellation, backpressure, timeouts, retry policy, redaction, concurrency tests, and malformed-payload tests.
- Benchmark added latency, context reduction, and memory growth with reproducible fixtures.

### Phase 7: Documentation and release readiness

- Update README.md with Proxy Mode positioning and the line Jungent gives your agent wings.
- Add docs/proxy-mode.md, docs/hammer-and-scissors.md, docs/instruction-funnel.md, and a complete configuration reference.
- Document a coding-agent setup example, a direct curl example, supported and unsupported protocol features, troubleshooting, and the module-extension contract.
- Add a changelog entry and upgrade notes for the provider API refactor.
