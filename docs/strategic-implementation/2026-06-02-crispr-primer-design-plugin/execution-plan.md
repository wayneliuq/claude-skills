# Execution Plan — crispr-primer-design plugin

**Date:** 2026-06-02
**Autonomy:** auto
**Fast-path:** yes (single-area packaging task following the repo's documented plugin pattern; no new architecture, no product/UX surface).

## Outcome

`crispr-primer-design` is installable as a plugin from the `wayneliuq` marketplace and
produces correct, genome-verified CRISPR validation primers. Success signal: the
packaged script runs end-to-end on two new human OR2W5 gRNAs without errors,
emitting valid primer reports + amplicon FASTAs, and the plugin is registered in
`marketplace.json` and pushed to `origin/main`.

## Source

Existing skill at `C:\Users\WayneLiu\.minimax\skills\crispr-primer-design`
(SKILL.md, README.md, scripts/design_primers.py, references/tm_methods.md).

## e2e validation case

- OR2W5 (human) GRNA03: `AACCAGGAGGACGCACTCGG`
- OR2W5 (human) GRNA04: `ACCGGCAGACGGCCACATAG`
- 20-mer protospacers, human/GRCh38, application ICE (default).
- Exercises the Ensembl→NCBI pseudogene fallback (OR2W5 is a pseudogene).

## Integration-risk dependencies

| Dependency | Why it matters |
|---|---|
| Ensembl REST (`rest.ensembl.org`) | Live gene-symbol resolution + region fetch; the primary network path. |
| NCBI E-utilities | Fallback locus resolution for pseudogenes (OR2W5). |
| NCBI Primer-BLAST | Optional off-target submission; must degrade gracefully on failure. |
| Python stdlib (`urllib`) | Only runtime dep; no third-party packages. Must run on Python 3.14. |

## Deliverables

### D1 — Package as plugin
Create `plugins/crispr-primer-design/`:
- `.claude-plugin/plugin.json` (manifest, version 1.0.0, mirroring strategic-implementation's schema)
- `skills/crispr-primer-design/SKILL.md` (copy, unchanged behavior)
- `skills/crispr-primer-design/scripts/design_primers.py` (copy; hardened in D2)
- `skills/crispr-primer-design/references/tm_methods.md` (copy)
- `README.md` (plugin-level)
Register the plugin in top-level `.claude-plugin/marketplace.json`.
Update top-level `README.md` plugins table.
**Validation (cli):** `python -c "json.load(...)"` on both JSON files; verify file tree; confirm SKILL.md frontmatter (`name`, `description`) parses.

### D2 — Harden the script
Fix known crash bugs in the shipped copy:
1. `submit_primer_blast` uses `urllib.parse.urlencode` but `urllib.parse` is never imported → `NameError` on the Primer-BLAST path.
2. `write_report` references an undefined `chrom` in the off-target section → `NameError` when a BLAST RID is returned.
Plus any defect surfaced by D3. Keep algorithm behavior unchanged.
**Validation (cli/tdd):** `python -m py_compile`; offline self-checks of `tm_santalucia` (sanity range), `find_guide`, `find_pam`, and an exercised `write_report` off-target branch with a stubbed RID.

### D3 — e2e validation (GATE)
Run the packaged script live on GRNA03 and GRNA04 against OR2W5/human.
Confirm: locus resolves (NCBI fallback), gRNA located, PAM/cut found, primers
selected, hard verification gate passes, report + FASTA written. Inspect outputs
for correctness (primer count, Tm sanity, cut centering, FASTA length).
If an external service failure prevents completion → **pause and report** (per PM).
Loop back to D2 if a defect is found.
**Validation (post-hoc):** inspect the two generated reports + FASTAs; assert exit 0, all 4 primers present, verification "All primers verified."

### D4 — Push
Commit deliverables into `claude-skills` and push to `origin/main`.
**Validation (post-hoc):** `git push` succeeds; `git log`/`git status` clean.
**Gate:** confirm with PM before pushing (irreversible, outward-facing).

## Status
- D1 — Package as plugin: **complete** (commit 43a66a8)
- D2 — Harden the script: **complete** (commit 1f0a3dc)
- D3 — e2e validation: **complete** (PASS; both OR2W5 gRNAs, exit 0, all primers verified)
- D4 — Push: pending (awaiting PM confirmation)

## Order
D1 → D2 → D3 (loop to D2 on defect) → D4.
