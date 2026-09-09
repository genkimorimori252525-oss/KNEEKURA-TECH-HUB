BEGIN;

CREATE FUNCTION kthub_source_identity_payload(p_kind TEXT, p_origin JSONB)
RETURNS JSONB
LANGUAGE sql
IMMUTABLE
AS $$
SELECT jsonb_build_object(
    'kind', p_kind,
    'origin', COALESCE(p_origin, '{}'::jsonb) - ARRAY[
        'default_branch',
        'description',
        'language',
        'fork',
        'archived',
        'disabled',
        'visibility',
        'stargazers_count',
        'forks_count',
        'open_issues_count',
        'pushed_at',
        'updated_at',
        'topics',
        'github_license_hint',
        'discovery_hits'
    ]::text[]
);
$$;

CREATE FUNCTION kthub_guard_source_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.id IS DISTINCT FROM NEW.id THEN
        RAISE EXCEPTION 'source id is immutable: %', OLD.id;
    END IF;

    IF kthub_source_identity_payload(OLD.kind, OLD.origin)
       IS DISTINCT FROM
       kthub_source_identity_payload(NEW.kind, NEW.origin) THEN
        RAISE EXCEPTION 'source identity is immutable: %', OLD.id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_source_identity_integrity
BEFORE UPDATE OF id, kind, origin ON source
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_source_identity();

COMMIT;
