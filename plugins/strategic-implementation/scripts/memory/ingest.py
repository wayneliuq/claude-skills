"""Typed, selective, status-aware ingest + 3-generation normalizer.

Turns a `docs/strategic-implementation/` tree into a list of uniform memory
`Record`s. NOTHING here writes to the database or to project-learnings.md —
this module is pure extraction. Backfill is therefore episodic-only by
construction (curated learnings are never produced here).

Design rules honored (from the execution plan):
  - TYPED + SELECTIVE: only the record types in INCLUDE are ingested.
  - EXCLUDE noise by filename: checkpoint / token-report / mockups / assets /
    briefs / brief-meta — see MEMORY-DOCTYPES.md.
  - STATUS-AWARE + generation-aware: complete / complete-legacy / superseded /
    aborted / in-progress. Gen-A predates post-execution-report.md, so its
    folders map to complete-legacy (searchable), never auto-aborted.
  - DEDUPE by content hash (handles duplicated mockup-spec copies, etc.).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Selection policy (the readable manifest lives in MEMORY-DOCTYPES.md).
# ---------------------------------------------------------------------------

EXCLUDE_BASENAMES = {"checkpoint.md", "token-report.md", "brief-meta.yaml"}
EXCLUDE_GLOBS = ("product-brief_*.md",)
EXCLUDE_SUFFIXES = {".html", ".svg", ".css", ".json", ".txt"}
# Never ingest the curated learnings file — it is the human-curated tier.
EXCLUDE_EXACT_RELPATHS = {"project-learnings.md", "documentation-registry.md"}

MAX_DISTILLED = 2000  # keep records compact → tight recall snippets, small index

DEMOTED_STATUSES = {"aborted", "superseded"}  # never surfaced as proven precedent


@dataclass
class Record:
    rec_id: str
    type: str            # approach | gotcha | deviation | spike | validation | postmortem | plan | spec | simplify | flag
    status: str          # complete | complete-legacy | superseded | aborted | in-progress
    domains: str         # comma-joined
    source_path: str     # repo-relative
    anchor: str          # e.g. "APPROACH — D7"
    schema_generation: str  # A | B | C | unknown
    distilled_text: str
    content_hash: str = field(default="")

    def finalize(self) -> "Record":
        self.distilled_text = self.distilled_text.strip()[:MAX_DISTILLED]
        h = hashlib.sha256()
        h.update((self.type + "\n" + self.distilled_text).encode("utf-8", "ignore"))
        self.content_hash = h.hexdigest()
        return self


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML frontmatter parser (key: value, and `[a, b]` lists). No deps."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    out: dict = {}
    for line in m.group(1).splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            out[key] = items
        else:
            out[key] = val.strip("'\"")
    return out


def _domains_to_str(val) -> str:
    if isinstance(val, list):
        return ",".join(val)
    return str(val or "")


def _split_h2_blocks(text: str):
    """Yield (header, body) for each `## ...` block."""
    parts = re.split(r"^##\s+", text, flags=re.M)
    for chunk in parts[1:]:
        header, _, body = chunk.partition("\n")
        yield header.strip(), body.strip()


def _field(body: str, label: str) -> str:
    m = re.search(rf"^\*\*{re.escape(label)}:?\*\*\s*(.+)$", body, re.M)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Generation + status inference (folder level)
# ---------------------------------------------------------------------------

def detect_generation(names: set[str]) -> str:
    if "brief-meta.yaml" in names:
        return "C"
    if "validation-log.md" in names:
        return "B"
    if any(n.startswith("session-") for n in names) or "implementation-guide.md" in names:
        return "A"
    return "unknown"


def _postexec_pass(folder: Path) -> bool:
    pe = folder / "post-execution-report.md"
    if not pe.exists():
        return False
    txt = _read(pe)
    m = re.search(r"^##\s+Status\b(.*?)(?:^##\s|\Z)", txt, re.M | re.S)
    region = m.group(1) if m else txt
    return "PASS" in region


def infer_status(folder: Path, names: set[str], superseded: set[str]) -> str:
    slug = folder.name
    if slug in superseded:
        return "superseded"

    # Explicit abort signals win.
    fm_status = ""
    for fn in ("validation-log.md", "post-execution-report.md"):
        if fn in names:
            fm_status = parse_frontmatter(_read(folder / fn)).get("status", "") or fm_status
    if fm_status == "aborted":
        return "aborted"
    bm = folder / "brainstorm.md"
    if bm.exists() and "not approved" in _read(bm).lower():
        return "aborted"

    gen = detect_generation(names)
    if _postexec_pass(folder):
        return "complete"
    if fm_status in ("complete", "in-progress", "flagged"):
        return "complete" if fm_status == "flagged" else fm_status
    # Gen-A predates post-execution-report.md — searchable legacy, NOT aborted.
    if gen == "A" and (any(n.startswith("session-") for n in names) or "implementation-guide.md" in names):
        return "complete-legacy"
    # Stub with no completion signal → aborted (last-resort heuristic only).
    real = [n for n in names if not n.startswith(".")]
    if len(real) <= 2:
        return "aborted"
    return "in-progress"


def collect_superseded(root: Path) -> set[str]:
    """Slugs that a later folder's frontmatter declares it supersedes."""
    out: set[str] = set()
    for folder in _iter_folders(root):
        for fn in ("validation-log.md", "post-execution-report.md"):
            f = folder / fn
            if f.exists():
                sup = parse_frontmatter(_read(f)).get("supersedes", "none")
                if sup and sup != "none":
                    out.add(sup)
    return out


# ---------------------------------------------------------------------------
# Per-file extractors → records
# ---------------------------------------------------------------------------

def _is_excluded(p: Path) -> bool:
    if p.name in EXCLUDE_BASENAMES:
        return True
    if p.suffix in EXCLUDE_SUFFIXES:
        return True
    if any(p.match(g) for g in EXCLUDE_GLOBS):
        return True
    return False


def _block_type(header: str) -> str | None:
    h = header.upper()
    if h.startswith("APPROACH"):
        return "approach"
    if h.startswith("GOTCHA"):
        return "gotcha"
    if h.startswith("DEV-") or h.startswith("DEV "):
        return "deviation"
    if h.startswith("SPIKE FINDING"):
        return "spike"
    if h.startswith("FLAG"):
        return "flag"
    if re.match(r"D\d+\b", h):       # "## D1 — ..." per-deliverable validation note
        return "validation"
    return None


def extract_records(folder: Path, root: Path, repo_root: Path, status: str,
                    gen: str, folder_domains: str) -> list[Record]:
    recs: list[Record] = []

    def add(rtype, source_rel, anchor, body, domains=""):
        if not body.strip():
            return
        src = folder / source_rel
        try:
            source_path = str(src.relative_to(repo_root))
        except ValueError:
            source_path = str(src.relative_to(root))
        recs.append(Record(
            rec_id=f"{folder.name}/{source_rel}#{anchor}",
            type=rtype, status=status,
            domains=(domains or folder_domains),
            source_path=source_path,
            anchor=anchor, schema_generation=gen, distilled_text=body,
        ))

    for p in sorted(folder.iterdir()):
        if not p.is_file() or _is_excluded(p):
            continue
        rel = p.name
        text = _read(p)

        # validation-log.md (Gen-B/C) + session-*-log.md (Gen-A) → typed blocks
        if rel == "validation-log.md" or (rel.startswith("session-") and rel.endswith("-log.md")):
            for header, body in _split_h2_blocks(text):
                t = _block_type(header)
                if t:
                    add(t, rel, header, f"{header}\n{body}", _field(body, "Domains"))
            continue

        # post-execution-report.md / session-*-postmortem.md → postmortem (per section)
        if rel == "post-execution-report.md" or (rel.startswith("session-") and rel.endswith("-postmortem.md")):
            for header, body in _split_h2_blocks(text):
                add("postmortem", rel, header, f"{header}\n{body}")
            continue

        # execution-plan.md → status-gated single plan record
        if rel == "execution-plan.md":
            if status in ("complete", "complete-legacy", "in-progress"):
                ctx = re.search(r"^##\s+Context\b(.*?)(?:^##\s|\Z)", text, re.M | re.S)
                titles = re.findall(r"^###\s+(D\d+\s+—\s+.+)$", text, re.M)
                body = (ctx.group(1).strip() if ctx else "") + "\n\nDeliverables: " + "; ".join(titles)
                add("plan", rel, "execution-plan", body)
            continue

        # session-*-plan.md / implementation-guide.md (Gen-A) → plan record
        if (rel.startswith("session-") and rel.endswith("-plan.md")) or rel == "implementation-guide.md":
            goal = re.search(r"^(?:###|##)\s+Goal\b(.*?)(?:^#{2,3}\s|\Z)", text, re.M | re.S)
            body = goal.group(1).strip() if goal else text
            add("plan", rel, rel.replace(".md", ""), body)
            continue

        # spec.md → spec record (intro)
        if rel == "spec.md":
            add("spec", rel, "spec", text)
            continue

        # simplify-report-*.md → one record per finding
        if rel.startswith("simplify-report-") and rel.endswith(".md"):
            for fheader, fbody in re.findall(r"^###\s+(F-\d+.*?)$\n(.*?)(?=^###\s|\Z)", text, re.M | re.S):
                add("simplify", rel, fheader.strip(), f"{fheader}\n{fbody}")
            continue

        # Everything else under the folder is intentionally NOT ingested.

    return recs


# ---------------------------------------------------------------------------
# Folder iteration + top-level driver
# ---------------------------------------------------------------------------

_FOLDER_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def _iter_folders(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return []
    return [p for p in sorted(root.iterdir()) if p.is_dir() and _FOLDER_RE.match(p.name)]


def build_records(root: Path, repo_root: Path | None = None) -> tuple[list[Record], dict]:
    """Walk the tree, return (deduped records, stats)."""
    root = root.resolve()
    # repo_root anchors source_path pointers; default = grandparent of
    # docs/strategic-implementation (i.e. the repo root), falling back to parent.
    if repo_root is None:
        repo_root = root.parent.parent if root.parent.parent.exists() else root.parent
    repo_root = repo_root.resolve()
    superseded = collect_superseded(root)
    seen_hashes: set[str] = set()
    out: list[Record] = []
    stats = {"folders": 0, "raw": 0, "deduped": 0, "by_type": {}, "by_status": {}}

    for folder in _iter_folders(root):
        stats["folders"] += 1
        names = {p.name for p in folder.iterdir() if p.is_file()}
        status = infer_status(folder, names, superseded)
        gen = detect_generation(names)
        # Folder-level domain default from validation-log frontmatter if present.
        fdom = ""
        vlog = folder / "validation-log.md"
        if vlog.exists():
            fdom = _domains_to_str(parse_frontmatter(_read(vlog)).get("domains", ""))

        for rec in extract_records(folder, root, repo_root, status, gen, fdom):
            rec.finalize()
            stats["raw"] += 1
            if rec.content_hash in seen_hashes:
                continue  # dedupe identical content (e.g. duplicated mockup-spec copies)
            seen_hashes.add(rec.content_hash)
            out.append(rec)
            stats["by_type"][rec.type] = stats["by_type"].get(rec.type, 0) + 1
            stats["by_status"][rec.status] = stats["by_status"].get(rec.status, 0) + 1

    stats["deduped"] = len(out)
    return out, stats
