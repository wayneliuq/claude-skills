#!/usr/bin/env python3
"""Point-of-need recall over the memory index (Phase 1a: BM25/FTS5).

Returns a small ranked set of distilled snippets + source pointers, or NOTHING.
Recall is advisory: on any problem it prints nothing and exits 0, so it can
never block or pollute execution. (recall.sh adds a second safety net.)

Relevance gate (Phase 1a): FTS5 MATCH inherently requires term overlap, so a
query with no shared terms returns zero rows — the natural "below-bar →
nothing" behavior. An optional numeric `--min-score` (bm25; lower = better)
tightens this further; D5 pins it via the labeled fixture.

Status gate: aborted / superseded records are NEVER surfaced as precedent
(use --include-demoted to override, e.g. for audit).

Usage:
  recall.py "<query text>" [--db PATH] [--domains a,b] [--types approach,gotcha]
            [--k 3] [--min-score FLOAT] [--include-demoted] [--format text|json]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = "docs/strategic-implementation/.memory/index.db"
DEMOTED = ("aborted", "superseded")
SNIPPET_CHARS = 280


def _tokens(query: str) -> list[str]:
    # Alphanumeric tokens ≥3 chars; strips FTS5-special characters so the
    # MATCH expression can never be a syntax error from user free-text.
    seen, out = set(), []
    for t in re.findall(r"[A-Za-z0-9]+", query.lower()):
        if len(t) >= 3 and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def search(conn, query, domains=None, types=None, k=3,
           min_score=None, include_demoted=False) -> list[dict]:
    toks = _tokens(query)
    if not toks:
        return []
    sql = ("SELECT rec_id, type, status, domains, source_path, anchor, "
           "distilled_text, bm25(records_fts) AS score "
           "FROM records_fts WHERE records_fts MATCH ?")
    params: list = [" OR ".join(toks)]
    if not include_demoted:
        sql += " AND status NOT IN (?, ?)"
        params += list(DEMOTED)
    if domains:
        sql += " AND (" + " OR ".join(["domains LIKE ?"] * len(domains)) + ")"
        params += [f"%{d}%" for d in domains]
    if types:
        sql += " AND type IN (" + ",".join(["?"] * len(types)) + ")"
        params += list(types)
    sql += " ORDER BY score LIMIT ?"
    params.append(int(k))

    rows = conn.execute(sql, params).fetchall()
    cols = ["rec_id", "type", "status", "domains", "source_path", "anchor",
            "distilled_text", "score"]
    out = []
    for r in rows:
        rec = dict(zip(cols, r))
        if min_score is not None and rec["score"] > float(min_score):
            continue  # bm25: lower = better; drop weak matches
        out.append(rec)
    return out


def _snippet(text: str) -> str:
    s = re.sub(r"\s+", " ", text).strip()
    return s if len(s) <= SNIPPET_CHARS else s[:SNIPPET_CHARS].rstrip() + "…"


def render(results: list[dict], fmt: str) -> str:
    if not results:
        return ""
    if fmt == "json":
        return json.dumps([{k: r[k] for k in
                            ("type", "status", "domains", "source_path", "anchor", "score")}
                           | {"snippet": _snippet(r["distilled_text"])} for r in results],
                          indent=2)
    lines = ["Prior approaches that may apply (advisory — recalled from memory):"]
    for r in results:
        dom = f" · domains: {r['domains']}" if r["domains"] else ""
        lines.append(f"- [{r['type']}]{dom} — {r['source_path']} :: {r['anchor']}")
        lines.append(f"    {_snippet(r['distilled_text'])}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Recall prior approaches from memory.")
    ap.add_argument("query")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--domains", default="")
    ap.add_argument("--types", default="")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--min-score", default=None)
    ap.add_argument("--include-demoted", action="store_true")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args(argv)

    db = Path(args.db)
    if not db.exists():
        return 0  # no index yet → advisory step no-ops silently

    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            results = search(conn, args.query, domains or None, types or None,
                             args.k, args.min_score, args.include_demoted)
        finally:
            conn.close()
    except sqlite3.Error:
        return 0  # malformed/locked index → degrade to silence
    out = render(results, args.format)
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
