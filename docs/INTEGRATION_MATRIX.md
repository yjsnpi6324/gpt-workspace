# Integration Matrix

| System | Primary responsibility | GitHub role |
|---|---|---|
| GPT | Reasoning, orchestration, research and execution | Consumer/producer |
| Notion | Plans, tasks, projects, state | Sync target/source |
| ai-agent-lab | Research, methods, experiments, durable technical knowledge | Research source |
| gpt-workspace | Tools, connectors, automations, runtime integrations | Implementation layer |

## Data movement

1. Notion creates or updates an operational task.
2. GPT determines whether the task needs research, implementation, or both.
3. Research and durable findings go to `ai-agent-lab`.
4. Tooling and integration code go to `gpt-workspace`.
5. Validation results are recorded with the relevant artifact.
6. GPT updates the operational state in Notion.

## Principle

One piece of information should have one canonical home. Cross-system links should point to the canonical artifact instead of duplicating it.
