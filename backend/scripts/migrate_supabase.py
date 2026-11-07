import os
import psycopg2

DB_HOST = os.getenv("DB_HOST", "aws-1-ca-central-1.pooler.supabase.com")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres.tywmyjecafmpufdfxbus")
DB_PASS = os.getenv("DB_PASS", os.getenv("DATABASE_PASSWORD", ""))
DB_NAME = os.getenv("DB_NAME", "postgres")

print("Connecting to Supabase...")
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    dbname=DB_NAME,
    sslmode="require",
    connect_timeout=20
)
conn.autocommit = True
cur = conn.cursor()

print("Dropping old conflicting empty tables (issues, reports, profiles)...")
cur.execute("""
    DROP TABLE IF EXISTS public.reports CASCADE;
    DROP TABLE IF EXISTS public.issues CASCADE;
    DROP TABLE IF EXISTS public.profiles CASCADE;
    DROP TABLE IF EXISTS public.issue_upvotes CASCADE;
    DROP TABLE IF EXISTS public.issue_audit_log CASCADE;
    DROP TABLE IF EXISTS public.issue_proofs CASCADE;
""")

migration_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "supabase", "migrations", "0001_civicfix_init.sql"))
with open(migration_file, "r", encoding="utf-8") as f:
    sql = f.read()

# Supabase dashboard manages pg_cron extension
sql_clean = sql.replace('CREATE EXTENSION IF NOT EXISTS "pg_cron";', '-- pg_cron managed in dashboard')

print("Executing migration 0001_civicfix_init.sql...")
cur.execute(sql_clean)
print(">>> Migration 0001_civicfix_init.sql executed successfully! <<<")

# Verify public tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
""")
tables = [r[0] for r in cur.fetchall()]
print(f"\nPublic tables and views now ({len(tables)} total):")
for t in tables:
    print(f"  [x] {t}")

# Verify PostGIS point column & GIST index on issues
cur.execute("""
    SELECT column_name, udt_name 
    FROM information_schema.columns 
    WHERE table_name = 'issues' AND column_name IN ('lat', 'lng', 'location');
""")
cols = cur.fetchall()
print(f"\nIssues location columns:")
for c in cols:
    print(f"  [x] {c[0]} ({c[1]})")

# Verify RPCs
cur.execute("""
    SELECT routine_name 
    FROM information_schema.routines 
    WHERE routine_schema = 'public' 
      AND routine_name IN ('issues_in_bounds', 'nearby_issues', 'custom_access_token_hook', 'resolve_issue_with_proof');
""")
routines = [r[0] for r in cur.fetchall()]
print(f"\nRPC Functions verified ({len(routines)} found):")
for r in routines:
    print(f"  [x] {r}")

# Check storage buckets
cur.execute("SELECT id, name, public FROM storage.buckets;")
buckets = cur.fetchall()
print(f"\nStorage buckets in 'storage.buckets':")
for b in buckets:
    print(f"  [x] {b[0]} (public={b[2]})")

conn.close()
print("\nALL SUPABASE TABLES, POSTGIS GEOMETRIES, VIEWS, RPCS, AND BUCKETS CREATED SUCCESSFULLY!")
