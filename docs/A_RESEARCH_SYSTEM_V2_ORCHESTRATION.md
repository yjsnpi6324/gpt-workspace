# A-Research System V2 — GPT Orchestration

## Scope

This document defines the orchestration boundary for the two A-share prediction tasks.

## Independent task identities

- `A-CORE` — A股基本盘预测
- `A-AI` — A股AI板块预测

Each task has its own execution context and output namespace. Neither task may depend on the other task's chat history.

## Shared services

Both tasks use the same contracts for:

- data quality
- trading-calendar resolution
- prediction horizons
- GitHub Prediction Ledger
- Notion reconciliation
- validation
- Evaluation
- Self-Audit
- Champion/Challenger
- recovery

## Execution modes

### Trading day

`data → state → research → prediction → validation → canonical report → GitHub ledger → Notion → PDF → audit`

### Saturday

`weekly review → prediction validation → error attribution → next-week watch variables`

### Sunday

`next-week coarse outlook → scenarios → catalysts/risks → rough T+1/T+3/T+5 trading-day directions`

Weekend records are typed separately from formal trading-day predictions.

## Close gate

A task run is closed only when:

1. Canonical report exists.
2. Original prediction/review record is durable in GitHub.
3. Notion is synchronized or an explicit recovery/audit state is recorded.
4. Reconciliation has a documented status.
5. PDF is either delivered or its failure is recorded.

## V2 migration

V2 starts in shadow mode. Existing production task behavior remains the baseline until V2 passes reliability and evaluation gates.
