#!/usr/bin/env python3
"""Build the derived memory index from a docs/strategic-implementation tree.

Rebuild-from-scratch: the db is dropped and recreated every run, so the
markdown files are always the single source of truth. The db lives at
<root>/.memory/index.db by default and is git-ignored.

Phase 1a: BM25/FTS5 only (no embeddings, no sqlite-vec). Phase 1b's embed.py
attaches the vector leg lazily, guarded by an extension-load probe.

Usage:
  build_index.py [--root docs/strategic-implementation] [--db <path>] [--quiet]

Exit codes: 0 success; 2 FTS5 unavailable in this sqlite build (build only —
recall degrades to silence independently and never blocks execution).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sqlite3
import sys
from pathlib import Path

import ingest

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def fts5_available() -> bool:
    try:
        c = sqlite3.connect(":memory:")
        c.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        c.close()
        return True
    except sqlite3.OperationalError:
        return False


def load_vec_extension(conn) -> bool:
    """Try to load sqlite-vec into conn. Returns True on success.

    Catches AttributeError (enable_load_extension compiled out — e.g. the
    python.org build) AND OperationalError/ImportError, so a non-capable
    interpreter degrades cleanly to BM25-only rather than crashing.
    """
    try:
        import sqlite_vec
    except ImportError:
        return False
    try:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute("SELECT vec_version()")
        return True
    except (AttributeError, sqlite3.OperationalError):
        return False


def _build_vectors(conn, want: str) -> str:
    """Populate a vec0 table from the FTS5 records. Returns a status string.

    `want`: 'off' | 'on' | 'auto'. 'auto' attempts only if the embedder is
    importable. Any failure (no embedder, no extension, no capable interpreter)
    degrades to BM25-only — the vector leg is strictly additive.
    """
    if want == "off":
        return "skipped (off)"
    import embed
    if not embed.available():
        return "skipped (embedder unavailable)"
    if not load_vec_extension(conn):
        return "skipped (sqlite-vec/extension-load unavailable on this interpreter)"

    rows = conn.execute(
        "SELECT rowid, distilled_text FROM records_fts ORDER BY rowid").fetchall()
    if not rows:
        return "skipped (empty index)"

    import sqlite_vec
    dim = embed.DIM
    # Drop+recreate on dimension mismatch (model change); rebuild-from-scratch
    # makes this the common path, but the guard is explicit per the plan.
    existing = conn.execute(
        "SELECT value FROM index_meta WHERE key='embedding_dim'").fetchone()
    if existing and existing[0] and existing[0] != str(dim):
        conn.execute("DROP TABLE IF EXISTS records_vec")
    conn.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS records_vec USING vec0(embedding float[{dim}])")

    vecs = embed.embed([t for (_, t) in rows])
    conn.executemany(
        "INSERT INTO records_vec(rowid, embedding) VALUES (?, ?)",
        [(rid, sqlite_vec.serialize_float32(v)) for (rid, _), v in zip(rows, vecs)])
    conn.executemany(
        "INSERT OR REPLACE INTO index_meta(key, value) VALUES (?, ?)",
        [("embedding_model_id", embed.MODEL_ID), ("embedding_dim", str(dim))])
    return f"built ({len(rows)} vectors, {embed.MODEL_ID}, dim={dim})"


def build(root: Path, db_path: Path, repo_root: Path | None = None,
          vectors: str = "auto") -> dict:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()  # rebuild from scratch — files are the source of truth

    records, stats = ingest.build_records(root, repo_root)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.executemany(
            "INSERT INTO records_fts "
            "(rec_id, type, status, domains, source_path, anchor, "
            " content_hash, schema_generation, distilled_text) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            [(r.rec_id, r.type, r.status, r.domains, r.source_path, r.anchor,
              r.content_hash, r.schema_generation, r.distilled_text) for r in records],
        )
        built_at = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        conn.executemany(
            "INSERT OR REPLACE INTO index_meta(key, value) VALUES (?,?)",
            [("schema_phase", "1a-bm25"), ("built_at", built_at),
             ("record_count", str(stats["deduped"])),
             ("embedding_model_id", ""), ("embedding_dim", "")],
        )
        # Commit BM25 FIRST so a vector-leg failure (missing embedder, model
        # download error, extension issue) can never lose the BM25 index.
        conn.commit()
        try:
            stats["vectors"] = _build_vectors(conn, vectors)
            conn.commit()
        except Exception as e:  # noqa: BLE001 — vectors are strictly additive
            conn.rollback()  # discard any partial vec writes; BM25 stays committed
            stats["vectors"] = f"skipped (error: {type(e).__name__})"
    finally:
        conn.close()
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build the memory/recall index.")
    ap.add_argument("--root", default="docs/strategic-implementation",
                    help="strategic-implementation docs root (default: %(default)s)")
    ap.add_argument("--db", default=None,
                    help="index db path (default: <root>/.memory/index.db)")
    ap.add_argument("--repo-root", default=None,
                    help="repo root for source_path pointers (default: inferred)")
    ap.add_argument("--vectors", choices=["auto", "on", "off"], default="auto",
                    help="vector leg: auto (if embedder importable), on, or off (default: auto)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not fts5_available():
        print("memory-index: SQLite FTS5 unavailable in this interpreter — "
              "cannot build the BM25 index. (Recall degrades to silence.)",
              file=sys.stderr)
        return 2

    root = Path(args.root)
    if not root.is_dir():
        print(f"memory-index: root not found: {root} (nothing to index)", file=sys.stderr)
        return 0  # not an error — an empty/absent corpus is valid

    db_path = Path(args.db) if args.db else root / ".memory" / "index.db"
    repo_root = Path(args.repo_root) if args.repo_root else None
    stats = build(root, db_path, repo_root, vectors=args.vectors)

    if not args.quiet:
        print(f"memory-index built: {db_path}")
        print(f"  folders scanned : {stats['folders']}")
        print(f"  records (raw)   : {stats['raw']}")
        print(f"  records (deduped): {stats['deduped']}")
        print(f"  by type         : {stats['by_type']}")
        print(f"  by status       : {stats['by_status']}")
        print(f"  vector leg      : {stats.get('vectors', 'n/a')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
