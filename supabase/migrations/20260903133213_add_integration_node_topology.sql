create table if not exists public.integration_nodes (
  id uuid primary key default gen_random_uuid(),
  node_key text not null unique,
  name text not null,
  provider text not null,
  node_type text not null,
  role text not null,
  status text not null default 'active' check (status in ('active','inactive','disabled','error')),
  capabilities jsonb not null default '[]'::jsonb,
  config jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.integration_events (
  id uuid primary key default gen_random_uuid(),
  source_node_id uuid references public.integration_nodes(id) on delete set null,
  target_node_id uuid references public.integration_nodes(id) on delete set null,
  task_id uuid references public.tasks(id) on delete set null,
  task_run_id uuid references public.task_runs(id) on delete set null,
  event_type text not null,
  status text not null default 'recorded' check (status in ('recorded','processed','failed','ignored')),
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_integration_events_source_created
  on public.integration_events(source_node_id, created_at desc);
create index if not exists idx_integration_events_target_created
  on public.integration_events(target_node_id, created_at desc);
create index if not exists idx_integration_events_task_run
  on public.integration_events(task_run_id);
create index if not exists idx_integration_events_type_created
  on public.integration_events(event_type, created_at desc);

-- Keep topology/event data private, with explicit backend access on every replay.
alter table public.integration_nodes enable row level security;
alter table public.integration_events enable row level security;
revoke all on table public.integration_nodes, public.integration_events
  from public, anon, authenticated, service_role;
grant select, insert, update, delete on table public.integration_nodes,
  public.integration_events to service_role;

insert into public.integration_nodes
  (node_key, name, provider, node_type, role, status, capabilities, metadata)
values
  ('supabase-core','Supabase','supabase','database_core','state_memory_data_hub','active',
   '["postgres","task_registry","run_history","results","memory","vector","integration_events"]'::jsonb,
   '{"position":"system_of_record"}'::jsonb),

  ('chatgpt-orchestrator','ChatGPT Agent','openai','agent_orchestrator','decision_and_orchestration','active',
   '["reasoning","planning","task_orchestration","tool_selection","research_synthesis"]'::jsonb,
   '{"position":"control_plane"}'::jsonb),

  ('notion-knowledge','Notion','notion','knowledge_base','human_readable_knowledge_and_project_workspace','active',
   '["search","fetch","pages","databases","comments"]'::jsonb,
   '{"position":"knowledge_plane"}'::jsonb),

  ('github-code','GitHub','github','code_repository','code_workflow_and_version_source','active',
   '["repositories","commits","branches","issues","pull_requests","workflow_logs"]'::jsonb,
   '{"position":"code_plane"}'::jsonb),

  ('dropbox-files','Dropbox','dropbox','file_storage','external_file_archive','active',
   '["files","folders","search","download_links","revisions","sharing"]'::jsonb,
   '{"position":"artifact_plane"}'::jsonb),

  ('canva-creative','Canva','canva','creative_engine','visual_design_production','active',
   '["designs","templates","generation","editing","assets","resize"]'::jsonb,
   '{"position":"creative_plane"}'::jsonb),

  ('apple-music','Apple Music','apple_music','media_catalog','music_catalog_and_playlist','active',
   '["music_search","track_details","playlists"]'::jsonb,
   '{"position":"specialized_capability"}'::jsonb),

  ('shazam','Shazam','shazam','media_intelligence','music_identification_and_discovery','active',
   '["music_recognition","music_search","charts","artists","songs"]'::jsonb,
   '{"position":"specialized_capability"}'::jsonb)

on conflict (node_key) do update set
  name = excluded.name,
  provider = excluded.provider,
  node_type = excluded.node_type,
  role = excluded.role,
  status = excluded.status,
  capabilities = excluded.capabilities,
  metadata = excluded.metadata,
  updated_at = now();
