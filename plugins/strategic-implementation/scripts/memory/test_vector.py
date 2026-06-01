#!/usr/bin/env python3
"""Integration test for the vector leg (D6) — REAL sqlite-vec + REAL model2vec.

MUST run on an extension-capable interpreter (e.g. the Homebrew-python venv):
  SI_MEMORY_PYTHON=/tmp/si-memory-venv/bin/python  # informational
  /tmp/si-memory-venv/bin/python test_vector.py

Covers execution-plan D6 acceptance:
  1. a wording-mismatch query (no shared terms) that BM25 MISSES is surfaced by
     the vector/fusion path
  2. RRF fusion returns the semantically-correct record
  3. embedding model_id + dim are persisted in index_meta
  4. a second build with egress forced off (HF_HUB_OFFLINE=1) still builds
     vectors from cache (offline, not merely warm-cache-by-luck)

If the interpreter cannot load sqlite-vec, the test SKIPS-WITH-REASON (exit 0)
rather than asserting green — honest per the plan.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import build_index
import embed
import recall


def _w(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main() -> int:
    # Capability gate — skip-with-reason if this interpreter can't do vectors.
    probe = sqlite3.connect(":memory:")
    if not (embed.available() and build_index.load_vec_extension(probe)):
        probe.close()
        print("SKIPPED-WITH-REASON: vector leg unavailable on this interpreter "
              "(needs model2vec + sqlite-vec + enable_load_extension). "
              "Recall stays BM25-only here.")
        return 0
    probe.close()

    fails = []

    def check(name, cond):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs" / "strategic-implementation"
        # Record A: about authentication — but phrased with NO overlap with the query.
        _w(root / "2026-05-10-auth/validation-log.md",
           "---\nstatus: complete\ndomains: [auth]\n---\n# Validation log\n\n"
           "## APPROACH — D1\n**Domains:** auth\n"
           "**Approach:** authenticate the user by verifying their credentials and "
           "issuing a session token after a successful handshake.\n")
        _w(root / "2026-05-10-auth/post-execution-report.md",
           "# Post-execution report\n## Status\n**PASS**\n")
        # Distractor B: clearly unrelated.
        _w(root / "2026-05-12-perf/validation-log.md",
           "---\nstatus: complete\ndomains: [perf]\n---\n# Validation log\n\n"
           "## APPROACH — D1\n**Domains:** perf\n"
           "**Approach:** optimize the slow database query by adding a cache layer "
           "and batching disk reads.\n")
        _w(root / "2026-05-12-perf/post-execution-report.md",
           "# Post-execution report\n## Status\n**PASS**\n")

        db = root / ".memory" / "index.db"
        stats = build_index.build(root, db, repo_root=Path(tmp), vectors="on")
        check("vector leg built", str(stats.get("vectors", "")).startswith("built"))

        conn = sqlite3.connect(str(db))

        # Query shares NO ≥3-char tokens with record A's text.
        q = "signing in and proving who somebody really is"
        bm = recall.search(conn, q, k=3, fuse=False)
        fused = recall.search(conn, q, k=3, fuse=True)
        bm_has_auth = any("auth" in r["source_path"] for r in bm)
        fused_has_auth = any("auth" in r["source_path"] for r in fused)

        # 1+2: BM25 misses the wording-mismatch; fusion (vector) surfaces it.
        check("1. BM25-only misses the wording-mismatch record", not bm_has_auth)
        check("2. fusion surfaces the semantically-correct auth record", fused_has_auth)

        # 3: model_id + dim persisted
        meta = dict(conn.execute("SELECT key,value FROM index_meta").fetchall())
        check("3. embedding_model_id persisted", meta.get("embedding_model_id") == embed.MODEL_ID)
        check("3. embedding_dim persisted", meta.get("embedding_dim") == str(embed.DIM))
        conn.close()

        # 4: offline rebuild (egress forced off) still builds vectors from cache
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        embed._MODEL = None  # force a fresh load under offline mode
        stats2 = build_index.build(root, db, repo_root=Path(tmp), vectors="on")
        check("4. offline rebuild (HF_HUB_OFFLINE=1) still builds vectors",
              str(stats2.get("vectors", "")).startswith("built"))

    if fails:
        print(f"\nFAILED: {fails}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
