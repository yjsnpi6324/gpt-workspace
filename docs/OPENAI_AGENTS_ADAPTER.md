# Optional OpenAI Agents adapter

`runtime/contracts.py` remains the provider-neutral boundary. Its Task validation,
SUCCESS / FAILED invariants and four ErrorType values are unchanged.

`runtime/adapters/openai_agents.py` translates one async, non-streaming SDK run
into that contract. Agent, Runner, configuration and exception types are injected.
Importing the adapter uses only the standard library; `from_sdk` is an explicit,
lazy binding. There is no global client, API key lookup or automatic execution.

## Composition

The optional compatibility target is `openai-agents==0.23.1`. Install it only in
an adapter environment with `python -m pip install -r requirements-openai-agents.txt`.

```python
from agents import Agent, function_tool
from runtime.adapters.openai_agents import OpenAIAgentsAdapter, raise_tool_error
from runtime.contracts import Task

@function_tool(failure_error_function=raise_tool_error)
def lookup() -> str:
    """Return a verified local fixture."""
    return "verified metric"

# The application supplies its own model/client; no provider default is selected here.
agent = Agent(name="lookup", model=application_model, tools=[lookup])
adapter = OpenAIAgentsAdapter.from_sdk(agent=agent, max_turns=3)
result = await adapter.run(Task("lookup-1", "look up metric"))
```

The exact Task is passed as local SDK context, and Task.input as model input.
`from_sdk` disables tracing by default; an injected RunConfig is preserved.
`run` calls Task.validate before invoking the Runner. It accepts only a string
final_output from an uninterrupted run, including the empty string already
allowed by RunResult. Missing or structured outputs are failures, never coerced.

## Failure mapping

| Trigger | Existing ErrorType |
| --- | --- |
| Task validation failure | INVALID_INPUT |
| SDK UserError, API BadRequestError / UnprocessableEntityError | INVALID_INPUT |
| Owned ToolExecutionError, SDK ToolTimeoutError / MCPToolCancellationError | TOOL_ERROR |
| PermissionError, API authentication / permission errors | PERMISSION_DENIED |
| SDK input, output or tool guardrails; model refusal; pending tool approval | PERMISSION_DENIED |
| Turn limit, model behavior / timeout, malformed result, other exceptions | RUNTIME_ERROR |

Permissions take precedence over tool and input mappings. Explicit exception
causes are inspected because the SDK wraps tool failures in UserError; wrapped
tool and permission failures retain their category. Every failed RunResult has a
nonempty error message and no output. Cancellation, including wrapped
cancellation, propagates as control flow without inventing a result.

Owned function tools must inject `raise_tool_error`. The SDK's default tool error
formatter can turn an exception into text and allow the model to continue; the
adapter cannot infer a hidden exception from that text. For timed tools, also
choose `timeout_behavior="raise_exception"`. Callers retain ownership of tools,
handoffs and policies. This slice does not implement approval resume, streaming,
structured output conversion, persistence or retries.

## Deterministic validation

- `python -m unittest discover -s tests -p "test_*.py" -v`: standard-library
  contract and injected-runner tests; works without any provider SDK installed.
- `python -m unittest discover -s tests/sdk -p "test_*.py" -v`: optional real SDK
  binding and Runner tests using scripted models. No API key is supplied, tracing
  is disabled and socket connections are blocked and checked for attempted calls.

CI runs these as separate jobs. Neither suite calls a model API. The SDK suite
checks real tool failures, pending approvals and guardrails; the core suite
checks malformed outputs, typed mappings, cancellation and import isolation.

References: [SDK release v0.23.1](https://github.com/openai/openai-agents-python/releases/tag/v0.23.1),
[Runner](https://openai.github.io/openai-agents-python/ref/run/),
[exceptions](https://openai.github.io/openai-agents-python/ref/exceptions/),
[tool error handling](https://openai.github.io/openai-agents-python/tools/#handling-errors-in-function-tools).
