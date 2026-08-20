# Current Technology Track

> Checked: 2026-08-21

## Priority technologies

### OpenAI Agents SDK

Track the current Agents SDK as a primary implementation route for code-based agent orchestration, long-running work, tool use and controlled sandbox execution. OpenAI's April 2026 update describes a model-native harness, native sandbox execution, and separation of harness from compute. Source: https://openai.com/index/the-next-evolution-of-the-agents-sdk/

### Model Context Protocol

Track MCP as a key interoperability layer. The July 28, 2026 specification introduced a stateless protocol core, multi-round-trip requests, header-based routing, cacheable list results, authorization hardening, extensions, Tasks, and a formal deprecation policy. Source: https://blog.modelcontextprotocol.io/posts/2026-07-28/

## Adoption rule

These technologies are tracked as current candidates, not automatic dependencies. Each should be tested against the actual GPT + Notion + GitHub workload before becoming a hard architectural requirement.

## Deprecation watch

OpenAI announced in June 2026 that Agent Builder and Evals are being wound down, with Agents SDK recommended for workflows that should continue as code. This repository therefore avoids building new core architecture around those retiring products.
