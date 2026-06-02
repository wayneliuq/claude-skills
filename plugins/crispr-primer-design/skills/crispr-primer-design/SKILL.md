---
name: crispr-primer-design
description: |
  Design PCR and Sanger primers to validate CRISPR-Cas9 cutting at a given gRNA
  locus. Use this skill when the user has a gRNA (20-23 nt) sequence and wants
  to genotype the cut site — typically for ICE, TIDE, or amplicon-NGS
  cutting-efficiency analysis. Triggers on phrases like "design primers for my
  gRNA", "ICE primers for CRISPR", "PCR/Sanger primers to check CRISPR
  cutting", "TIDE primers for [gene]", "validate CRISPR cutting efficiency",
  "primers for CRISPR knockout validation". Do NOT use for general primer
  design without a CRISPR context, qPCR primers, cloning primers, gRNA design
  itself, or for non-cutting assays (ChIP, RNA-seq library prep, etc.).
---

# CRISPR Validation Primer Design

## Inputs to collect

- **gRNA sequence** — 20–23 nt DNA (convert U→T if RNA). The script auto-detects: 20-bp protospacer, or 23-bp protospacer+PAM (the trailing 3 bp are recorded as the user-annotated PAM but the genome's actual 3 bases 3' of the protospacer are still checked against the nuclease).
- **Target locus** — gene symbol (e.g. `TCL1A`, `OR2W5`) **or** explicit `chrN:start-end` (commas and missing `chr` prefix both accepted). If a gene symbol isn't in Ensembl (typical for pseudogenes), the script falls through to NCBI E-utilities to resolve the coordinates.
- **Species / assembly** — defaults to `human` / `GRCh38`. Mouse (`GRCm39`), rat (`mRatBN7.2`), and any Ensembl species are supported.
- **Application** — `ICE` (default), `TIDE`, or `amplicon-NGS`. Drives amplicon size and nested-primer distance.
- Optional: `--amplicon-size`, `--tm-min`, `--tm-max`, `--nuclease` (spcas9 or cas12a), `--skip-pam-check` (use for non-standard nucleases like xCas9/SaCas9, or when you have orthogonal evidence that cutting occurs despite a non-standard PAM), `--output-dir`.

If the user hasn't specified the application, **ask once before invoking** — picking the wrong one (e.g. designing 1 kb for TIDE which wants ~500 bp) wastes bench time.

## Procedure

The whole pipeline runs in **one pass** through `scripts/design_primers.py`. Do not iterate by hand — the script's job is to generate, score, and select in a single sweep so you don't end up chasing your own off-by-ones.

1. **Resolve the locus**:
   - If `--locus` is given: parse `chrN:start-end` (commas and missing `chr` prefix both tolerated), use as the search region.
   - If `--gene` is given: hit Ensembl `/lookup/symbol/`. On 4xx (typical for pseudogenes like `OR2W5P`), fall through to NCBI E-utilities `esearch` + `esummary`, take the GRCh38 entry, and continue.
2. **Locate the gRNA in the genome** by searching the ±2 kb region around the locus, both strands. If multiple perfect matches exist, use the leftmost and warn in the report.
3. **Identify PAM and cut site** (or bypass):
   - SpCas9: PAM = `NGG` immediately 3' of the protospacer on the same strand. Cut between bp 17 and 18 (3 bp 5' of the PAM).
   - Cas12a: PAM = `TTTV`. Cut similarly 18–23 bp from PAM (handled by the protospacer's 17/18 boundary; treat as a flag, the actual cut offset is a Cas12a-specific tuning the user should verify).
   - If `--skip-pam-check` is set, the genome's actual 3 bp 3' of the protospacer are reported as the PAM (informational only) and the design proceeds regardless of whether they match a known PAM pattern.
4. **Fetch the amplicon-window sequence**. At least `amplicon_size/2 + 200` bp each side of the cut.
5. **Generate the full candidate matrix in one shot**:
   - F primer candidates: distances 480–520 bp upstream of cut (5-bp steps), lengths 18–22 bp.
   - R primer candidates: same, downstream.
   - Compute Wallace Tm, SantaLucia NN Tm, GC%, length, 3'-clamp status, homopolymer runs — all in a single loop.
6. **Score and select** the best (F, R) pair with a joint score (both Tm in target window, matched Tms, centered cut, no homopolymers, G/C clamp).
7. **Select nested Sanger primers** (80–150 bp from cut for ICE; 60–120 bp for TIDE).
8. **Hard verification gate**: every primer must match the + strand at its claimed binding site. If any fails, abort with the exact mismatch.
9. **Off-target check (PCR only)**: submit the PCR primer pair to NCBI Primer-BLAST, restricted to the amplicon region, return the RID for the user to poll. Nested Sanger primers are guaranteed inside the amplicon so they can't introduce new off-targets.
10. **Output** the markdown report + wild-type amplicon FASTA.

## Output contract

A markdown report at `<output-dir>/crispr_primers_<gene>_<grna-short>.md` with:
- Header: gRNA, PAM (genome-actual + user-annotated if 23-bp input), cut site, nuclease, application, amplicon size
- Primer table: 4 rows (PCR-F, PCR-R, Sanger-F, Sanger-R) with length, Tm (Wallace and NN), position, G/C clamp
- Phusion recommended Ta with the formula shown explicitly and a caution if NN Tm is above Phusion's practical ceiling
- Optional section: "Multiple gRNA matches found" with the up-to-5 other hits
- Optional section: "Off-target check" with the Primer-BLAST RID + poll URL
- Wild-type amplicon FASTA block (cut site marked)
- Notes explaining the Tm-target convention (Wallace), the Phusion Ta clamping, and any skipped-PAM caveat

Plus a separate `<output-dir>/<gene>_<grna-short>_amplicon_WT.fa` for direct upload into ICE.

## Failure handling

- **gRNA not found in genome** — try both strands, the reverse-complement, then report clearly. Common cause: wrong species/assembly, or the gRNA was pasted with U's (RNA) instead of T's.
- **Gene symbol not in Ensembl** — fall through to NCBI E-utilities. If NCBI also returns nothing, error out with a clear "this symbol may be wrong or the locus may be on a different assembly" message.
- **PAM not found** — by default, error out. The error message now suggests `--skip-pam-check` and `--nuclease` so the user has an obvious next move.
- **Multiple perfect gRNA matches** — use the leftmost, list the rest in the report's "Multiple gRNA matches" section.
- **No candidate primer pair meets the Tm filter** — error out with a suggestion to widen `--tm-min/--tm-max` or adjust `--amplicon-size`. (Was previously auto-widened silently — that was confusing, now we surface it.)
- **Primer-BLAST submission fails** — print a warning and tell the user to do the off-target check manually. The script doesn't depend on Primer-BLAST to function.

## Examples

**Input:** "Design ICE primers for gRNA `GGGTAGAGCTGCCACATGAT` targeting `TCL1A` in human, Phusion polymerase."

**Output:** a markdown report with the 4-primer set (PCR + nested Sanger), Tm in both Wallace and NN, the Phusion recommended Ta, and a wild-type amplicon FASTA ready for ICE.

**Input:** "I have a gRNA with PAM — `TCGGCCTGGACTGGAGAAAACGG` — for `OR2W5`. Skip the PAM check, the library annotation is wrong."

**Output:** script auto-detects the 23-bp input, splits it into 20-bp protospacer + 3-bp user-annotated `CGG`, runs Ensembl → falls through to NCBI because OR2W5P isn't in Ensembl → locates the protospacer in chr1:247,488,092-247,492,408 → reports the genome's actual 3' bases as the PAM (which won't match the user's `CGG`) → with `--skip-pam-check` it proceeds and produces primers anyway, with a clear note in the report that the PAM check was skipped.
