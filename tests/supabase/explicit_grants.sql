-- Run only on a disposable local/preview database after migration replay.
-- All fixture rows and temporary GRANTs roll back; errors must stop the runner.
begin;

do $test$
declare
  table_name text;
  api_role text;
  privilege_name text;
  table_names constant text[] := array['tasks', 'prompt_versions', 'task_runs',
    'task_results', 'memories', 'artifacts', 'integration_nodes', 'integration_events'];
begin
  foreach table_name in array table_names loop
    if not exists (select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public' and c.relname = table_name and c.relrowsecurity) then
      raise exception 'Missing table or RLS: public.%', table_name;
    end if;
    if exists (select 1 from pg_policies where schemaname = 'public' and tablename = table_name) then
      raise exception 'Unexpected client policy on public.%', table_name;
    end if;
    foreach api_role in array array['anon', 'authenticated', 'service_role'] loop
      if not has_schema_privilege(api_role, 'public', 'USAGE') then
        raise exception 'Missing schema USAGE: %', api_role;
      end if;
      foreach privilege_name in array array['SELECT', 'INSERT', 'UPDATE', 'DELETE'] loop
        if has_table_privilege(api_role, format('public.%I', table_name), privilege_name)
          <> (api_role = 'service_role') then
          raise exception 'Unexpected % privilege for % on public.%', privilege_name, api_role, table_name;
        end if;
      end loop;
      foreach privilege_name in array array['TRUNCATE', 'REFERENCES', 'TRIGGER', 'MAINTAIN'] loop
        if has_table_privilege(api_role, format('public.%I', table_name), privilege_name) then
          raise exception 'Excess % privilege for % on public.%', privilege_name, api_role, table_name;
        end if;
      end loop;
    end loop;
  end loop;
  if exists (select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relkind = 'S') then
    raise exception 'New sequence needs an explicit access review';
  end if;
end;
$test$;

-- Exercise actual service-role DML, including UUID defaults and foreign keys.
set local role service_role;
insert into public.tasks (task_key, name) values ('__explicit_grants_test__', 'Grant test');
insert into public.prompt_versions (task_id, version, prompt_text)
  select id, 1, 'test' from public.tasks where task_key = '__explicit_grants_test__';
insert into public.task_runs (task_id, run_key)
  select id, '__explicit_grants_run__' from public.tasks where task_key = '__explicit_grants_test__';
insert into public.task_results (task_id, task_run_id)
  select task_id, id from public.task_runs where run_key = '__explicit_grants_run__';
insert into public.memories (task_id, content)
  select id, 'test' from public.tasks where task_key = '__explicit_grants_test__';
insert into public.artifacts (task_id, artifact_type, name)
  select id, 'test', 'test' from public.tasks where task_key = '__explicit_grants_test__';
insert into public.integration_nodes (node_key, name, provider, node_type, role)
  values ('__explicit_grants_node__', 'test', 'test', 'test', 'test');
insert into public.integration_events (task_id, source_node_id, event_type)
  select t.id, n.id, '__explicit_grants_event__' from public.tasks t, public.integration_nodes n
    where t.task_key = '__explicit_grants_test__' and n.node_key = '__explicit_grants_node__';
update public.tasks set name = 'updated' where task_key = '__explicit_grants_test__';
do $test$
begin
  if (select count(*) from public.tasks where task_key = '__explicit_grants_test__' and name = 'updated') <> 1 then
    raise exception 'Service role CRUD cannot reach the fixture row';
  end if;
end;
$test$;
reset role;

-- Missing ACLs must produce 42501 for both client roles, on all eight tables.
set local role anon;
do $test$
declare table_name text;
begin
  foreach table_name in array array['tasks', 'prompt_versions', 'task_runs', 'task_results',
    'memories', 'artifacts', 'integration_nodes', 'integration_events'] loop
    begin
      execute format('select 1 from public.%I limit 1', table_name);
      raise exception 'anon unexpectedly accessed public.%', table_name;
    exception when insufficient_privilege then null;
    end;
  end loop;
end;
$test$;
reset role;
set local role authenticated;
do $test$
declare table_name text;
begin
  foreach table_name in array array['tasks', 'prompt_versions', 'task_runs', 'task_results',
    'memories', 'artifacts', 'integration_nodes', 'integration_events'] loop
    begin
      execute format('select 1 from public.%I limit 1', table_name);
      raise exception 'authenticated unexpectedly accessed public.%', table_name;
    exception when insufficient_privilege then null;
    end;
  end loop;
end;
$test$;
reset role;

-- Prove RLS still blocks clients even if SELECT is temporarily granted.
grant select on public.tasks to anon, authenticated;
set local role anon;
do $test$
begin
  if exists (select 1 from public.tasks where task_key = '__explicit_grants_test__') then
    raise exception 'anon bypassed RLS';
  end if;
end;
$test$;
reset role;
set local role authenticated;
do $test$
begin
  if exists (select 1 from public.tasks where task_key = '__explicit_grants_test__') then
    raise exception 'authenticated bypassed RLS';
  end if;
end;
$test$;
reset role;
set local role service_role;
delete from public.integration_events where event_type = '__explicit_grants_event__';
delete from public.integration_nodes where node_key = '__explicit_grants_node__';
delete from public.tasks where task_key = '__explicit_grants_test__';
do $test$
begin
  if exists (select 1 from public.tasks where task_key = '__explicit_grants_test__') then
    raise exception 'Service role DELETE failed';
  end if;
end;
$test$;
reset role;
rollback;
