create index if not exists idx_integration_events_task_created on public.integration_events(task_id, created_at desc);
