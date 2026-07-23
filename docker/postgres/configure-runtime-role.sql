\set ON_ERROR_STOP on

-- Create/update a non-owner login used by the API and scheduler.
SELECT format(
    'CREATE ROLE %I LOGIN PASSWORD %L',
    :'app_db_user',
    :'app_db_password'
)
WHERE NOT EXISTS (
    SELECT 1 FROM pg_roles WHERE rolname = :'app_db_user'
)
\gexec

SELECT format(
    'ALTER ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',
    :'app_db_user',
    :'app_db_password'
)
\gexec

REVOKE CREATE, TEMPORARY ON DATABASE :"app_db_name" FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'app_db_name', :'app_db_user')
\gexec
SELECT format('GRANT USAGE ON SCHEMA public TO %I', :'app_db_user')
\gexec
SELECT format(
    'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO %I',
    :'app_db_user'
)
\gexec
SELECT format(
    'GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO %I',
    :'app_db_user'
)
\gexec

-- Alembic runs as the owner. Future tables/sequences inherit runtime grants.
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I',
    :'owner_user',
    :'app_db_user'
)
\gexec
SELECT format(
    'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO %I',
    :'owner_user',
    :'app_db_user'
)
\gexec
