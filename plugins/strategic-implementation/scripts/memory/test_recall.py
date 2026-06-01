#!/usr/bin/env python3
"""Integration test for BM25 recall — REAL SQLite index, no mocks.

Covers execution-plan D3 acceptance:
  1. a known repeat-case query returns the relevant prior approach + pointer
  2. a query with no term overlap returns nothing (relevance gate)
  3. aborted-status records are never surfaced as precedent

Run: python3 test_recall.py   (exit 0 = pass)
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import build_index
import recall
from test_build_index import make_fixture

HERE = Path(__file__).parent


def main() -> int:
    fails = []

    def check(name, cond):
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "docs" / "strategic-implementation"
        root.mkdir(parents=True)
        make_fixture(root)
        db = root / ".memory" / "index.db"
        build_index.build(root, db, repo_root=Path(tmp))
        conn = sqlite3.connect(str(db))

        # 1. known repeat case: the auth APPROACH was "spin up the auth service
        #    in docker, hit /login" — a docker/login query must surface it w/ pointer.
        res = recall.search(conn, "run the login test in a docker container", k=3)
        hit = next((r for r in res if "genb-auth" in r["source_path"]
                    and r["type"] in ("approach", "gotcha")), None)
        check("1. repeat-case query returns the auth approach", hit is not None)
        check("1. result carries a source pointer", bool(hit and hit["source_path"] and hit["anchor"]))

        # 2. no term overlap → nothing
        res_none = recall.search(conn, "xyzzy plugh frobnicate", k=3)
        check("2. unrelated query returns nothing", res_none == [])

        # 3. aborted records never surfaced as precedent. The stub (aborted) spec
        #    says "abandoned approach"; querying its terms must not return it.
        res_ab = recall.search(conn, "abandoned approach never executed", k=5)
        check("3. aborted stub not surfaced",
              all("stub-aborted" not in r["source_path"] for r in res_ab))
        # ...but it IS retrievable when explicitly auditing demoted records:
        res_ab2 = recall.search(conn, "abandoned approach never executed", k=5,
                                include_demoted=True)
        check("3. demoted record retrievable only with --include-demoted",
              any("stub-aborted" in r["source_path"] for r in res_ab2))

        conn.close()

        # 4. recall.sh degrades to silence on a missing index (advisory-never-blocks)
        r = subprocess.run(["bash", str(HERE / "recall.sh"), "anything",
                            "--db", str(root / ".memory" / "does-not-exist.db")],
                           capture_output=True, text=True)
        check("4. recall.sh exit 0 + empty on missing index",
              r.returncode == 0 and r.stdout.strip() == "")

    if fails:
        print(f"\nFAILED: {fails}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
