-- TEST DATABASES ONLY. Remove legacy defaults for the postgres creator.
-- In local Supabase Postgres 17, the postgres connection cannot ALTER DEFAULT
-- PRIVILEGES FOR ROLE supabase_admin (42501). The previous fixture failed before
-- replay and before the permission assertions could execute.
-- Do not run against production. The creation migrations independently revoke
-- client privileges and grant service_role CRUD for each of the eight tables.
alter default privileges for role postgres
  revoke all on tables from public, anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  revoke all on tables from public, anon, authenticated, service_role;
