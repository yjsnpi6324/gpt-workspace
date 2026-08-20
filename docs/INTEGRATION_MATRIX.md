# Integration Matrix

| System | Primary responsibility | GitHub role |
|---|---|---|
| GPT | Reasoning, orchestration, research, decision-making and execution planning | Consumer / producer |
| Notion | Plans, tasks, projects, operational state and coordination | Sync target / source |
| Quantitative-Investment-Research-Lab | Research, methods, experiments, A-share research and durable technical knowledge | Research source |
| gpt-workspace | Tools, connectors, automations, runtime and integration code | Implementation layer |

## Data movement

1. Notion creates or updates an operational task.
2. GPT determines whether the task needs research, implementation, or both.
3. Research, methods, experiments and durable findings go to `Quantitative-Investment-Research-Lab`.
4. Tooling, integrations, automation and runtime code go to `gpt-workspace`.
5. Validation results are recorded with the relevant GitHub artifact.
6. GPT updates the operational state in Notion.

## Canonical-home principle

One durable piece of information should have one canonical home. Cross-system links should point to the canonical artifact instead of duplicating it.
