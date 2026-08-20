# Integration Matrix

| System | Primary responsibility | GitHub role |
|---|---|---|
| GPT | Reasoning, research, decision-making and orchestration | Consumer / producer |
| Project | Current project context | Context source |
| Task | Recurring or triggered execution | Execution trigger |
| Notion | Plans, tasks, project state, prediction history, evaluations and change logs | Structured state source |
| File Library | Research materials, rules, Skill definitions and historical files | Source material |
| gpt-workspace | Prompts, Skills, workflows, automations, tooling and integrations | Engineering implementation |
| Quantitative-Investment-Research-Lab | Factors, models, experiments, backtests and validation | Quant research implementation |

## Data movement

1. A Project or Task establishes the execution context.
2. GPT decides whether the work needs research, engineering, or quantitative experimentation.
3. Reusable GPT tooling and workflow changes go to `gpt-workspace`.
4. Quantitative experiments and models go to `Quantitative-Investment-Research-Lab`.
5. Durable structured results and evaluation history are recorded in Notion.
6. GPT uses those validated artifacts in subsequent research and execution.

## Canonical-home principle

One piece of information should have one canonical home. Cross-system links should point to the canonical artifact instead of duplicating it.
