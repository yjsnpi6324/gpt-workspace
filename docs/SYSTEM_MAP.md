# System Map

## Role
`gpt-workspace` is the engineering and integration layer for the GPT / ChatGPT work system.

## Responsibilities
- GPT-facing utilities and reusable tools
- Prompt and Skill specifications
- Project / Task execution workflows
- Connector and external-service integration
- Automation workflows
- Runtime configuration
- Integration tests and technical documentation

## System boundaries

- GPT owns reasoning, research, decisions, and orchestration.
- Project owns current working context.
- Task owns recurring or triggered execution.
- Notion owns durable structured state and historical records.
- File Library owns research materials, rules, and reusable source files.
- `gpt-workspace` owns reusable GPT engineering assets.
- `Quantitative-Investment-Research-Lab` owns quantitative models, factors, experiments, backtests, and validation.

## Quality loop

`design → implement → test → validate → document → integrate → maintain`
