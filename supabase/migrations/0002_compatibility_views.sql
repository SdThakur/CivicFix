-- =============================================================================
-- Migration: 0002_compatibility_views.sql
-- Description: Backward Compatibility for Legacy SQLAlchemy Models (Report, Issue)
-- =============================================================================

-- Add compatibility columns to reports
ALTER TABLE public.reports 
    ADD COLUMN IF NOT EXISTS tracking_number TEXT,
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'MEDIUM',
    ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS address TEXT,
    ADD COLUMN IF NOT EXISTS neighborhood TEXT,
    ADD COLUMN IF NOT EXISTS image_urls JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS ai_score DOUBLE PRECISION DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS upvotes INTEGER DEFAULT 0;

-- Add compatibility columns to issues
ALTER TABLE public.issues
    ADD COLUMN IF NOT EXISTS issue_code TEXT,
    ADD COLUMN IF NOT EXISTS priority TEXT DEFAULT 'MEDIUM',
    ADD COLUMN IF NOT EXISTS department_id INTEGER,
    ADD COLUMN IF NOT EXISTS assigned_to_id INTEGER,
    ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS estimated_cost DOUBLE PRECISION DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS actual_cost DOUBLE PRECISION DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS total_reports_count INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS score DOUBLE PRECISION DEFAULT 50.0;

-- Bidirectional coordinate & default values synchronization for reports
CREATE OR REPLACE FUNCTION public.sync_report_compatibility_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Coordinate sync
    IF NEW.latitude IS NULL AND NEW.lat IS NOT NULL THEN
        NEW.latitude := NEW.lat;
    ELSIF NEW.lat IS NULL AND NEW.latitude IS NOT NULL THEN
        NEW.lat := NEW.latitude;
    END IF;

    IF NEW.longitude IS NULL AND NEW.lng IS NOT NULL THEN
        NEW.longitude := NEW.lng;
    ELSIF NEW.lng IS NULL AND NEW.longitude IS NOT NULL THEN
        NEW.lng := NEW.longitude;
    END IF;

    -- Defaults for legacy queries
    IF NEW.tracking_number IS NULL THEN
        NEW.tracking_number := 'RPT-' || upper(substr(NEW.id::text, 1, 8));
    END IF;

    IF NEW.title IS NULL THEN
        NEW.title := COALESCE(NEW.category, 'Citizen Report');
    END IF;

    IF NEW.neighborhood IS NULL THEN
        NEW.neighborhood := 'Downtown';
    END IF;

    IF NEW.address IS NULL THEN
        NEW.address := 'Reported Location';
    END IF;

    IF NEW.image_urls IS NULL OR NEW.image_urls = '[]'::jsonb THEN
        IF NEW.image_path IS NOT NULL AND NEW.image_path != '' THEN
            NEW.image_urls := jsonb_build_array(NEW.image_path);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_report_compatibility ON public.reports;
CREATE TRIGGER trg_sync_report_compatibility
    BEFORE INSERT OR UPDATE ON public.reports
    FOR EACH ROW
    EXECUTE FUNCTION public.sync_report_compatibility_fields();

-- Bidirectional coordinate & status/priority synchronization for issues
CREATE OR REPLACE FUNCTION public.sync_issue_compatibility_fields()
RETURNS TRIGGER AS $$
BEGIN
    -- Coordinate sync
    IF NEW.latitude IS NULL AND NEW.lat IS NOT NULL THEN
        NEW.latitude := NEW.lat;
    ELSIF NEW.lat IS NULL AND NEW.latitude IS NOT NULL THEN
        NEW.lat := NEW.latitude;
    END IF;

    IF NEW.longitude IS NULL AND NEW.lng IS NOT NULL THEN
        NEW.longitude := NEW.lng;
    ELSIF NEW.lng IS NULL AND NEW.longitude IS NOT NULL THEN
        NEW.lng := NEW.longitude;
    END IF;

    -- Code / tracking sync
    IF NEW.issue_code IS NULL AND NEW.tracking_number IS NOT NULL THEN
        NEW.issue_code := NEW.tracking_number;
    ELSIF NEW.tracking_number IS NULL AND NEW.issue_code IS NOT NULL THEN
        NEW.tracking_number := NEW.issue_code;
    END IF;

    -- Priority sync
    IF NEW.priority IS NULL AND NEW.priority_level IS NOT NULL THEN
        NEW.priority := NEW.priority_level;
    ELSIF NEW.priority_level IS NULL AND NEW.priority IS NOT NULL THEN
        NEW.priority_level := NEW.priority;
    END IF;

    -- Score sync
    IF NEW.score IS NULL AND NEW.priority_score IS NOT NULL THEN
        NEW.score := NEW.priority_score::double precision;
    ELSIF NEW.priority_score IS NULL AND NEW.score IS NOT NULL THEN
        NEW.priority_score := NEW.score::numeric(5,2);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_issue_compatibility ON public.issues;
CREATE TRIGGER trg_sync_issue_compatibility
    BEFORE INSERT OR UPDATE ON public.issues
    FOR EACH ROW
    EXECUTE FUNCTION public.sync_issue_compatibility_fields();

