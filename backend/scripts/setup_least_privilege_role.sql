-- ==============================================================================
-- CivicFix Production Least-Privilege Database Role Setup
-- ==============================================================================
-- Creates a dedicated, unprivileged application role for the FastAPI backend,
-- replacing the postgres superuser in production connection strings.
-- ==============================================================================

-- 1. Create the application role if it does not already exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'civicfix_api') THEN
        CREATE ROLE civicfix_api WITH
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
            CONNECTION LIMIT 50
            PASSWORD 'civicfix_app_secure_pass_2026';
    END IF;
END$$;

-- 2. Grant Database connection rights
GRANT CONNECT ON DATABASE civicfix_db TO civicfix_api;

-- 3. Grant schema usage (strictly on public schema)
GRANT USAGE ON SCHEMA public TO civicfix_api;

-- 4. Grant DML rights on existing tables (NO DDL: DROP/ALTER/TRUNCATE forbidden)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO civicfix_api;

-- 5. Grant sequence usage for auto-incrementing primary keys
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO civicfix_api;

-- 6. Configure default privileges for future tables created by migrations
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO civicfix_api;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO civicfix_api;

-- 7. Verification Query
SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolconnlimit
FROM pg_roles
WHERE rolname IN ('civicfix_api', 'postgres');

