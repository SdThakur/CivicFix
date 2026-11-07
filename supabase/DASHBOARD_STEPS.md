# Supabase Dashboard Configuration Guide

This document specifies the required manual configuration steps in the Supabase Cloud / Project Dashboard (`https://supabase.com/dashboard/project/tywmyjecafmpufdfxbus`).

---

### 1. Enable Anonymous Sign-Ins
1. Navigate to **Authentication** -> **Providers** -> **Email & Anonymous**.
2. Scroll to the **Anonymous Sign-Ins** section.
3. Toggle **Enable Anonymous Sign-Ins** to **ON**.
4. Click **Save**.
   > *Purpose*: Allows citizens to report hazards instantly without prior friction or upfront password registration. The anonymous session can seamlessly link to an email account later while retaining their report history.

---

### 2. Custom Access Token (Auth Hook)
To ensure the user's role (e.g. `CITIZEN`, `STAFF`, `ADMIN`) is available directly inside `auth.jwt()` without querying the database on every RLS evaluation:
1. Navigate to **Authentication** -> **Hooks**.
2. Select **Custom Access Token (JWT) Hook**.
3. Choose **Postgres function**.
4. Set the function to:
```sql
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event jsonb)
RETURNS jsonb LANGUAGE plpgsql STABLE AS $$
DECLARE
  user_role TEXT;
BEGIN
  SELECT role INTO user_role FROM public.profiles WHERE id = (event->>'user_id')::uuid;
  
  -- Inject the role into the claims
  event := jsonb_set(event, '{claims,user_role}', to_jsonb(COALESCE(user_role, 'CITIZEN')));
  RETURN event;
END;
$$;
```
5. Grant execute permission to `supabase_auth_admin`:
```sql
GRANT EXECUTE ON FUNCTION public.custom_access_token_hook TO supabase_auth_admin;
REVOKE EXECUTE ON FUNCTION public.custom_access_token_hook FROM authenticated, anon, public;
```

---

### 3. Enable `pg_cron` & Schedule Automated Jobs
1. Navigate to **Database** -> **Extensions**.
2. Search for **`pg_cron`** and toggle it to **Active**.
3. In the **SQL Editor**, verify and activate the two background schedules defined in Section 14 of the migration:

```sql
-- Schedule 1: Stale Report Sweeper Recovery (Runs every 5 minutes)
-- Resets uncompleted reports stuck in PROCESSING for > 10 minutes to FAILED
SELECT cron.schedule(
    'civicfix_sweeper_recovery',
    '*/5 * * * *',
    $$SELECT public.recover_stale_reports();$$
);

-- Schedule 2: Refresh Public Analytics Materialized Views (Runs every 15 minutes)
SELECT cron.schedule(
    'civicfix_refresh_materialized_views',
    '*/15 * * * *',
    $$REFRESH MATERIALIZED VIEW CONCURRENTLY public.public_stats; REFRESH MATERIALIZED VIEW CONCURRENTLY public.public_category_stats;$$
);
```

---

### 4. Storage Buckets Verification
1. Navigate to **Storage** -> **Buckets**.
2. Verify the two buckets are created:
   * **`reports`**: Public: `ON` (Citizen photo uploads stored under `reports/<user_id>/<uuid>.webp`).
   * **`proofs`**: Public: `OFF` (Private verification photos accessible only via short-lived signed URLs for `RESOLVED` issues).

