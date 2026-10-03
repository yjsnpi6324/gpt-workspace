create index if not exists idx_artifacts_task on public.artifacts(task_id);
create index if not exists idx_artifacts_run on public.artifacts(task_run_id);
create index if not exists idx_memories_source_run on public.memories(source_run_id);

-- Keep the tables private until an authenticated application/API layer is explicitly configured.
-- No broad anon/authenticated policies are added here.
