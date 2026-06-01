#!/usr/bin/env python3
"""Precision A/B gate — the make-or-break check for the memory/recall layer.

Loads a COMMITTED labeled fixture (memory-fixtures/labeled-set.json) whose
thresholds, corpus, and per-query relevance labels are pinned BEFORE this script
runs — so the gate is independently reproducible, not self-defined at run time.
It materializes the fixture corpus, builds a real FTS5 index, runs recall per
query, and asserts:

  - precision@k >= precision_target over the labeled "expect_nonempty" queries
    (precision = relevant returned / returned),
  - "expect_nonempty: false" queries return NOTHING (no false positives;
    includes the aborted-record-exclusion check),
  - mean recall-injection size <= max_injection_tokens (the recall a deliverable
    pays for must be small — it is meant to REPLACE far costlier re-derivation).

It does NOT measure the live "agent adopts recall instead of re-deriving" /
true point-of-use token delta — that is post-hoc on a real run after plugin
reload (see post-reload-verification.md). This script proves recall is precise
and cheap enough to be net-token-negative; the live half confirms adoption.

Exit 0 = gate PASS; exit 1 = gate FLAG (targets missed → PM decision).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

import build_index
import recall

FIXTURE = Path(__file__).with_name("memory-fixtures") / "labeled-set.json"


def _approx_tokens(text: str) -> int:
    return (len(text) + 3) // 4  # ~4 chars/token heuristic


def run(fixture_path: Path) -> dict:
    spec = json.loads(fixture_path.read_text(encoding="utf-8"))
    th = spec["thresholds"]
    results = {"queries": [], "thresholds": th}

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs" / "strategic-implementation"
        for entry in spec["corpus"]:
            f = root / entry["path"]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(entry["content"], encoding="utf-8")
        db = root / ".memory" / "index.db"
        build_index.build(root, db, repo_root=Path(tmp))
        conn = sqlite3.connect(str(db))

        precisions, injections, false_positives = [], [], []
        for q in spec["queries"]:
            res = recall.search(conn, q["query"], q.get("domains") or None,
                                k=th["k"], min_score=th.get("min_score"))
            paths = [r["source_path"] for r in res]
            rendered = recall.render(res, "text")
            inj = _approx_tokens(rendered)
            row = {"name": q["name"], "returned": len(res),
                   "paths": paths, "injection_tokens": inj}

            if q.get("expect_nonempty"):
                rel = [p for p in paths
                       if any(s in p for s in q.get("relevant_substrings", []))]
                prec = (len(rel) / len(paths)) if paths else 0.0
                row["precision"] = round(prec, 3)
                precisions.append(prec)
                injections.append(inj)
                if not paths:
                    row["error"] = "expected results, got none"
            else:
                # must return nothing (unrelated / aborted-excluded)
                if paths:
                    row["error"] = f"expected nothing, got {paths}"
                    false_positives.append(q["name"])
            results["queries"].append(row)

        conn.close()

    mean_prec = sum(precisions) / len(precisions) if precisions else 0.0
    mean_inj = sum(injections) / len(injections) if injections else 0
    results["precision_mean"] = round(mean_prec, 3)
    results["mean_injection_tokens"] = round(mean_inj, 1)
    results["false_positives"] = false_positives
    results["pass"] = (
        mean_prec >= th["precision_target"]
        and not false_positives
        and mean_inj <= th["max_injection_tokens"]
    )
    return results


def write_findings(results: dict, out_path: Path) -> None:
    th = results["thresholds"]
    lines = [
        "# Precision A/B findings — memory-recall-layer (D5)",
        "_The make-or-break gate. Source fixture: "
        "`plugins/strategic-implementation/scripts/memory/memory-fixtures/labeled-set.json` "
        "(thresholds + labels committed before this ran)._",
        "",
        f"**Verdict: {'PASS' if results['pass'] else 'FLAG'}**",
        "",
        f"- precision@{th['k']} (mean over expect-nonempty queries): "
        f"**{results['precision_mean']}** (target ≥ {th['precision_target']})",
        f"- false positives (unrelated/aborted queries that returned anything): "
        f"**{results['false_positives'] or 'none'}**",
        f"- mean recall-injection size: **{results['mean_injection_tokens']} tokens** "
        f"(budget ≤ {th['max_injection_tokens']}) — the cost recall pays to replace re-derivation",
        "",
        "## Per-query",
        "",
        "| query | returned | precision | injection (tok) | note |",
        "|---|---|---|---|---|",
    ]
    for q in results["queries"]:
        lines.append(
            f"| {q['name']} | {q['returned']} | "
            f"{q.get('precision', '—')} | {q['injection_tokens']} | "
            f"{q.get('error', 'ok')} |")
    lines += [
        "",
        "## Scope (honesty)",
        "- Measured here: recall **precision** and **injection cost** on a pinned labeled set.",
        "- NOT measured here (post-hoc, after plugin reload — see `post-reload-verification.md`): "
        "the live 'agent adopts the recalled approach instead of re-deriving' behavior and the "
        "true point-of-use token delta vs a recall-disabled run. This script establishes that "
        "recall is precise + cheap enough to be net-token-negative; the live run confirms adoption.",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Precision A/B gate.")
    ap.add_argument("--fixture", default=str(FIXTURE))
    ap.add_argument("--out", default=None, help="findings doc path")
    args = ap.parse_args(argv)

    results = run(Path(args.fixture))
    if args.out:
        write_findings(results, Path(args.out))

    print(f"precision_mean={results['precision_mean']} "
          f"(target {results['thresholds']['precision_target']}) | "
          f"false_positives={results['false_positives'] or 'none'} | "
          f"mean_injection_tokens={results['mean_injection_tokens']} "
          f"(budget {results['thresholds']['max_injection_tokens']})")
    print("GATE: PASS" if results["pass"] else "GATE: FLAG (targets missed)")
    return 0 if results["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
