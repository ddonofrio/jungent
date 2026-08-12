# Hammer & Scissors Module

Hammer & Scissors is a deterministic interception engine that moves packets between the agent and provider, invokes installed modules in order, validates their requested actions, applies those actions, and records an audit trace.

## Product Metaphor

- **Hammer**: Approves or modifies packets (`pass_packet`, `rewrite_packet`)
- **Scissors**: Cuts obsolete context elements (`cut_context`)

## Design Principles

1. Deterministic interception - not an evaluator
2. No task-quality evaluation
3. No provider-specific reasoning
4. All modules must return exactly one valid action tool call

## Packet Actions

| Action | Metaphor | Behavior |
| --- | --- | --- |
| `pass` | Approved hammer | Forward unchanged |
| `rewrite` | Rejected hammer | Modify selected fields, then forward |
| `cut` | Scissors | Remove context elements by stable ID |

## Module Interface

```python
class Module:
    """Base class for pipeline modules."""
    
    name: str = "base_module"
    version: str = "1.0.0"
    supported_directions: List[ProxyDirection]
    streaming_safe: bool = False
    
    async def process(
        self,
        packet: Packet,
        context: PipelineContext,
    ) -> Action:
        """Process a packet and return an action."""
```

## Lifecycle Hooks

Modules receive:
- Read-only packet view
- Conversation state
- Active-memory access
- Cancellation deadline

Modules must not:
- Mutate shared state directly
- Call transport internals (prevents recursion)

## Failure Policy

Configurable via `module_failure_mode`:
- `open` (default): Record error, forward last valid packet
- `fail`: Stop pipeline on first failure

## Recursion Bypass

Internal module model calls bypass the proxy pipeline using a direct provider channel marked as internal. This prevents infinite recursion loops.

## Audit Events

Every mutation records:
- Action type
- Selected IDs (messages/tools)
- Tool names restored/removed
- Size before and after
- Duration
- Module version
- Concise machine-oriented reason
