-- =============================================================================
-- Migration: 0001_civicfix_init.sql
-- Description: Core Schema, PostGIS, RLS, Triggers, RPCs, Views & Cron Schedules
-- =============================================================================

-- ─── SECTION 1: EXTENSIONS ───────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";
-- Note: In Supabase cloud / dashboard, pg_cron is enabled via Database -> Extensions
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- ─── SECTION 2: PROFILES & USER RBAC ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'CITIZEN' CHECK (role IN (
        'CITIZEN', 'STAFF', 'MANAGER', 'DISPATCHER', 'INSPECTOR', 'FIELD_WORKER', 'ADMIN'
    )),
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- Protect role escalation: Citizens cannot alter their own role
CREATE OR REPLACE FUNCTION public.check_profile_role_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.role IS DISTINCT FROM OLD.role) THEN
        -- Only service_role or admin can modify roles
        IF (current_setting('request.jwt.claim.role', true) != 'service_role' AND
            COALESCE((SELECT role FROM public.profiles WHERE id = auth.uid()), '') != 'ADMIN') THEN
            RAISE EXCEPTION 'Citizens and non-admin users are strictly forbidden from altering user roles.';
        END IF;
    END IF;
    NEW.updated_at = timezone('utc', now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_profile_role_guard ON public.profiles;
CREATE TRIGGER trg_profile_role_guard
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.check_profile_role_guard();

-- Auto-create profile on auth.users signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'Citizen'),
        COALESCE(NEW.raw_user_meta_data->>'role', 'CITIZEN')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ─── SECTION 3: ISSUES TABLE ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tracking_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'SUBMITTED' CHECK (status IN (
        'SUBMITTED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'CANCELLED'
    )),
    priority_level TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (priority_level IN (
        'LOW', 'MEDIUM', 'HIGH', 'URGENT'
    )),
    priority_score NUMERIC(5,2) NOT NULL DEFAULT 50.00,
    score_factors JSONB NOT NULL DEFAULT '{}'::jsonb,
    lat DOUBLE PRECISION NOT NULL CHECK (lat >= -90.0 AND lat <= 90.0),
    lng DOUBLE PRECISION NOT NULL CHECK (lng >= -180.0 AND lng <= 180.0),
    location GEOMETRY(Point, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lng, lat), 4326)) STORED,
    address TEXT,
    neighborhood TEXT,
    department_code TEXT DEFAULT 'DPW',
    upvotes INTEGER NOT NULL DEFAULT 0 CHECK (upvotes >= 0),
    duplicate_count INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_count >= 0),
    before_photo_path TEXT,
    after_photo_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_issues_location ON public.issues USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_issues_status ON public.issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_category ON public.issues(category);
CREATE INDEX IF NOT EXISTS idx_issues_priority_score ON public.issues(priority_score DESC);

-- ─── SECTION 4: REPORTS TABLE (ASYNC CITIZEN INGESTION) ──────────────────────
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    issue_id UUID REFERENCES public.issues(id) ON DELETE SET NULL,
    image_path TEXT NOT NULL,
    lat DOUBLE PRECISION NOT NULL CHECK (lat >= -90.0 AND lat <= 90.0),
    lng DOUBLE PRECISION NOT NULL CHECK (lng >= -180.0 AND lng <= 180.0),
    location GEOMETRY(Point, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lng, lat), 4326)) STORED,
    description TEXT,
    category TEXT,
    ai_confidence NUMERIC(4,2),
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN (
        'PENDING', 'PROCESSING', 'DONE', 'FAILED', 'DUPLICATE'
    )),
    error_message TEXT,
    is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
    duplicate_of_id UUID REFERENCES public.reports(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON public.reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_location ON public.reports USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at DESC);

-- ─── SECTION 5: ISSUE TIMELINE ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.issue_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES public.issues(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    actor_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_timeline_issue_id ON public.issue_timeline(issue_id, created_at ASC);

-- ─── SECTION 6: ISSUE UPVOTES ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.issue_upvotes (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    issue_id UUID NOT NULL REFERENCES public.issues(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    PRIMARY KEY (user_id, issue_id)
);

CREATE INDEX IF NOT EXISTS idx_issue_upvotes_issue ON public.issue_upvotes(issue_id);

-- ─── SECTION 7: AUDIT LOG (STRICTLY APPEND-ONLY) ─────────────────────────────
CREATE TABLE IF NOT EXISTS public.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_name TEXT NOT NULL,
    entity_id UUID NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'RESOLVE', 'MERGE', 'STATUS_CHANGE')),
    old_data JSONB,
    new_data JSONB,
    performed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON public.audit_log(entity_name, entity_id);

-- Append-only guard trigger for audit_log
CREATE OR REPLACE FUNCTION public.audit_log_immutable_guard()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only. UPDATE and DELETE actions are strictly prohibited.';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_audit_log_immutable ON public.audit_log;
CREATE TRIGGER trg_audit_log_immutable
    BEFORE UPDATE OR DELETE ON public.audit_log
    FOR EACH ROW
    EXECUTE FUNCTION public.audit_log_immutable_guard();

-- ─── SECTION 8: PRIORITY RECOMPUTE ENGINE ─────────────────────────────────────
CREATE OR REPLACE FUNCTION public.recompute_issue_priority(p_issue_id UUID)
RETURNS VOID AS $$
DECLARE
    v_cat TEXT;
    v_created_at TIMESTAMPTZ;
    v_upvotes INT;
    v_duplicates INT;
    v_cat_weight NUMERIC(5,2) := 15.00;
    v_age_boost NUMERIC(5,2) := 0.00;
    v_upvote_boost NUMERIC(5,2) := 0.00;
    v_cluster_boost NUMERIC(5,2) := 0.00;
    v_final_score NUMERIC(5,2);
    v_priority_level TEXT;
    v_factors JSONB;
BEGIN
    SELECT category, created_at, upvotes, duplicate_count
    INTO v_cat, v_created_at, v_upvotes, v_duplicates
    FROM public.issues
    WHERE id = p_issue_id;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    -- Category baseline weights
    IF v_cat IN ('Traffic Signal Outage', 'TRAFFIC_SIGNAL') THEN
        v_cat_weight := 40.00;
    ELSIF v_cat IN ('Water Main Leak / Flooding', 'WATER_LEAK') THEN
        v_cat_weight := 35.00;
    ELSIF v_cat IN ('Pothole & Road Damage', 'POTHOLE') THEN
        v_cat_weight := 25.00;
    ELSIF v_cat IN ('Broken Streetlight', 'STREETLIGHT') THEN
        v_cat_weight := 20.00;
    ELSIF v_cat IN ('Overflowing Trash / Illegal Dumping', 'TRASH') THEN
        v_cat_weight := 15.00;
    ELSIF v_cat IN ('Damaged Sidewalk', 'SIDEWALK') THEN
        v_cat_weight := 15.00;
    ELSIF v_cat IN ('Graffiti & Vandalism', 'GRAFFITI') THEN
        v_cat_weight := 10.00;
    ELSE
        v_cat_weight := 10.00;
    END IF;

    -- Age boost: 0.5 per day, max 20
    v_age_boost := LEAST(20.00, ROUND(EXTRACT(EPOCH FROM (timezone('utc', now()) - v_created_at)) / 86400.0 * 0.5, 2));
    -- Upvote boost: 2 pts per upvote, max 20
    v_upvote_boost := LEAST(20.00, v_upvotes * 2.00);
    -- Duplicate cluster boost: 5 pts per duplicate, max 20
    v_cluster_boost := LEAST(20.00, v_duplicates * 5.00);

    v_final_score := LEAST(100.00, v_cat_weight + v_age_boost + v_upvote_boost + v_cluster_boost);

    IF v_final_score >= 80.00 THEN
        v_priority_level := 'URGENT';
    ELSIF v_final_score >= 60.00 THEN
        v_priority_level := 'HIGH';
    ELSIF v_final_score >= 30.00 THEN
        v_priority_level := 'MEDIUM';
    ELSE
        v_priority_level := 'LOW';
    END IF;

    v_factors := jsonb_build_object(
        'category_weight', v_cat_weight,
        'age_boost', v_age_boost,
        'upvote_boost', v_upvote_boost,
        'duplicate_cluster_boost', v_cluster_boost,
        'final_score', v_final_score
    );

    UPDATE public.issues
    SET priority_score = v_final_score,
        priority_level = v_priority_level,
        score_factors = v_factors,
        updated_at = timezone('utc', now())
    WHERE id = p_issue_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to recompute on upvote change
CREATE OR REPLACE FUNCTION public.handle_upvote_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE public.issues SET upvotes = upvotes + 1 WHERE id = NEW.issue_id;
        PERFORM public.recompute_issue_priority(NEW.issue_id);
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE public.issues SET upvotes = GREATEST(0, upvotes - 1) WHERE id = OLD.issue_id;
        PERFORM public.recompute_issue_priority(OLD.issue_id);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_upvote_change ON public.issue_upvotes;
CREATE TRIGGER trg_upvote_change
    AFTER INSERT OR DELETE ON public.issue_upvotes
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_upvote_change();

-- ─── SECTION 9: RESOLVED GUARD TRIGGER (BLOCKED WITHOUT AFTER PHOTO) ─────────
CREATE OR REPLACE FUNCTION public.check_resolve_has_after_photo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'RESOLVED' THEN
        IF NEW.after_photo_path IS NULL OR trim(NEW.after_photo_path) = '' THEN
            RAISE EXCEPTION 'Resolution blocked: Issues cannot transition to RESOLVED without an after photo proof.';
        END IF;
        NEW.resolved_at = COALESCE(NEW.resolved_at, timezone('utc', now()));
    END IF;

    -- Record audit log and timeline on status change
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO public.issue_timeline (issue_id, status, message, actor_id)
        VALUES (
            NEW.id,
            NEW.status,
            'Status changed from ' || OLD.status || ' to ' || NEW.status,
            auth.uid()
        );

        INSERT INTO public.audit_log (entity_name, entity_id, action, old_data, new_data, performed_by)
        VALUES (
            'issues',
            NEW.id,
            'STATUS_CHANGE',
            jsonb_build_object('status', OLD.status, 'priority_score', OLD.priority_score),
            jsonb_build_object('status', NEW.status, 'priority_score', NEW.priority_score, 'after_photo_path', NEW.after_photo_path),
            auth.uid()
        );
    END IF;

    NEW.updated_at = timezone('utc', now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_check_resolve_after_photo ON public.issues;
CREATE TRIGGER trg_check_resolve_after_photo
    BEFORE UPDATE ON public.issues
    FOR EACH ROW
    EXECUTE FUNCTION public.check_resolve_has_after_photo();

-- ─── SECTION 10: 100M DUPLICATE MERGE ENGINE ─────────────────────────────────
CREATE OR REPLACE FUNCTION public.process_report_deduplication(p_report_id UUID)
RETURNS JSONB AS $$
DECLARE
    v_report RECORD;
    v_existing_issue RECORD;
    v_new_issue_id UUID;
    v_tracking TEXT;
BEGIN
    SELECT * INTO v_report FROM public.reports WHERE id = p_report_id;
    IF NOT FOUND THEN
        RETURN jsonb_build_object('status', 'not_found');
    END IF;

    -- Find matching active issue within 100 meters (using PostGIS geography distance)
    SELECT * INTO v_existing_issue
    FROM public.issues
    WHERE status NOT IN ('RESOLVED', 'CLOSED', 'CANCELLED')
      AND ST_DWithin(location::geography, v_report.location::geography, 100.0)
    ORDER BY ST_Distance(location::geography, v_report.location::geography) ASC
    LIMIT 1;

    IF FOUND THEN
        -- MERGE DUPLICATE
        UPDATE public.reports
        SET issue_id = v_existing_issue.id,
            is_duplicate = TRUE,
            status = 'DONE',
            updated_at = timezone('utc', now())
        WHERE id = p_report_id;

        UPDATE public.issues
        SET duplicate_count = duplicate_count + 1,
            updated_at = timezone('utc', now())
        WHERE id = v_existing_issue.id;

        PERFORM public.recompute_issue_priority(v_existing_issue.id);

        INSERT INTO public.issue_timeline (issue_id, status, message, metadata)
        VALUES (
            v_existing_issue.id,
            v_existing_issue.status,
            'Duplicate report merged from citizen submission (within 100m)',
            jsonb_build_object('report_id', p_report_id)
        );

        INSERT INTO public.audit_log (entity_name, entity_id, action, new_data, performed_by)
        VALUES (
            'issues',
            v_existing_issue.id,
            'MERGE',
            jsonb_build_object('merged_report_id', p_report_id, 'duplicate_count', v_existing_issue.duplicate_count + 1),
            v_report.user_id
        );

        RETURN jsonb_build_object('action', 'merged', 'issue_id', v_existing_issue.id);
    ELSE
        -- CREATE NEW ISSUE
        v_tracking := 'MD-' || to_char(timezone('utc', now()), 'YYYYMMDD') || '-' || upper(substring(gen_random_uuid()::text from 1 for 4));

        INSERT INTO public.issues (
            tracking_number,
            title,
            category,
            description,
            status,
            lat,
            lng,
            before_photo_path
        )
        VALUES (
            v_tracking,
            COALESCE(v_report.category, 'Infrastructure Report') || ' on Public Right-of-Way',
            COALESCE(v_report.category, 'OTHER'),
            v_report.description,
            'SUBMITTED',
            v_report.lat,
            v_report.lng,
            v_report.image_path
        )
        RETURNING id INTO v_new_issue_id;

        UPDATE public.reports
        SET issue_id = v_new_issue_id,
            status = 'DONE',
            updated_at = timezone('utc', now())
        WHERE id = p_report_id;

        PERFORM public.recompute_issue_priority(v_new_issue_id);

        INSERT INTO public.issue_timeline (issue_id, status, message)
        VALUES (
            v_new_issue_id,
            'SUBMITTED',
            'Issue created and verified from citizen report ' || v_tracking
        );

        RETURN jsonb_build_object('action', 'created', 'issue_id', v_new_issue_id);
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ─── SECTION 11: PUBLIC & ANONYMOUS VIEWS ────────────────────────────────────

-- 1. public_issues: Sanitized view for public map and listings
CREATE OR REPLACE VIEW public.public_issues AS
SELECT
    i.id,
    i.tracking_number,
    i.title,
    i.category,
    i.description,
    i.status,
    i.priority_level,
    i.priority_score,
    i.score_factors,
    i.lat,
    i.lng,
    i.address,
    i.neighborhood,
    i.department_code,
    i.upvotes,
    i.duplicate_count,
    i.before_photo_path,
    i.after_photo_path,
    i.created_at,
    i.updated_at,
    i.resolved_at
FROM public.issues i;

-- 2. public_issue_timeline: Public milestone timeline
CREATE OR REPLACE VIEW public.public_issue_timeline AS
SELECT
    t.id,
    t.issue_id,
    t.status,
    t.message,
    t.created_at
FROM public.issue_timeline t;

-- 3. public_proofs: Proof paths for resolved work verification
CREATE OR REPLACE VIEW public.public_proofs AS
SELECT
    i.id AS issue_id,
    i.tracking_number,
    i.before_photo_path,
    i.after_photo_path,
    i.resolved_at
FROM public.issues i
WHERE i.status = 'RESOLVED';

-- 4. public_stats & public_category_stats: Aggregate metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS public.public_stats AS
SELECT
    count(*)::INT AS total_issues,
    count(*) FILTER (WHERE status = 'RESOLVED')::INT AS resolved_issues,
    count(*) FILTER (WHERE status = 'IN_PROGRESS')::INT AS in_progress_issues,
    count(*) FILTER (WHERE status = 'SUBMITTED')::INT AS open_issues,
    COALESCE(ROUND((count(*) FILTER (WHERE status = 'RESOLVED')::NUMERIC / NULLIF(count(*), 0) * 100), 1), 0.0) AS resolution_rate_pct,
    COALESCE(ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600.0) FILTER (WHERE resolved_at IS NOT NULL), 1), 0.0) AS avg_resolution_hours,
    timezone('utc', now()) AS refreshed_at
FROM public.issues;

CREATE UNIQUE INDEX IF NOT EXISTS idx_public_stats_unique ON public.public_stats (refreshed_at);

CREATE MATERIALIZED VIEW IF NOT EXISTS public.public_category_stats AS
SELECT
    category,
    count(*)::INT AS total_count,
    count(*) FILTER (WHERE status = 'RESOLVED')::INT AS resolved_count,
    COALESCE(ROUND(AVG(priority_score), 1), 50.0) AS avg_priority,
    COALESCE(ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600.0) FILTER (WHERE resolved_at IS NOT NULL), 1), 0.0) AS avg_turnaround_hours,
    timezone('utc', now()) AS refreshed_at
FROM public.issues
GROUP BY category;

CREATE UNIQUE INDEX IF NOT EXISTS idx_public_cat_stats_cat ON public.public_category_stats (category);

-- ─── SECTION 12: SPATIAL RPCs ────────────────────────────────────────────────

-- 1. issues_in_bounds (Viewport loading with bounding box)
CREATE OR REPLACE FUNCTION public.issues_in_bounds(
    min_lat DOUBLE PRECISION,
    max_lat DOUBLE PRECISION,
    min_lng DOUBLE PRECISION,
    max_lng DOUBLE PRECISION,
    category_filter TEXT DEFAULT NULL,
    status_filter TEXT DEFAULT NULL,
    p_limit INT DEFAULT 200
)
RETURNS TABLE (
    id UUID,
    tracking_number TEXT,
    title TEXT,
    category TEXT,
    status TEXT,
    priority_level TEXT,
    priority_score NUMERIC(5,2),
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    address TEXT,
    neighborhood TEXT,
    upvotes INT,
    duplicate_count INT,
    created_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.tracking_number,
        i.title,
        i.category,
        i.status,
        i.priority_level,
        i.priority_score,
        i.lat,
        i.lng,
        i.address,
        i.neighborhood,
        i.upvotes,
        i.duplicate_count,
        i.created_at,
        i.resolved_at
    FROM public.issues i
    WHERE i.lat BETWEEN min_lat AND max_lat
      AND i.lng BETWEEN min_lng AND max_lng
      AND (category_filter IS NULL OR i.category = category_filter)
      AND (status_filter IS NULL OR i.status = status_filter)
    ORDER BY i.priority_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- 2. nearby_issues (Radius lookup, default 100 meters)
CREATE OR REPLACE FUNCTION public.nearby_issues(
    user_lat DOUBLE PRECISION,
    user_lng DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION DEFAULT 100.0,
    p_limit INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    tracking_number TEXT,
    title TEXT,
    category TEXT,
    status TEXT,
    distance_meters DOUBLE PRECISION,
    upvotes INT,
    duplicate_count INT,
    created_at TIMESTAMPTZ
) AS $$
DECLARE
    v_user_geom GEOMETRY;
BEGIN
    v_user_geom := ST_SetSRID(ST_MakePoint(user_lng, user_lat), 4326);

    RETURN QUERY
    SELECT
        i.id,
        i.tracking_number,
        i.title,
        i.category,
        i.status,
        ROUND(ST_Distance(i.location::geography, v_user_geom::geography)::NUMERIC, 1)::DOUBLE PRECISION AS distance_meters,
        i.upvotes,
        i.duplicate_count,
        i.created_at
    FROM public.issues i
    WHERE ST_DWithin(i.location::geography, v_user_geom::geography, radius_meters)
    ORDER BY distance_meters ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- ─── SECTION 13: ROW LEVEL SECURITY (RLS) POLICIES ───────────────────────────

-- Enable RLS across all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.issue_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.issue_upvotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- 1. PROFILES POLICIES
-- Anyone authenticated can view their own profile; staff/admin can view all
CREATE POLICY profiles_select_own ON public.profiles
    FOR SELECT TO authenticated
    USING (auth.uid() = id);

CREATE POLICY profiles_update_own ON public.profiles
    FOR UPDATE TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- 2. REPORTS POLICIES
-- Citizens see ONLY their own reports
CREATE POLICY reports_citizen_select_own ON public.reports
    FOR SELECT TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY reports_citizen_insert_own ON public.reports
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

-- Citizens can delete or update their pending report only before it is processed
CREATE POLICY reports_citizen_update_own ON public.reports
    FOR UPDATE TO authenticated
    USING (auth.uid() = user_id AND status = 'PENDING')
    WITH CHECK (auth.uid() = user_id AND status = 'PENDING');

-- 3. ISSUES POLICIES
-- Citizens and Anon CANNOT directly insert, update or delete issues table
CREATE POLICY issues_select_authenticated ON public.issues
    FOR SELECT TO authenticated
    USING (true);

-- Only staff/admin or service_role can update issues directly
CREATE POLICY issues_staff_update ON public.issues
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid()
              AND p.role IN ('STAFF', 'MANAGER', 'ADMIN', 'DISPATCHER', 'INSPECTOR', 'FIELD_WORKER')
        )
    );

-- 4. ISSUE UPVOTES POLICIES
CREATE POLICY upvotes_select_authenticated ON public.issue_upvotes
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY upvotes_insert_own ON public.issue_upvotes
    FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY upvotes_delete_own ON public.issue_upvotes
    FOR DELETE TO authenticated
    USING (auth.uid() = user_id);

-- 5. AUDIT LOG POLICIES
-- Only admin can view audit log
CREATE POLICY audit_log_admin_read ON public.audit_log
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role = 'ADMIN'
        )
    );

-- 6. TIMELINE POLICIES
CREATE POLICY timeline_select_authenticated ON public.issue_timeline
    FOR SELECT TO authenticated
    USING (true);

-- 7. GRANTS FOR ANONYMOUS ROLE (ANON CAN READ ONLY SANITIZED VIEWS)
REVOKE ALL ON public.profiles FROM anon;
REVOKE ALL ON public.reports FROM anon;
REVOKE ALL ON public.issues FROM anon;
REVOKE ALL ON public.issue_timeline FROM anon;
REVOKE ALL ON public.issue_upvotes FROM anon;
REVOKE ALL ON public.audit_log FROM anon;

GRANT SELECT ON public.public_issues TO anon, authenticated;
GRANT SELECT ON public.public_issue_timeline TO anon, authenticated;
GRANT SELECT ON public.public_proofs TO anon, authenticated;
GRANT SELECT ON public.public_stats TO anon, authenticated;
GRANT SELECT ON public.public_category_stats TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.issues_in_bounds TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.nearby_issues TO anon, authenticated;

-- ─── SECTION 14: PG_CRON SCHEDULES ───────────────────────────────────────────
-- Sweeper recovery function for stale PROCESSING reports (> 10 minutes)
CREATE OR REPLACE FUNCTION public.recover_stale_reports()
RETURNS INT AS $$
DECLARE
    v_recovered_count INT;
BEGIN
    WITH stale AS (
        UPDATE public.reports
        SET status = 'FAILED',
            error_message = 'Report processing timed out. Automatically marked as FAILED by sweeper.',
            updated_at = timezone('utc', now())
        WHERE status = 'PROCESSING'
          AND updated_at < (timezone('utc', now()) - INTERVAL '10 minutes')
        RETURNING id
    )
    SELECT count(*) INTO v_recovered_count FROM stale;

    RETURN v_recovered_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Schedule 1: Run sweeper recovery every 5 minutes
-- SELECT cron.schedule('civicfix_sweeper_recovery', '*/5 * * * *', 'SELECT public.recover_stale_reports();');

-- Schedule 2: Refresh public analytics materialized views every 15 minutes
-- SELECT cron.schedule('civicfix_refresh_materialized_views', '*/15 * * * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY public.public_stats; REFRESH MATERIALIZED VIEW CONCURRENTLY public.public_category_stats;');

-- ─── SECTION 15: STORAGE BUCKETS CONFIGURATION ───────────────────────────────
INSERT INTO storage.buckets (id, name, public)
VALUES ('reports', 'reports', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('proofs', 'proofs', false)
ON CONFLICT (id) DO NOTHING;

-- Storage Policy: Authenticated users can upload to reports/<user_id>/...
CREATE POLICY "Allow authenticated upload to reports bucket"
ON storage.objects FOR INSERT TO authenticated
WITH CHECK (
    bucket_id = 'reports' AND
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Public can read reports photos
CREATE POLICY "Public read access for reports bucket"
ON storage.objects FOR SELECT TO public
USING (bucket_id = 'reports');

-- Proofs bucket is private: only service_role or staff/admin can read/upload
CREATE POLICY "Private read for proofs bucket"
ON storage.objects FOR SELECT TO authenticated
USING (
    bucket_id = 'proofs' AND
    EXISTS (
        SELECT 1 FROM public.profiles p
        WHERE p.id = auth.uid()
          AND p.role IN ('STAFF', 'MANAGER', 'ADMIN', 'FIELD_WORKER', 'INSPECTOR')
    )
);

