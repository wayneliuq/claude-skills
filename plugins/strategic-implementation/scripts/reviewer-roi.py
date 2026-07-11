#!/usr/bin/env python3
"""reviewer-roi.py — transcript-based reviewer cost/value telemetry.

Measures the REAL per-reviewer-agent token cost of strategic-implementation
review rounds (from session transcripts) and, paired with a haiku value-
classification pass, the value-per-token each reviewer produces.

Why transcripts: every Claude Code session is written to
  ~/.claude/projects/<encoded-cwd>/<session-id>.jsonl
one JSON event per line. Assistant messages carry real `usage` (input/output/
cache tokens) + model id; every Task/Agent tool_result embeds
  <usage>subagent_tokens: N  tool_uses: N  duration_ms: N</usage>
so each reviewer invocation's real cost + its output text are both recoverable.
This is exact — not the tool-output-byte proxy in token-report.sh.

TWO LAYERS
  1. deterministic (this script, `extract`): per-invocation cost + duration +
     output, aggregated per agent; also writes per-review-round slices for the
     value pass. No LLM.
  2. haiku value pass (manual, between the two subcommands): fan out one haiku
     agent per batch of round slices; each reads a round's sibling reviewers and
     classifies every reviewer's findings novel / overlap / no-op, writing a JSON
     array to <out>/verdicts/verdict-*.json. Prompt template in HAIKU_PROMPT below.
  3. deterministic (this script, `roi`): join verdicts + slices → ROI table
     (tokens per novel finding, overlap %, no-op %, value distribution).

USAGE
  reviewer-roi.py extract [--projects GLOB] [--out DIR]
  reviewer-roi.py roi     [--out DIR]

  --projects  glob for project transcript dirs
              (default: ~/.claude/projects/* — all projects)
  --out       working dir for artifacts (default: ./reviewer-roi)

Deterministic; no network. Exits 0 on partial data (missing usage blocks are
reported as coverage, not fatal).
"""
import argparse, glob, json, os, re, sys
from collections import defaultdict
from datetime import datetime

STRAT = {"alignment", "plan-simplify", "user-validation", "boundaries",
         "technical-expert", "runtime-risk", "frontend-engineer",
         "frontend-quality", "tests", "plan-gate"}

USAGE_RE = re.compile(r'subagent_tokens:\s*(\d+).*?tool_uses:\s*(\d+).*?duration_ms:\s*(\d+)', re.S)

HAIKU_PROMPT = """\
Between `extract` and `roi`, run a haiku value pass. For each round slice in
<out>/rounds/round-*.json (each holds the sibling reviewers that reviewed ONE
plan in parallel, with each reviewer's real `tokens` and its `output` text),
classify every reviewer:
  n_findings  distinct actionable findings (a PASS with no action = 0)
  n_novel     findings no OTHER reviewer in the same round raised
  n_overlap   n_findings - n_novel
  no_op       true if no actionable finding
  verdict     high_value | moderate | low_value | no_op
  note        <=15 words
Write a JSON array per batch to <out>/verdicts/verdict-<X>.json with objects:
  {"round_file","agent","n_findings","n_novel","n_overlap","no_op","verdict","note"}
Judge substance over wording (same root cause = overlap even if phrased differently)."""


def parse_ts(s):
    try:
        return datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except Exception:
        return None


def iter_events(files):
    for fp in files:
        try:
            fh = open(fp, encoding="utf-8")
        except Exception:
            continue
        tname = os.path.basename(fp)
        for line in fh:
            try:
                yield tname, json.loads(line)
            except Exception:
                continue


def extract(projects_glob, out):
    files = []
    for d in glob.glob(projects_glob):
        files += glob.glob(os.path.join(d, "*.jsonl"))
    calls, results = {}, {}
    for tname, ev in iter_events(files):
        msg = ev.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use" and c.get("name") in ("Task", "Agent"):
                at = (c.get("input") or {}).get("subagent_type") or "(none)"
                calls[c["id"]] = {"agent": at, "ts": ev.get("timestamp"), "transcript": tname}
            elif c.get("type") == "tool_result":
                tid = c.get("tool_use_id")
                body = c.get("content")
                if isinstance(body, list):
                    body = " ".join(b.get("text", "") for b in body if isinstance(b, dict))
                body = body or ""
                m = USAGE_RE.search(body)
                clean = re.sub(r'agentId:.*$', '', re.sub(r'<usage>.*?</usage>', '', body, flags=re.S), flags=re.S).strip()
                results[tid] = (len(clean), clean, int(m.group(1)) if m else None, int(m.group(3)) if m else None)

    recs = []
    for tid, info in calls.items():
        r = results.get(tid)
        if not r:
            continue
        out_len, clean, tok, dur = r
        recs.append({**info, "tid": tid, "tokens": tok, "dur_ms": dur, "out_len": out_len, "output": clean})

    os.makedirs(out, exist_ok=True)
    json.dump(recs, open(os.path.join(out, "invocations.json"), "w"))

    # aggregate strat reviewers
    agg = defaultdict(lambda: {"n": 0, "tok": 0, "tn": 0, "out": 0, "dur": 0, "dn": 0})
    for r in recs:
        short = r["agent"].split(":")[-1]
        if short not in STRAT:
            continue
        a = agg[short]
        a["n"] += 1
        a["out"] += r["out_len"]
        if r["tokens"] is not None:
            a["tok"] += r["tokens"]
            a["tn"] += 1
        if r["dur_ms"] is not None:
            a["dur"] += r["dur_ms"]
            a["dn"] += 1

    print(f"transcripts: {len(files)} · Task/Agent calls: {len(calls)} · "
          f"with usage: {sum(a['tn'] for a in agg.values())}\n")
    print(f"{'reviewer':<20}{'inv':>4}{'wTok':>5}{'avgTok':>9}{'avgOut':>8}{'durS':>6}")
    for at, a in sorted(agg.items(), key=lambda kv: -(kv[1]['tok'] / kv[1]['tn'] if kv[1]['tn'] else 0)):
        avgtok = a["tok"] / a["tn"] if a["tn"] else 0
        avgout = a["out"] / a["n"] if a["n"] else 0
        durs = a["dur"] / a["dn"] / 1000 if a["dn"] else 0
        print(f"{at:<20}{a['n']:>4}{a['tn']:>5}{avgtok:>9.0f}{avgout:>8.0f}{durs:>6.0f}")

    # cluster into review rounds by timestamp proximity (<=180s within a transcript)
    rev = [r for r in recs if r["agent"].split(":")[-1] in STRAT
           and r["tokens"] is not None and parse_ts(r["ts"])]
    by_t = defaultdict(list)
    for r in rev:
        by_t[r["transcript"]].append(r)
    rounds = []
    for _, rs in by_t.items():
        rs.sort(key=lambda r: parse_ts(r["ts"]))
        cur = [rs[0]]
        for a, b in zip(rs, rs[1:]):
            if (parse_ts(b["ts"]) - parse_ts(a["ts"])).total_seconds() <= 180:
                cur.append(b)
            else:
                rounds.append(cur)
                cur = [b]
        rounds.append(cur)
    kept = [c for c in rounds if len(c) >= 2]

    rdir = os.path.join(out, "rounds")
    os.makedirs(rdir, exist_ok=True)
    for f in os.listdir(rdir):
        if f.startswith("round-") or f == "index.json":
            os.remove(os.path.join(rdir, f))
    idx = []
    for i, members in enumerate(sorted(kept, key=lambda c: -len(c))):
        slc = {"transcript": members[0]["transcript"], "reviewers": [
            {"agent": m["agent"].split(":")[-1], "tokens": m["tokens"],
             "out_len": m["out_len"], "output": m["output"][:6000]} for m in members]}
        json.dump(slc, open(os.path.join(rdir, f"round-{i:02d}.json"), "w"), indent=1)
        idx.append({"file": f"round-{i:02d}.json",
                    "agents": [m["agent"].split(":")[-1] for m in members]})
    json.dump(idx, open(os.path.join(rdir, "index.json"), "w"), indent=1)
    print(f"\nanalyzable review rounds (>=2 reviewers w/tokens): {len(kept)} → "
          f"wrote {len(idx)} slices to {rdir}/")
    print(f"\nNEXT: run the haiku value pass, then `reviewer-roi.py roi`.\n\n{HAIKU_PROMPT}")


def roi(out):
    rdir = os.path.join(out, "rounds")
    tok = {}
    for f in sorted(glob.glob(os.path.join(rdir, "round-*.json"))):
        d = json.load(open(f))
        rf = os.path.basename(f)
        for r in d["reviewers"]:
            tok[(rf, r["agent"])] = r["tokens"]

    verd = []
    for f in sorted(glob.glob(os.path.join(out, "verdicts", "verdict-*.json"))):
        try:
            verd += json.load(open(f))
        except Exception as e:
            print(f"parse fail {f}: {e}", file=sys.stderr)
    if not verd:
        print("no verdicts found — run the haiku value pass first (see `extract` output).",
              file=sys.stderr)
        return 1

    agg = defaultdict(lambda: {"n": 0, "tok": 0, "find": 0, "nov": 0, "ov": 0,
                               "noop": 0, "hv": 0, "mod": 0, "lv": 0})
    unmatched = 0
    for v in verd:
        key = (v.get("round_file"), v.get("agent"))
        t = tok.get(key)
        if t is None:
            unmatched += 1
            continue
        g = agg[v["agent"]]
        g["n"] += 1
        g["tok"] += t
        g["find"] += v.get("n_findings", 0)
        g["nov"] += v.get("n_novel", 0)
        g["ov"] += v.get("n_overlap", 0)
        if v.get("no_op"):
            g["noop"] += 1
        vd = v.get("verdict", "")
        g["hv"] += vd == "high_value"
        g["mod"] += vd == "moderate"
        g["lv"] += vd in ("low_value", "no_op")

    print(f"joined {sum(g['n'] for g in agg.values())} verdicts · unmatched {unmatched}\n")
    hdr = f"{'reviewer':<18}{'inv':>4}{'avgTok':>8}{'find':>5}{'novel':>6}{'ovlp%':>6}{'noop%':>6}{'tok/novel':>10}  H/M/L"
    print(hdr)
    print("-" * len(hdr))
    rows = []
    for a, g in agg.items():
        tpn = g["tok"] / g["nov"] if g["nov"] else float('inf')
        rows.append((a, g, tpn))
    for a, g, tpn in sorted(rows, key=lambda r: -(r[2] if r[2] != float('inf') else 9e9)):
        avgtok = g["tok"] / g["n"]
        ovp = g["ov"] / g["find"] * 100 if g["find"] else 0
        noopp = g["noop"] / g["n"] * 100
        tpn_s = "  inf(0nov)" if tpn == float('inf') else f"{tpn:>10.0f}"
        print(f"{a:<18}{g['n']:>4}{avgtok:>8.0f}{g['find']:>5}{g['nov']:>6}"
              f"{ovp:>5.0f}%{noopp:>5.0f}%{tpn_s}  {g['hv']}/{g['mod']}/{g['lv']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="reviewer cost/value telemetry from session transcripts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    default_glob = os.path.expanduser("~/.claude/projects/*")
    pe = sub.add_parser("extract")
    pe.add_argument("--projects", default=default_glob)
    pe.add_argument("--out", default="reviewer-roi")
    pr = sub.add_parser("roi")
    pr.add_argument("--out", default="reviewer-roi")
    args = ap.parse_args()
    if args.cmd == "extract":
        extract(args.projects, args.out)
        return 0
    if args.cmd == "roi":
        return roi(args.out)


if __name__ == "__main__":
    sys.exit(main() or 0)
