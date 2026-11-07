-- =============================================================================
-- Test Suite: 01_rls_and_guards_test.sql
-- Description: Automated verification for RLS, Security Guards, Audit Log,
--              Duplicate Merging, and Anon Access Restriction.
-- =============================================================================

BEGIN;

-- Setup test helper assertions
CREATE OR REPLACE FUNCTION pg_temp.assert(condition BOOLEAN, test_name TEXT)
RETURNS VOID AS $$
BEGIN
    IF NOT condition THEN
        RAISE EXCEPTION 'TEST FAILED: %', test_name;
    ELSE
        RAISE NOTICE 'TEST PASSED: %', test_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- Setup Test Fixtures (2 Mock Users)
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    uid1 UUID := '11111111-1111-1111-1111-111111111111';
    uid2 UUID := '22222222-2222-2222-2222-222222222222';
BEGIN
    INSERT INTO auth.users (id, email)
    VALUES (uid1, 'citizen1@maryland.gov'), (uid2, 'citizen2@maryland.gov')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO public.profiles (id, email, full_name, role)
    VALUES
        (uid1, 'citizen1@maryland.gov', 'Citizen One', 'CITIZEN'),
        (uid2, 'citizen2@maryland.gov', 'Citizen Two', 'CITIZEN')
    ON CONFLICT (id) DO NOTHING;
END $$;

-- -----------------------------------------------------------------------------
-- TEST 1: Citizens see ONLY their own reports
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    uid1 UUID := '11111111-1111-1111-1111-111111111111';
    uid2 UUID := '22222222-2222-2222-2222-222222222222';
    v_count INT;
BEGIN
    -- Insert reports under service role
    INSERT INTO public.reports (id, user_id, image_path, lat, lng, category, description)
    VALUES
        ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', uid1, 'reports/1.webp', 38.9784, -76.4922, 'POTHOLE', 'Pothole 1'),
        ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', uid2, 'reports/2.webp', 38.9790, -76.4930, 'STREETLIGHT', 'Light 2');

    -- Switch context to uid1
    PERFORM set_config('role', 'authenticated', true);
    PERFORM set_config('request.jwt.claim.sub', uid1::text, true);

    SELECT count(*) INTO v_count FROM public.reports;
    PERFORM pg_temp.assert(v_count = 1, 'TEST 1: Citizen 1 can see ONLY their own report (1 row visible out of 2)');

    -- Switch back
    PERFORM set_config('role', 'service_role', true);
END $$;

-- -----------------------------------------------------------------------------
-- TEST 2: Citizens CANNOT change role
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    uid1 UUID := '11111111-1111-1111-1111-111111111111';
    v_caught BOOLEAN := FALSE;
BEGIN
    -- Switch context to uid1
    PERFORM set_config('role', 'authenticated', true);
    PERFORM set_config('request.jwt.claim.sub', uid1::text, true);

    BEGIN
        UPDATE public.profiles SET role = 'ADMIN' WHERE id = uid1;
    EXCEPTION WHEN OTHERS THEN
        v_caught := TRUE;
    END;

    PERFORM pg_temp.assert(v_caught, 'TEST 2: Citizen role modification blocked by profile guard trigger');
    PERFORM set_config('role', 'service_role', true);
END $$;

-- -----------------------------------------------------------------------------
-- TEST 3: Citizens CANNOT update issues
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    uid1 UUID := '11111111-1111-1111-1111-111111111111';
    v_issue_id UUID;
    v_rows_affected INT;
BEGIN
    -- Create test issue under service role
    INSERT INTO public.issues (tracking_number, title, category, lat, lng)
    VALUES ('MD-TEST-001', 'Test Issue', 'POTHOLE', 38.9784, -76.4922)
    RETURNING id INTO v_issue_id;

    -- Switch to citizen1
    PERFORM set_config('role', 'authenticated', true);
    PERFORM set_config('request.jwt.claim.sub', uid1::text, true);

    UPDATE public.issues SET title = 'Hacked Title' WHERE id = v_issue_id;
    GET DIAGNOSTICS v_rows_affected = ROW_COUNT;

    PERFORM pg_temp.assert(v_rows_affected = 0, 'TEST 3: Citizen cannot update issues (RLS allows 0 affected rows)');
    PERFORM set_config('role', 'service_role', true);
END $$;

-- -----------------------------------------------------------------------------
-- TEST 4: RESOLVED is blocked without an after photo
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_issue_id UUID;
    v_caught BOOLEAN := FALSE;
BEGIN
    SELECT id INTO v_issue_id FROM public.issues WHERE tracking_number = 'MD-TEST-001';

    BEGIN
        UPDATE public.issues
        SET status = 'RESOLVED', after_photo_path = NULL
        WHERE id = v_issue_id;
    EXCEPTION WHEN OTHERS THEN
        v_caught := TRUE;
    END;

    PERFORM pg_temp.assert(v_caught, 'TEST 4a: Transition to RESOLVED blocked when after_photo_path is NULL');

    -- Now provide after photo, transition should succeed
    UPDATE public.issues
    SET status = 'RESOLVED', after_photo_path = 'proofs/resolved_after_001.webp'
    WHERE id = v_issue_id;

    PERFORM pg_temp.assert((SELECT status FROM public.issues WHERE id = v_issue_id) = 'RESOLVED',
                           'TEST 4b: Transition to RESOLVED succeeds when after_photo_path is provided');
END $$;

-- -----------------------------------------------------------------------------
-- TEST 5: The audit log is strictly append-only
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_log_id UUID;
    v_caught_update BOOLEAN := FALSE;
    v_caught_delete BOOLEAN := FALSE;
BEGIN
    INSERT INTO public.audit_log (entity_name, entity_id, action, new_data)
    VALUES ('test_entity', gen_random_uuid(), 'INSERT', '{"test": true}'::jsonb)
    RETURNING id INTO v_log_id;

    -- Attempt UPDATE
    BEGIN
        UPDATE public.audit_log SET action = 'UPDATE' WHERE id = v_log_id;
    EXCEPTION WHEN OTHERS THEN
        v_caught_update := TRUE;
    END;

    -- Attempt DELETE
    BEGIN
        DELETE FROM public.audit_log WHERE id = v_log_id;
    EXCEPTION WHEN OTHERS THEN
        v_caught_delete := TRUE;
    END;

    PERFORM pg_temp.assert(v_caught_update, 'TEST 5a: UPDATE on audit_log blocked by immutable trigger');
    PERFORM pg_temp.assert(v_caught_delete, 'TEST 5b: DELETE on audit_log blocked by immutable trigger');
END $$;

-- -----------------------------------------------------------------------------
-- TEST 6: Duplicates within 100m merge and priority recomputes
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    uid1 UUID := '11111111-1111-1111-1111-111111111111';
    v_rep1 UUID := 'cccccccc-cccc-cccc-cccc-cccccccccccc';
    v_rep2 UUID := 'dddddddd-dddd-dddd-dddd-dddddddddddd';
    v_res1 JSONB;
    v_res2 JSONB;
    v_issue_id UUID;
    v_dup_count INT;
    v_priority NUMERIC;
BEGIN
    -- Report 1 at State Circle, Annapolis (38.9784, -76.4922)
    INSERT INTO public.reports (id, user_id, image_path, lat, lng, category, description)
    VALUES (v_rep1, uid1, 'reports/state_circle_1.webp', 38.9784, -76.4922, 'Pothole & Road Damage', 'Deep pothole on State Circle');

    v_res1 := public.process_report_deduplication(v_rep1);
    v_issue_id := (v_res1->>'issue_id')::UUID;

    -- Report 2 located ~45 meters away (38.9787, -76.4925)
    INSERT INTO public.reports (id, user_id, image_path, lat, lng, category, description)
    VALUES (v_rep2, uid1, 'reports/state_circle_2.webp', 38.9787, -76.4925, 'Pothole & Road Damage', 'Another report of road damage nearby');

    v_res2 := public.process_report_deduplication(v_rep2);

    SELECT duplicate_count, priority_score INTO v_dup_count, v_priority
    FROM public.issues WHERE id = v_issue_id;

    PERFORM pg_temp.assert((v_res2->>'action') = 'merged', 'TEST 6a: Report within 100m detected as duplicate and merged');
    PERFORM pg_temp.assert(v_dup_count = 1, 'TEST 6b: Issue duplicate_count incremented to 1');
    PERFORM pg_temp.assert(v_priority > 25.0, 'TEST 6c: Issue priority score recomputed upwards with cluster boost');
END $$;

-- -----------------------------------------------------------------------------
-- TEST 7: Anon can read only public views, NOT raw tables
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_anon_issues_count INT;
    v_anon_blocked_reports BOOLEAN := FALSE;
    v_anon_blocked_profiles BOOLEAN := FALSE;
BEGIN
    PERFORM set_config('role', 'anon', true);

    -- Should succeed reading public_issues
    SELECT count(*) INTO v_anon_issues_count FROM public.public_issues;
    PERFORM pg_temp.assert(v_anon_issues_count >= 1, 'TEST 7a: Anon can read public_issues view');

    -- Should fail reading raw reports
    BEGIN
        PERFORM count(*) FROM public.reports;
    EXCEPTION WHEN OTHERS THEN
        v_anon_blocked_reports := TRUE;
    END;
    PERFORM pg_temp.assert(v_anon_blocked_reports, 'TEST 7b: Anon direct read from public.reports denied');

    -- Should fail reading raw profiles
    BEGIN
        PERFORM count(*) FROM public.profiles;
    EXCEPTION WHEN OTHERS THEN
        v_anon_blocked_profiles := TRUE;
    END;
    PERFORM pg_temp.assert(v_anon_blocked_profiles, 'TEST 7c: Anon direct read from public.profiles denied');

    PERFORM set_config('role', 'service_role', true);
END $$;

ROLLBACK; -- Clean rollback of test execution

