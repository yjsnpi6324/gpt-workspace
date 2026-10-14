# Supabase migration grants

## Source and ownership

The runtime/integration repository owns the Supabase data-hub migrations used by
the research system. Before this change neither repository contained SQL migration
sources. Five migrations were recovered read-only from
`maxbwlhkgxnniclontig.supabase_migrations.schema_migrations` on 2026-10-03.
Their existing versions and names are preserved. These are recovered historical
migrations, not newly generated migration timestamps. The online migration history
and production database were not modified.

Supabase enforces explicit access for newly created public tables from 2026-10-30.
Existing objects retain their ACLs. Historical migrations replayed into a fresh
preview or reset database create new objects, so they need the same explicit ACLs.
See the [official announcement](https://github.com/orgs/supabase/discussions/45329)
and [Data API security guide](https://supabase.com/docs/guides/api/securing-your-api).

## Minimal source changes

| Migration under `supabase/migrations/` | Tables | Difference from recovered source |
| --- | --- | --- |
| `20260903132909_enable_vector_extension.sql` | None | Unchanged SQL |
| `20260903132922_initialize_ai_agent_data_hub_v1.sql` | tasks, prompt_versions, task_runs, task_results, memories, artifacts | Explicit RLS, per-table service CRUD and client revokes; guard the existing helper-function revoke when the hosted helper is absent |
| `20260903132935_add_missing_foreign_key_indexes.sql` | None | Unchanged SQL |
| `20260903133213_add_integration_node_topology.sql` | integration_nodes, integration_events | Explicit RLS, per-table service CRUD and client revokes before the existing topology insert |
| `20260903133554_add_integration_events_task_index.sql` | None | Unchanged SQL |

All column definitions, constraints, indexes and original topology values stay the
same. RLS has no client policies, matching the existing private-backend access
intent documented in the recovered foreign-key-index migration. No sequences
exist: UUID keys use `gen_random_uuid()`. No blanket future default grants or
`ON ALL TABLES` grants are added.

## Permission difference for the eight data-hub tables

| Role | Existing online ACL (unchanged) | Unpatched replay without auto-grants | Repaired replay |
| --- | --- | --- | --- |
| anon | CRUD plus legacy extra privileges; no client RLS policies | No table privileges | Explicitly no table privileges |
| authenticated | CRUD plus legacy extra privileges; no client RLS policies | No table privileges | Explicitly no table privileges |
| service_role | CRUD plus legacy extra privileges; BYPASSRLS | No table privileges; Data API operations fail with 42501 | SELECT, INSERT, UPDATE, DELETE only; existing BYPASSRLS behavior |

The creation migrations revoke table privileges from PUBLIC and the three roles
before granting exactly service CRUD. This makes both legacy-default and new-default
replays deterministic. Public-schema USAGE remains a Supabase platform prerequisite.
Client access requires a deliberate future grant and a matching RLS policy; adding
a grant alone does not expose rows.

Already-applied versions are skipped on an existing linked database, so editing
the recovered files fixes fresh/replayed environments and does not silently change
existing production permissions. A separately reviewed forward migration would be
needed to deliberately tighten existing objects. Do not repair migration history,
reapply old versions, or reset a linked production database for this change.

## Verification

`tests/supabase/explicit_grants.sql` checks 192 role/privilege combinations, RLS,
schema USAGE, UUID defaults and foreign keys, actual service-role DML, 16 client
SELECT denials, and RLS row invisibility after temporary SELECT grants. Fixture
rows and temporary permissions roll back. The default-revoke fixture is restricted
to disposable test databases.

The GitHub workflow pins Supabase CLI 2.119.0 and Postgres major version 17. It runs
a reset through the extension migration, removes automatic grants before any table
is created, applies the remaining migrations, and checks permissions. It then runs
a full `db reset --local --no-seed` and repeats the checks.

For a disposable hosted preview with these versions already applied, editing old
files will not rerun them. Recreate the preview from the repaired migration sources
or use a separately reviewed forward patch. For a fresh preview, replay all five
migrations, then run the same SQL checks. Do not reset a branch containing needed
data. The project had no existing preview branches on 2026-10-03; no paid branch
was created during this audit.

The local fallback used PGlite 0.5.8 (Postgres 18.3) with pgvector 0.0.9. Eight
scenarios passed: original-source 42501 and missing-helper 42883 controls, repaired
replays under new and legacy defaults, helper present/absent, two schema rebuilds,
and removing each creation migration's GRANT. This verifies database semantics;
it is distinct from the workflow's real Supabase/Postgres 17 reset and a hosted
preview. Machine-readable results are in
`docs/evidence/supabase-grants-20261003.json`.

## Recovered-source SHA-256

Hashes cover each original statement list joined with LF, trimmed, and terminated
with one LF. Only the two creation files have intentional SQL changes above.

| Version | Original SHA-256 |
| --- | --- |
| 20260903132909 | 594a2e965c9ad145469fc378cf7b6f109d661dfa5037f99c9c0e229e83612d10 |
| 20260903132922 | 689754eb7bffa87d7566ae465225030ea8940e02ea8c90b644ac055d72138a0b |
| 20260903132935 | 2c80313fb80bba280e123e2ae85e4c1acdfd5798354370182ccc8e347c4e1151 |
| 20260903133213 | 2d6249e6f97585648c2cc6480b39168d027f90cbf24a7a63171beda34a2bf229 |
| 20260903133554 | 0a6bd3c17144aaf074a32431ab2a0393bc04d1d307faf89d23853fa065dec43e |
