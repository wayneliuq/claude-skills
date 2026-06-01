-- Memory/recall index schema — Phase 1a (BM25/FTS5 only).
-- The index is a DERIVED, rebuildable artifact over the canonical markdown.
-- Deleting the db loses nothing; build_index.py rebuilds it from files.
--
-- Phase 1b attaches a `vec0` table for the local-embedding vector leg LAZILY,
-- guarded by an extension-load probe. This file intentionally creates NO vec0
-- DDL, so the BM25 leg never inherits sqlite-vec's extension-load risk.

-- Build/version metadata (Phase 1b stores embedding model_id + dim here).
CREATE TABLE IF NOT EXISTS index_meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);

-- Single FTS5 table. Metadata columns are UNINDEXED (stored + filterable in
-- WHERE, but not full-text ranked); `domains` + `distilled_text` are indexed,
-- so bm25(records_fts) ranks on the meaningful text. content_hash is the
-- dedupe key (enforced at ingest, not by a UNIQUE constraint — FTS5 has none).
CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(
  rec_id UNINDEXED,
  type UNINDEXED,
  status UNINDEXED,
  domains,
  source_path UNINDEXED,
  anchor UNINDEXED,
  content_hash UNINDEXED,
  schema_generation UNINDEXED,
  distilled_text,
  tokenize = 'porter unicode61'
);
