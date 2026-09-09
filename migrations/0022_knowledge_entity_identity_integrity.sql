BEGIN;

CREATE TABLE knowledge_entity_identity_anchor (
    entity_id TEXT PRIMARY KEY REFERENCES knowledge_entity(id) ON DELETE RESTRICT,
    payload JSONB NOT NULL
);

CREATE FUNCTION kthub_entity_identity_payload(p_entity_id TEXT)
RETURNS JSONB
LANGUAGE sql
STABLE
AS $$
SELECT jsonb_build_object(
    'canonical_name', e.canonical_name,
    'abstraction_level', e.abstraction_level,
    'aliases', COALESCE(
        (SELECT jsonb_agg(a.alias ORDER BY a.alias)
         FROM entity_alias a
         WHERE a.entity_id = e.id),
        '[]'::jsonb
    ),
    'kinds', COALESCE(
        (SELECT jsonb_agg(k.kind ORDER BY k.kind)
         FROM entity_kind k
         WHERE k.entity_id = e.id),
        '[]'::jsonb
    ),
    'relations', COALESCE(
        (SELECT jsonb_agg(
             jsonb_build_object('type', r.relation_type, 'target', r.target_entity_id)
             ORDER BY r.relation_type, r.target_entity_id
         )
         FROM entity_relation r
         WHERE r.source_entity_id = e.id),
        '[]'::jsonb
    )
)
FROM knowledge_entity e
WHERE e.id = p_entity_id;
$$;

INSERT INTO knowledge_entity_identity_anchor(entity_id, payload)
SELECT e.id, kthub_entity_identity_payload(e.id)
FROM knowledge_entity e;

CREATE FUNCTION kthub_capture_entity_identity_anchor()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO knowledge_entity_identity_anchor(entity_id, payload)
    VALUES (NEW.id, kthub_entity_identity_payload(NEW.id))
    ON CONFLICT (entity_id) DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_knowledge_entity_capture_identity
AFTER INSERT ON knowledge_entity
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_capture_entity_identity_anchor();

CREATE FUNCTION kthub_assert_entity_identity_anchor()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_entity_id TEXT;
    v_expected JSONB;
    v_actual JSONB;
BEGIN
    IF TG_TABLE_NAME = 'knowledge_entity' THEN
        IF TG_OP = 'DELETE' THEN
            v_entity_id := OLD.id;
        ELSE
            v_entity_id := NEW.id;
        END IF;
    ELSIF TG_TABLE_NAME IN ('entity_alias', 'entity_kind') THEN
        IF TG_OP = 'DELETE' THEN
            v_entity_id := OLD.entity_id;
        ELSE
            v_entity_id := NEW.entity_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'entity_relation' THEN
        IF TG_OP = 'DELETE' THEN
            v_entity_id := OLD.source_entity_id;
        ELSE
            v_entity_id := NEW.source_entity_id;
        END IF;
    ELSE
        RAISE EXCEPTION 'unsupported entity identity table: %', TG_TABLE_NAME;
    END IF;

    SELECT payload INTO v_expected
    FROM knowledge_entity_identity_anchor
    WHERE entity_id = v_entity_id;

    -- New entities receive their anchor at the end of their creation transaction.
    IF v_expected IS NULL THEN
        IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
    END IF;

    v_actual := kthub_entity_identity_payload(v_entity_id);
    IF v_actual IS DISTINCT FROM v_expected THEN
        RAISE EXCEPTION 'knowledge_entity concept payload is immutable: %', v_entity_id;
    END IF;

    IF TG_OP = 'DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_knowledge_entity_identity_payload
AFTER UPDATE ON knowledge_entity
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_assert_entity_identity_anchor();

CREATE CONSTRAINT TRIGGER trg_entity_alias_identity_payload
AFTER INSERT OR UPDATE OR DELETE ON entity_alias
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_assert_entity_identity_anchor();

CREATE CONSTRAINT TRIGGER trg_entity_kind_identity_payload
AFTER INSERT OR UPDATE OR DELETE ON entity_kind
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_assert_entity_identity_anchor();

CREATE CONSTRAINT TRIGGER trg_entity_relation_identity_payload
AFTER INSERT OR UPDATE OR DELETE ON entity_relation
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_assert_entity_identity_anchor();

CREATE FUNCTION kthub_guard_entity_identity_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_target_state TEXT;
BEGIN
    IF OLD.identity_state = NEW.identity_state
       AND OLD.redirect_to IS NOT DISTINCT FROM NEW.redirect_to THEN
        RETURN NEW;
    END IF;

    IF OLD.identity_state = 'CANONICAL'
       AND OLD.redirect_to IS NULL
       AND NEW.identity_state = 'MERGED'
       AND NEW.redirect_to IS NOT NULL
       AND NEW.redirect_to <> NEW.id THEN
        SELECT identity_state INTO v_target_state
        FROM knowledge_entity
        WHERE id = NEW.redirect_to;
        IF v_target_state IS DISTINCT FROM 'CANONICAL' THEN
            RAISE EXCEPTION 'entity merge redirect must target a canonical entity: %', NEW.redirect_to;
        END IF;
        RETURN NEW;
    END IF;

    RAISE EXCEPTION 'invalid knowledge_entity identity transition: % -> %',
        OLD.identity_state, NEW.identity_state;
END;
$$;

CREATE TRIGGER trg_knowledge_entity_identity_state
BEFORE UPDATE OF identity_state, redirect_to ON knowledge_entity
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_entity_identity_state();

COMMIT;
