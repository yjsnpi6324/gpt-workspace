# GPT Workspace Operating Model

## System role

`gpt-workspace` is the execution/integration layer around GPT. It should not duplicate Notion's task database or `ai-agent-lab`'s research corpus.

## Responsibilities

- Connector integrations
- Tool definitions and reusable tool wrappers
- Automation workflows
- GPT ↔ Notion ↔ GitHub synchronization patterns
- Runtime experiments
- Operational checks and integration tests

## Task → Skill → Agent

- **Task**: a concrete objective tracked operationally in Notion.
- **Skill**: a reusable capability with inputs, outputs, validation criteria and lifecycle status.
- **Agent**: an orchestrated worker that selects skills and tools to complete tasks.

## System loop

`Notion task → GPT planning → Skill/Tool execution → GitHub artifact or research update → validation → Notion state update`

## Boundary rules

Do not store secrets in GitHub. Do not make GitHub the source of truth for transient task state. Do not copy large amounts of Notion prose into code repositories unless it is durable technical knowledge or a reproducible specification.
