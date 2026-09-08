BEGIN;

ALTER TABLE claim
    ALTER COLUMN entity_id DROP NOT NULL;

ALTER TABLE claim
    ADD COLUMN relation_source_entity_id TEXT REFERENCES knowledge_entity(id),
    ADD COLUMN relation_type TEXT,
    ADD COLUMN relation_target_entity_id TEXT REFERENCES knowledge_entity(id);

ALTER TABLE claim
    ADD CONSTRAINT claim_exactly_one_subject CHECK (
        (
            entity_id IS NOT NULL AND
            relation_source_entity_id IS NULL AND
            relation_type IS NULL AND
            relation_target_entity_id IS NULL
        ) OR (
            entity_id IS NULL AND
            relation_source_entity_id IS NOT NULL AND
            relation_type IS NOT NULL AND
            relation_target_entity_id IS NOT NULL
        )
    );

ALTER TABLE claim
    ADD CONSTRAINT claim_relation_type_allowed CHECK (
        relation_type IS NULL OR relation_type IN (
            'broader_than',
            'narrower_than',
            'related_to',
            'solves',
            'requires',
            'enables',
            'implements',
            'derived_from',
            'inspired_by',
            'conflicts_with',
            'tradeoff_with',
            'supersedes'
        )
    );

ALTER TABLE claim
    ADD CONSTRAINT claim_relation_not_self CHECK (
        relation_source_entity_id IS NULL OR
        relation_source_entity_id <> relation_target_entity_id
    );

CREATE INDEX idx_claim_relation_source
    ON claim(relation_source_entity_id)
    WHERE relation_source_entity_id IS NOT NULL;

CREATE INDEX idx_claim_relation_target
    ON claim(relation_target_entity_id)
    WHERE relation_target_entity_id IS NOT NULL;

CREATE INDEX idx_claim_relation_type
    ON claim(relation_type)
    WHERE relation_type IS NOT NULL;

COMMIT;
