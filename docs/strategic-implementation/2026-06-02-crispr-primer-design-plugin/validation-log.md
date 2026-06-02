# Validation log
_Feature: crispr-primer-design-plugin · Started: 2026-06-02 · Autonomy: auto_

## DEV-001
**Type:** branch-risk
**Deliverable:** (pre-flight)
**Plan said:** execute in claude-skills repo
**Actually:** repo is on `main`; PM confirmed staying on main (matches repo's existing maintenance pattern — strategic-implementation plugin committed directly to main).
**Resolution:** proceed on main; confirm before push.
**Downstream impact?** no
**Agent category:** alignment

## DEV-002
**Type:** retry
**Deliverable:** D3
**Plan said:** post-hoc inspect the two generated reports + FASTAs
**Actually:** first inspection script globbed `/tmp/crispr_e2e` (Git-bash mount) but native Python resolved it to `C:\tmp`, matching zero files → vacuous PASS. Re-ran against `%LOCALAPPDATA%\Temp\crispr_e2e` (the path the script actually wrote to); real assertions then passed.
**Resolution:** validation re-run on the correct path; both reports have 4 primers + FASTA + PAM + Phusion Ta, both amplicons 1006 bp with declared==actual length and ACGT-only bases. Biology spot-checked (PAM, cut position, primer coords).
**Downstream impact?** no
**Agent category:** tests

## NOTE — Primer-BLAST off-target submission (D3, not a defect)
On both live runs the NCBI Primer-BLAST submission returned no parseable RID and the
script printed its documented graceful-degrade message ("do the off-target check
manually"). This is expected: Primer-BLAST returns an interactive/async page that is
fragile to scrape. The off-target check is optional and the pipeline does not depend
on it. The `urllib.parse` fix (D2) is exercised on this path — the request is now sent
without a NameError; NCBI simply doesn't hand back a synchronous RID. Left as-is;
hardening the NCBI async flow is out of scope and higher-risk than the graceful degrade.

## D3 RESULT — PASS
Both OR2W5 gRNAs (GRNA03 `AACCAGGAGGACGCACTCGG`, GRNA04 `ACCGGCAGACGGCCACATAG`) ran
end-to-end, exit 0, all primers verified against the genome. Ensembl→NCBI pseudogene
fallback worked. Cut sites centered (bp 506 / bp 496 of 1006 bp).
