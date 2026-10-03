-- TEST DATABASES ONLY. Remove global and schema defaults for both Supabase
-- migration creators. Never run this fixture against a production project.
alter default privileges for role postgres
  revoke all on tables from public, anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  revoke all on tables from public, anon, authenticated, service_role;
alter default privileges for role supabase_admin
  revoke all on tables from public, anon, authenticated, service_role;
alter default privileges for role supabase_admin in schema public
  revoke all on tables from public, anon, authenticated, service_role;
