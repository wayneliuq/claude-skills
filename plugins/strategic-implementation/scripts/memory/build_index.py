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


def build(root: Path, db_path: Path, repo_root: Path | None = None) -> dict:
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
        conn.commit()
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
    stats = build(root, db_path, repo_root)

    if not args.quiet:
        print(f"memory-index built: {db_path}")
        print(f"  folders scanned : {stats['folders']}")
        print(f"  records (raw)   : {stats['raw']}")
        print(f"  records (deduped): {stats['deduped']}")
        print(f"  by type         : {stats['by_type']}")
        print(f"  by status       : {stats['by_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
