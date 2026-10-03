create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  task_key text not null unique,
  name text not null,
  description text,
  category text not null default 'agent',
  status text not null default 'active' check (status in ('active','paused','archived')),
  schedule_config jsonb not null default '{}'::jsonb,
  config jsonb not null default '{}'::jsonb,
  current_prompt_version integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.prompt_versions (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.tasks(id) on delete cascade,
  version integer not null,
  prompt_text text not null,
  change_note text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  unique(task_id, version)
);

create table if not exists public.task_runs (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.tasks(id) on delete cascade,
  run_key text not null unique,
  trigger_type text not null default 'manual' check (trigger_type in ('manual','scheduled','backfill','retry','api')),
  status text not null default 'queued' check (status in ('queued','running','succeeded','failed','cancelled')),
  started_at timestamptz,
  finished_at timestamptz,
  model_info jsonb not null default '{}'::jsonb,
  input_snapshot jsonb not null default '{}'::jsonb,
  metrics jsonb not null default '{}'::jsonb,
  error_message text,
  created_at timestamptz not null default now()
);

create table if not exists public.task_results (
  id uuid primary key default gen_random_uuid(),
  task_run_id uuid not null references public.task_runs(id) on delete cascade,
  task_id uuid not null references public.tasks(id) on delete cascade,
  result_type text not null default 'primary',
  result_date date,
  title text,
  summary text,
  content jsonb not null default '{}'::jsonb,
  confidence numeric(5,4),
  created_at timestamptz not null default now()
);

create table if not exists public.memories (
  id uuid primary key default gen_random_uuid(),
  scope text not null default 'project' check (scope in ('global','project','task','user')),
  project_key text,
  task_id uuid references public.tasks(id) on delete cascade,
  memory_type text not null default 'fact',
  importance smallint not null default 5 check (importance between 1 and 10),
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding extensions.vector(1536),
  source_run_id uuid references public.task_runs(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.artifacts (
  id uuid primary key default gen_random_uuid(),
  task_run_id uuid references public.task_runs(id) on delete cascade,
  task_id uuid references public.tasks(id) on delete cascade,
  artifact_type text not null,
  name text not null,
  storage_path text,
  external_url text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_prompt_versions_task_version on public.prompt_versions(task_id, version desc);
create index if not exists idx_task_runs_task_created on public.task_runs(task_id, created_at desc);
create index if not exists idx_task_runs_status on public.task_runs(status);
create index if not exists idx_task_results_task_date on public.task_results(task_id, result_date desc);
create index if not exists idx_task_results_run on public.task_results(task_run_id);
create index if not exists idx_memories_task_created on public.memories(task_id, created_at desc);
create index if not exists idx_memories_scope_project on public.memories(scope, project_key);

-- These are private backend tables. Grants and RLS must survive a fresh replay
-- without Supabase's legacy default ACLs or the hosted ensure_rls event trigger.
alter table public.tasks enable row level security;
alter table public.prompt_versions enable row level security;
alter table public.task_runs enable row level security;
alter table public.task_results enable row level security;
alter table public.memories enable row level security;
alter table public.artifacts enable row level security;

revoke all on table public.tasks, public.prompt_versions, public.task_runs,
  public.task_results, public.memories, public.artifacts
  from public, anon, authenticated, service_role;
grant select, insert, update, delete on table public.tasks, public.prompt_versions,
  public.task_runs, public.task_results, public.memories, public.artifacts
  to service_role;

-- This hosted helper is not guaranteed to exist in a fresh local/preview DB.
-- Preserve its original protection when present; table RLS is explicit above.
do $migration$
begin
  if to_regprocedure('public.rls_auto_enable()') is not null then
    revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
  end if;
end;
$migration$;
