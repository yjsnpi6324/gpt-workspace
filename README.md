# GPT Workspace

> GPT / ChatGPT 工作体系工程主仓。

## Project role

`gpt-workspace` is the reusable engineering layer for the GPT-driven work system. It defines and implements how GPT, Project, Task, Notion, Memory, File Library, skills, prompts, workflows, and automations work together.

This repository is **not** the A-share quantitative model lab and is **not** a replacement for Notion or the File Library.

## System boundaries

- **GPT** — reasoning, research, decision-making, orchestration, and execution planning.
- **Project** — current project context and working scope.
- **Task** — recurring or triggered execution units.
- **Notion** — long-term structured records, project/task state, prediction history, model evaluation, and change logs.
- **File Library** — research materials, rules, skill definitions, and historical files.
- **GitHub / gpt-workspace** — reusable engineering assets, prompts, skills, workflows, automation, configuration, and technical documentation.
- **GitHub / Quantitative-Investment-Research-Lab** — quantitative research, experiments, models, factors, backtests, and validation.

## Current engineering scope

- GPT work patterns and orchestration
- Prompt and skill specifications
- Research Agent operating conventions
- Project / Task execution workflows
- Notion ↔ GitHub coordination patterns
- Automation and integration experiments
- Reusable technical documentation and configuration

## Development principles

- Keep components small and composable.
- Prefer explicit interfaces and reproducible workflows.
- Do not store secrets or transient task state in GitHub.
- Avoid coupling the whole workspace to a single model provider or framework unless the dependency is justified.
- Validate reusable skills and workflows before promotion to the stable path.

## Relationship to quantitative research

`gpt-workspace` can define how GPT launches, monitors, and records quantitative research work, but quantitative models and factor experiments belong in `Quantitative-Investment-Research-Lab`.

The expected flow is:

`Task → GPT planning → Skill / workflow execution → Quant research or engineering artifact → validation → Notion record`

## Status

**Phase 1 — engineering baseline.**

The repository is being evolved from an integration workspace into the reusable GPT engineering layer described above. Structure should grow only when real implementation needs appear.
