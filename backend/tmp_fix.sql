ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED;
CREATE INDEX IF NOT EXISTS ix_document_chunks_search_vector_gin ON document_chunks USING gin (search_vector);
