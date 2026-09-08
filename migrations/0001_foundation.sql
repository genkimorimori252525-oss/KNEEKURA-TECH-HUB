BEGIN;

CREATE TABLE IF NOT EXISTS knowledge_entity (
    id TEXT PRIMARY KEY CHECK (id LIKE 'ke:%'),
    canonical_name TEXT NOT NULL,
    abstraction_level TEXT NOT NULL CHECK (abstraction_level IN ('L0','L1','L2','L3','L4')),
    identity_state TEXT NOT NULL CHECK (identity_state IN ('PROPOSED','CANONICAL','MERGED','RETIRED')),
    redirect_to TEXT REFERENCES knowledge_entity(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_identity_reviewed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS entity_alias (
    entity_id TEXT NOT NULL REFERENCES knowledge_entity(id),
    alias TEXT NOT NULL,
    language_tag TEXT,
    PRIMARY KEY (entity_id, alias)
);

CREATE TABLE IF NOT EXISTS entity_kind (
    entity_id TEXT NOT NULL REFERENCES knowledge_entity(id),
    kind TEXT NOT NULL,
    PRIMARY KEY (entity_id, kind)
);

CREATE TABLE IF NOT EXISTS entity_relation (
    source_entity_id TEXT NOT NULL REFERENCES knowledge_entity(id),
    relation_type TEXT NOT NULL,
    target_entity_id TEXT NOT NULL REFERENCES knowledge_entity(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source_entity_id, relation_type, target_entity_id),
    CHECK (source_entity_id <> target_entity_id OR relation_type = 'related_to')
);

CREATE TABLE IF NOT EXISTS source (
    id TEXT PRIMARY KEY CHECK (id LIKE 'src:%'),
    kind TEXT NOT NULL,
    origin JSONB NOT NULL,
    license JSONB NOT NULL,
    acquisition_level TEXT NOT NULL CHECK (acquisition_level IN ('metadata-only','snapshot','selected-files','full-source')),
    first_observed TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_checked TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS source_snapshot (
    id TEXT PRIMARY KEY CHECK (id LIKE 'ss:%'),
    source_id TEXT NOT NULL REFERENCES source(id),
    revision TEXT,
    content_hash TEXT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY CHECK (id LIKE 'ev:%'),
    source_id TEXT NOT NULL REFERENCES source(id),
    source_snapshot_id TEXT REFERENCES source_snapshot(id),
    locator JSONB NOT NULL,
    roles TEXT[] NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_relation (
    from_evidence_id TEXT NOT NULL REFERENCES evidence(id),
    relation_type TEXT NOT NULL,
    to_evidence_id TEXT NOT NULL REFERENCES evidence(id),
    PRIMARY KEY (from_evidence_id, relation_type, to_evidence_id)
);

CREATE TABLE IF NOT EXISTS claim (
    id TEXT PRIMARY KEY CHECK (id LIKE 'cl:%'),
    entity_id TEXT NOT NULL REFERENCES knowledge_entity(id),
    claim_type TEXT NOT NULL CHECK (claim_type IN ('DIRECT_OBSERVATION','AUTHOR_CLAIM','INFERENCE','EXPERIMENT_RESULT','JUDGMENT')),
    statement TEXT NOT NULL,
    maturity TEXT NOT NULL CHECK (maturity IN ('CANDIDATE','SUPPORTED','VALIDATED','CHALLENGED','SUPERSEDED','REJECTED')),
    scope JSONB NOT NULL DEFAULT '{}'::jsonb,
    applicability JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence TEXT,
    reasoning_basis JSONB NOT NULL DEFAULT '[]'::jsonb,
    alternative_interpretations JSONB NOT NULL DEFAULT '[]'::jsonb,
    first_observed TIMESTAMPTZ,
    last_verified TIMESTAMPTZ,
    verification_due_at TIMESTAMPTZ,
    superseded_by TEXT REFERENCES claim(id),
    created_by JSONB NOT NULL,
    policy_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claim_evidence (
    claim_id TEXT NOT NULL REFERENCES claim(id),
    evidence_id TEXT NOT NULL REFERENCES evidence(id),
    PRIMARY KEY (claim_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS staged_observation (
    id TEXT PRIMARY KEY CHECK (id LIKE 'obs:%'),
    source_id TEXT NOT NULL REFERENCES source(id),
    summary TEXT NOT NULL,
    candidate_names JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL CHECK (status IN ('NEW','TRIAGED','PROMOTED','REJECTED','EXPIRED')),
    created_by JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS curation_event (
    id TEXT PRIMARY KEY CHECK (id LIKE 'ce:%'),
    operation TEXT NOT NULL,
    actor JSONB NOT NULL,
    subject_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    reason TEXT,
    policy_version TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    reversible BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_claim_entity ON claim(entity_id);
CREATE INDEX IF NOT EXISTS idx_claim_maturity ON claim(maturity);
CREATE INDEX IF NOT EXISTS idx_claim_last_verified ON claim(last_verified);
CREATE INDEX IF NOT EXISTS idx_source_kind ON source(kind);
CREATE INDEX IF NOT EXISTS idx_staged_observation_status ON staged_observation(status);

COMMIT;
