# Contributing

## Change policy

Use the smallest change that solves the actual problem. Preserve existing history and important configuration.

## Branches

Use one of:

- `feature/<name>`
- `chore/<name>`
- `research/<name>`
- `experiment/<name>`
- `fix/<name>`

Do not develop directly on `main` for important changes.

## Commit messages

Prefer concise, action-oriented messages such as:

- `feat: add research workflow runner`
- `docs: clarify skill lifecycle`
- `fix: handle connector timeout`
- `chore: update workspace configuration`

## Validation

Before opening a PR:

1. Check changed files and the diff.
2. Run available tests, linters, formatters, or configuration validation.
3. Confirm no secrets or local state were introduced.
4. Explain remaining risks in the PR.

## Repository boundary

Reusable GPT engineering belongs here. Quantitative models, factors, backtests, and portfolio research belong in `Quantitative-Investment-Research-Lab`.
