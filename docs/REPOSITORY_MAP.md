# Repository Map

This repository is the durable **GPT runtime, integration, orchestration and skills layer** for the broader research operating system.

## Directory responsibilities

- `docs/` — runtime architecture, integration contracts and operating notes.
- `skills/` — reusable reasoning/agent skills intended for the workspace layer.

## System boundary

This repository does **not** own the quantitative research truth or prediction evaluation datasets. Those belong to `Quantitative-Investment-Research-Lab` and the Notion control plane.

It owns:

- GPT ↔ Notion ↔ GitHub integration
- Task/automation orchestration contracts
- runtime workflows and handoffs
- reusable workspace skills
- delivery/integration diagnostics

## Research handoff

`Project → Task → gpt-workspace orchestration → Quantitative-Investment-Research-Lab experiment → Evaluation → Notion → next Task`

Do not duplicate research content here. Store orchestration/status references and link to the research repository instead.

## Delivery boundary

Chat and PDF are presentation layers. A failed delivery must not destroy research or evaluation assets. Canonical Report content must be reproducible from durable records.
