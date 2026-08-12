# Instruction Funnel Module

Instruction Funnel is an LLM-assisted Hammer & Scissors module that reduces instruction and context load while preserving everything needed for the agent's current work.

## Objective

Reduce irrelevant instructions and noisy history without judging whether the coding task was completed correctly.

## Behaviors

### 1. Instruction Classification

Classify incoming instruction material into:
- Stable identity/personality
- Active user objective
- Reusable operational instructions
- Tool catalogue
- Recent task state
- Tool results
- Obsolete noise

Preserve system-level authority and message order.

### 2. Tool Catalogue Extraction

Detect tool schemas in API tool fields or embedded instruction text. Store complete canonical definitions in conversation-scoped active memory using stable names and content hashes.

Never permanently delete the only copy until storage succeeds.

### 3. Relevant Tool Restoration

For each user objective, select the smallest sufficient subset of stored tools and attach their full definitions to the provider-bound request. Never invent a tool or expose unavailable client agent tools.

### 4. Noise Reduction

Rewrite provider-bound context to remove:
- Unrelated tool catalogues
- Repeated instructions
- Redundant status chatter
- Superseded attempts

Keep:
- Active objective and constraints
- Necessary file/environment facts
- Unresolved errors
- Minimum causal chain for correct tool use

### 5. Failed-attempt Repair

Recognize actionable tool errors and rewrite context into concise recovery instruction. The task model emits the actual next agent tool call; Instruction Funnel does not claim commands succeeded before corresponding tool result arrives.

### 6. Context Cutting

After a corrected attempt supersedes a failed one, request `cut_context` for obsolete assistant tool calls and paired tool results. Preserve compact factual replacements when removed events contain information still required by the task.

## Decision Trace

Record:
- Action type (pass/rewrite/cut)
- Selected IDs
- Tool names restored/removed
- Size before/after
- Duration
- Module version
- Concise machine-oriented reason

Never log secrets, full API keys, authorization headers, or unredacted sensitive payloads.

## Behavioral Scenarios

### Scenario A: Large Initial Prompt

Given an initial request with ~10K-token context containing ~7K tokens of tool descriptions and user message `Hello`:
- **Expected**: Persist tool catalogue in active session memory, rewrite provider-bound request to contain governing personality/instructions and greeting without irrelevant tool payload
- **Normal greeting response**: Pass unchanged

### Scenario B: Work-order Request

Given the next user message `Look in the directory, find OT.md, and execute it`:
- **Expected**: Rewrite provider-bound request to include unchanged user request plus only stored filesystem, file-reading, editing, shell, and validation tools required by configured agent environment

### Scenario C: PowerShell Recovery

Given an assistant tool call containing:
```powershell
.\script\start-vite.ps1
```
and paired tool result with `PSSecurityException` error, Instruction Funnel must rewrite context with recovery instruction to retry using:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\script\start-vite.ps1
```

After corrected tool result arrives, cut superseded failing call/result pair while retaining corrected pair and any still-relevant facts.

## Active Memory Interface

Async `ActiveMemoryStore` contract:
- Operations to put, get, list, delete conversation-scoped entries
- Each entry includes type, stable key, content hash, canonical payload, creation time, last-used time, relevance metadata
- Conversation-isolated and cleared on session expiry
- No persistence across process restarts (MVP)

Store tool schemas separately from compact conversation facts for future indexing strategies.
