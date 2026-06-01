#!/usr/bin/env python3
"""Integration test for the memory index builder — REAL SQLite, no mocks.

Covers execution-plan D2 acceptance (a)-(f):
  (a) only typed records ingested
  (b) noise excluded by filename (checkpoint/token-report/html/brief/assets)
  (c) generation-aware status — a Gen-A folder is `complete-legacy`, not `aborted`
  (d) duplicate content collapses to one record
  (e) backfill is episodic-only — project-learnings.md never ingested or written
  (f) cross-domain exclusion — a domain-A filter returns zero domain-B records

Run: python3 test_build_index.py   (exit 0 = pass)
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import build_index
import ingest

DUP_GOTCHA = (
    "## GOTCHA — D9\n"
    "**Domains:** dedupe-test\n"
    "**Lost time on:** rebuilt the image from scratch each run\n"
    "**Do instead:** reuse the cached layer; run the e2e test in a container first\n"
)


def _w(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def make_fixture(root: Path):
    # --- Gen-A (session-based; predates post-execution-report) -> complete-legacy
    a = root / "2026-04-05-gena-feature"
    _w(a / "implementation-guide.md", "# Guide\n## Goal\nBuild the thing.\n")
    _w(a / "session-3-log.md",
       "# Session 3 log\n\n## DEV-001\n**Type:** retry\n**Domains:** backend\n"
       "**Plan said:** x\n**Actually:** y\n**Resolution:** z\n")
    _w(a / "session-3-postmortem.md", "# Postmortem\n## Outcome\nShipped.\n")

    # --- Gen-B (validation-log + post-exec PASS) -> complete; domain=auth
    b = root / "2026-05-10-genb-auth"
    _w(b / "validation-log.md",
       "---\nstatus: complete\ndomains: [auth]\noutcome: shipped\nsupersedes: none\n---\n"
       "# Validation log\n\n## APPROACH — D1\n**Method:** integration-test\n"
       "**Domains:** auth\n**Approach:** spin up the auth service in docker, hit /login.\n\n"
       "## GOTCHA — D2\n**Domains:** auth\n**Lost time on:** mocking the token refresh\n"
       "**Do instead:** exercise the real refresh against a container.\n\n" + DUP_GOTCHA)
    _w(b / "post-execution-report.md",
       "# Post-execution report\n## Status\n**PASS**\n")
    # noise + non-episodic in the same folder — must all be excluded:
    _w(b / "checkpoint.md", "# Checkpoint\n## Done\n- D1\n")
    _w(b / "token-report.md", "# Token report\n## Tool-call mix\n- Bash: 9\n")
    _w(b / "product-brief_genb-auth.md", "# Brief\nauth stuff\n")
    _w(b / "mockup.html", "<html>auth login</html>")
    _w(b / "tokens.css", ".x{color:red}")

    # --- Gen-C (brief-meta) -> complete; domain=search; + simplify finding + plan
    c = root / "2026-05-20-genc-search"
    _w(c / "brief-meta.yaml", "specialists_recommended:\n  - tests\n")
    _w(c / "validation-log.md",
       "---\nstatus: complete\ndomains: [search]\noutcome: shipped\nsupersedes: none\n---\n"
       "# Validation log\n\n## APPROACH — D1\n**Method:** cli\n**Domains:** search\n"
       "**Approach:** build the FTS5 index and grep it.\n\n" + DUP_GOTCHA)  # duplicate of b's GOTCHA
    _w(c / "execution-plan.md",
       "# Execution Plan\n## Context\nAdd search.\n### D1 — search index\n### D2 — recall\n")
    _w(c / "simplify-report-01.md",
       "# Simplify report 01\n## Findings\n### F-01 — reuse-miss — med — dup ranking\n"
       "**File:** recall.py\n**Why:** duplicated.\n")
    _w(c / "post-execution-report.md", "# Post-execution report\n## Status\n**PASS**\n")

    # --- Stub (1 file, no completion signal) -> aborted
    s = root / "2026-05-25-stub-aborted"
    _w(s / "spec.md", "# Spec\nNever executed; abandoned approach.\n")

    # --- Curated tier at root (NOT a dated folder) — must never be ingested/written
    _w(root / "project-learnings.md", "# Project Learnings\n### L-001: keep\n")


def query(db: Path, sql: str, params=()):
    conn = sqlite3.connect(str(db))
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs" / "strategic-implementation"
        root.mkdir(parents=True)
        make_fixture(root)
        learnings = root / "project-learnings.md"
        learnings_before = learnings.read_text()

        db = root / ".memory" / "index.db"
        stats = build_index.build(root, db, repo_root=Path(tmp))
        fails = []

        def check(name, cond):
            print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
            if not cond:
                fails.append(name)

        # (a) only typed records — every record has a known type
        types = {t for (t,) in query(db, "SELECT DISTINCT type FROM records_fts")}
        allowed = {"approach", "gotcha", "deviation", "spike", "validation",
                   "postmortem", "plan", "spec", "simplify", "flag"}
        check("(a) only typed records ingested", types and types.issubset(allowed))
        check("(a) approach+gotcha+plan+simplify+spec present",
              {"approach", "gotcha", "plan", "simplify", "spec"}.issubset(types))

        # (b) noise excluded by filename
        noise = query(db,
            "SELECT count(*) FROM records_fts WHERE "
            "source_path LIKE '%checkpoint.md%' OR source_path LIKE '%token-report.md%' "
            "OR source_path LIKE '%.html' OR source_path LIKE '%product-brief_%' "
            "OR source_path LIKE '%.css' OR source_path LIKE '%brief-meta%'")[0][0]
        check("(b) zero noise records (checkpoint/token-report/html/brief/css/meta)", noise == 0)

        # (c) Gen-A folder is complete-legacy, not aborted
        gena = {st for (st,) in query(db,
            "SELECT DISTINCT status FROM records_fts WHERE source_path LIKE '%gena-feature%'")}
        check("(c) Gen-A tagged complete-legacy (not aborted)", gena == {"complete-legacy"})

        # (c2) stub -> aborted
        stub = {st for (st,) in query(db,
            "SELECT DISTINCT status FROM records_fts WHERE source_path LIKE '%stub-aborted%'")}
        check("(c2) stub folder tagged aborted", stub == {"aborted"})

        # (d) duplicate content collapses — the identical DUP_GOTCHA appears in 2 folders
        dup = query(db, "SELECT count(*) FROM records_fts WHERE anchor='GOTCHA — D9'")[0][0]
        check("(d) duplicate GOTCHA collapsed to one record", dup == 1)

        # (e) project-learnings.md never ingested + never written
        pl = query(db, "SELECT count(*) FROM records_fts WHERE source_path LIKE '%project-learnings.md%'")[0][0]
        check("(e) project-learnings.md not ingested", pl == 0)
        check("(e) project-learnings.md untouched on disk", learnings.read_text() == learnings_before)

        # (f) cross-domain exclusion — auth filter returns no search records
        auth_rows = query(db,
            "SELECT domains FROM records_fts WHERE domains LIKE '%auth%'")
        check("(f) auth-domain filter returns rows", len(auth_rows) > 0)
        check("(f) auth-domain filter excludes search-domain records",
              all("search" not in d for (d,) in auth_rows))

        print(f"\n  stats: {stats}")

    # Smoke test against the real corpus (must not crash; must exclude noise).
    real = Path("docs/strategic-implementation")
    if real.is_dir():
        recs, rstats = ingest.build_records(real)
        bad = [r for r in recs if any(x in r.source_path for x in
               ("checkpoint.md", "token-report.md", ".html", "product-brief_", "brief-meta"))]
        print(f"  [real corpus] {rstats['deduped']} records, {rstats['by_status']}")
        if bad:
            print(f"  [FAIL] real corpus leaked noise: {[r.source_path for r in bad][:3]}")
            fails.append("real-corpus-noise")
        else:
            print("  [PASS] real corpus excludes noise")

    if fails:
        print(f"\nFAILED: {fails}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
