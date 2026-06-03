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

- **gRNA sequence(s)** — 20–23 nt DNA (convert U→T if RNA). The script auto-detects: 20-bp protospacer, or 23-bp protospacer+PAM (the trailing 3 bp are recorded as the user-annotated PAM but the genome's actual 3 bases 3' of the protospacer are still checked against the nuclease). `--grna` accepts **multiple** sequences — see "Multiple gRNAs on one gene" below.
- **Target locus** — gene symbol (e.g. `TCL1A`, `OR2W5`) **or** explicit `chrN:start-end` (commas and missing `chr` prefix both accepted). If a gene symbol isn't in Ensembl (typical for pseudogenes), the script falls through to NCBI E-utilities to resolve the coordinates.
- **Species / assembly** — defaults to `human` / `GRCh38`. Mouse (`GRCm39`), rat (`mRatBN7.2`), and any Ensembl species are supported.
- **Application** — `ICE` (default), `TIDE`, or `amplicon-NGS`. Drives nested-Sanger-primer distance and the single-read coverage threshold. (It no longer drives amplicon size — every design defaults to a uniform 2 kb, see below.)
- Optional: `--amplicon-size`, `--tm-min`, `--tm-max`, `--nuclease` (spcas9 or cas12a), `--skip-pam-check` (use for non-standard nucleases like xCas9/SaCas9, or when you have orthogonal evidence that cutting occurs despite a non-standard PAM), `--max-amplicon` (cap for repeat-avoidance expansion; default 1.5× target), `--no-repeat-check` (skip repeat screening — offline or poorly-annotated species), `--output-dir`.

If the user hasn't specified the application, **ask once before invoking** — it sets the nested-Sanger-primer distance (ICE 80–150 bp, TIDE 60–120 bp from the cut) and the single-read coverage threshold, which affect how the trace is genotyped.

**Amplicon size defaults to a uniform 2 kb for every design** (single, separate, or combined), so all loci amplify under one PCR condition and pool easily. The cut is genotyped from nested Sanger primers, so a large amplicon doesn't hurt ICE/TIDE resolution. Override per run with `--amplicon-size`.

## Multiple gRNAs on one gene

`--grna` takes one or more sequences that target the **same** gene/locus (one invocation per gene). **Group the user's gRNAs by gene and call the script once per gene with all of that gene's gRNAs.** The script decides automatically:

- **Cut sites within 1000 bp** → **one combined PCR amplicon** spanning all cuts (uniform 2 kb default, override with `--amplicon-size`). F primer sits upstream of the leftmost cut, R downstream of the rightmost.
- **Cut sites > 1000 bp apart** → can't combine; the script designs each gRNA independently (one report each), exactly as the single-gRNA path.
- **Sanger primers (combined case)** → always an **F + R pair**: Sanger-F decomposes the leftmost cut, Sanger-R the rightmost. This is mandatory because a Sanger trace is a mixture of alleles immediately 3' of any cut it reads through, so **one read can only cleanly decompose the first cut it reaches** — two co-delivered (dual-cut) edits need both reads regardless of distance. A *single* forward read suffices only when each gRNA is in a **separate single-cut sample** and the cut spread is within the clean decomposition window: **≤ 500 bp for ICE, ≤ 200 bp for TIDE** (TIDE's window is tighter). The report spells out both scenarios.

Different genes are independent — make a separate call per gene. (For the 4-gRNA example with OR2W5 ×2 and TCL1A ×2: one combined OR2W5 call, one TCL1A call that auto-splits because its cuts are ~1.7 kb apart.)

## Repeat screening (avoid Alu/LINE/low-complexity)

PCR primers that land in a **known repetitive element** (Alu, LINE, microsatellite, …) prime all over the genome. The script screens against Ensembl's RepeatMasker annotation (`/overlap/region?feature=repeat`) and avoids them automatically:

- A primer's **3′ anchor (last 15 bp)** — the part that drives priming specificity — must be repeat-free. Candidates whose 3′ anchor sits in a repeat are rejected; a clean 3′ anchor is the **top selection priority**, above the Tm/clamp rules.
- If the default-size window is all-repeat, the search **expands the amplicon up to `--max-amplicon` (default 1.5× target)** to reach repeat-free sequence, always preferring the smallest clean amplicon. The report notes any enlargement.
- If no clean primer exists even at the cap, the best available is kept and **flagged** with the repeat name + a suggestion (raise `--max-amplicon`, move the other primer, or rely on Primer-BLAST).
- Sanger primers are screened too but **flag-only** (they sit inside the amplicon).
- `--no-repeat-check` skips this (offline / poorly-annotated species); if the Ensembl call fails the pipeline proceeds unscreened with a note. Repeat screening **complements** Primer-BLAST — it avoids annotated repeats up front; Primer-BLAST still does the genome-wide specificity check.

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
4. **Fetch the amplicon-window sequence**. Centered on the cut (single) or the cut-cluster midpoint (combined), sized by `--max-amplicon` so a primer can move out to clear a repeat. Then **fetch repeat annotation** for the same window (unless `--no-repeat-check`).
5. **Generate the full candidate matrix in one shot**:
   - F primer candidates: a window of distances upstream of the (leftmost) cut, 5-bp steps, lengths 18–22 bp. When repeat-screening, the distance range is widened so a primer can reach repeat-free sequence within the cap.
   - R primer candidates: same, downstream of the (rightmost) cut.
   - Compute Wallace Tm, SantaLucia NN Tm, GC%, length, 3'-clamp status, homopolymer runs, and 3'-anchor repeat overlap — all in a single loop.
6. **Score and select** the best (F, R) pair, lexicographically: (1) **both 3′ anchors repeat-free**; (2) **smallest |amplicon − target|** (prefer the least enlargement); (3) primer quality — Wallace Tm within **60 ± 2 °C** with a **3' G/C clamp**, then 60 ± 2 °C without a clamp, then the broad `--tm-min/--tm-max` window (default 57–63), closest-to-60 within each tier. Homopolymer runs and GC% outside 30–70 are hard rejects. (When `--no-repeat-check` is set, criterion 1 is inert and selection is size → Tm/clamp.)
7. **Select Sanger primers**. Single cut: nested F + R flanking the cut (80–150 bp for ICE, 60–120 bp for TIDE). Combined: F at the leftmost cut, R at the rightmost (see "Multiple gRNAs on one gene").
8. **Hard verification gate**: every primer must match the + strand at its claimed binding site. If any fails, abort with the exact mismatch.
9. **Off-target check (PCR only)**: submit the PCR primer pair to NCBI Primer-BLAST against the organism genome database, returning a **job key + results URL** for the user to poll. Sanger primers are guaranteed inside the amplicon so they can't introduce new off-targets.
10. **Output** the markdown report + wild-type amplicon FASTA (all cut sites marked).

## Output contract

A markdown report at `<output-dir>/crispr_primers_<gene>_<grna-short>.md` (combined: `<gene>_<g1-short>_<g2-short>…`) with:
- Header: each gRNA + PAM (genome-actual + user-annotated if 23-bp input) + cut site; for combined, a cut-site span line; nuclease, application, amplicon size
- Primer table: PCR-F, PCR-R, Sanger-F, Sanger-R with length, Tm (Wallace and NN), position, G/C clamp
- Phusion recommended Ta with the formula shown explicitly and a caution if NN Tm is above Phusion's practical ceiling
- Combined only: a "Sanger sequencing coverage" section explaining the dual-cut (need both reads) vs separate-sample (one read may suffice, per ICE/TIDE threshold) cases
- Optional section: "Multiple gRNA matches found" with the up-to-5 other hits (per gRNA)
- "Repeat screening" section: per-primer status (clear / 3′-clean-5′-overlap / ⚠ 3′ overlaps `<repeat>`), a note if the amplicon was enlarged to avoid a repeat, or "Skipped"/"Unavailable" when screening didn't run
- Optional section: "Off-target check" with the Primer-BLAST **job key + results URL**
- Wild-type amplicon FASTA block (all cut sites marked, in amplicon bp)
- Notes explaining the Tm-selection rule (Wallace, 60 ± 2 with clamp preference), the Phusion Ta clamping, and any skipped-PAM caveat

Plus a separate `<output-dir>/<gene>_<grna-short>_amplicon_WT.fa` for direct upload into ICE.

## Failure handling

- **gRNA not found in genome** — try both strands, the reverse-complement, then report clearly. Common cause: wrong species/assembly, or the gRNA was pasted with U's (RNA) instead of T's.
- **Gene symbol not in Ensembl** — fall through to NCBI E-utilities. If NCBI also returns nothing, error out with a clear "this symbol may be wrong or the locus may be on a different assembly" message.
- **PAM not found** — by default, error out. The error message now suggests `--skip-pam-check` and `--nuclease` so the user has an obvious next move.
- **Multiple perfect gRNA matches** — use the leftmost, list the rest in the report's "Multiple gRNA matches" section.
- **No candidate primer pair meets the Tm filter** — error out with a suggestion to widen `--tm-min/--tm-max` or adjust `--amplicon-size`. (Was previously auto-widened silently — that was confusing, now we surface it.)
- **Primer-BLAST submission fails** — print a warning and tell the user to do the off-target check manually. The script doesn't depend on Primer-BLAST to function. (The script uses the live form fields `PRIMER_LEFT_INPUT`/`PRIMER_RIGHT_INPUT` + `SEARCH_SPECIFIC_PRIMER` and parses the returned `job_key`+`ctg_time`; server-side validation errors are surfaced verbatim.)
- **Multiple gRNAs given but > 1000 bp apart** — not an error; the script reports the span and designs each independently.
- **Primer stuck in a repeat** — if no repeat-free 3′ anchor exists within `--max-amplicon`, the primer is kept and flagged in "Repeat screening" with the repeat name + suggestion (raise `--max-amplicon`, move the other primer, or rely on Primer-BLAST).
- **Repeat annotation unavailable** — Ensembl call fails or species lacks RepeatMasker data → print a warning, proceed unscreened, and note it in the report. Never fatal. `--no-repeat-check` opts out deliberately.

## Examples

**Input:** "Design ICE primers for gRNA `GGGTAGAGCTGCCACATGAT` targeting `TCL1A` in human, Phusion polymerase."

**Output:** a markdown report with the 4-primer set (PCR + nested Sanger), Tm in both Wallace and NN, the Phusion recommended Ta, and a wild-type amplicon FASTA ready for ICE.

**Input:** "I have a gRNA with PAM — `TCGGCCTGGACTGGAGAAAACGG` — for `OR2W5`. Skip the PAM check, the library annotation is wrong."

**Output:** script auto-detects the 23-bp input, splits it into 20-bp protospacer + 3-bp user-annotated `CGG`, runs Ensembl → falls through to NCBI because OR2W5P isn't in Ensembl → locates the protospacer in chr1:247,488,092-247,492,408 → reports the genome's actual 3' bases as the PAM (which won't match the user's `CGG`) → with `--skip-pam-check` it proceeds and produces primers anyway, with a clear note in the report that the PAM check was skipped.

**Input:** "Design TIDE primers for two OR2W5 gRNAs: `AACCAGGAGGACGCACTCGG` and `ACCGGCAGACGGCCACATAG`."

**Command:** `--grna AACCAGGAGGACGCACTCGG ACCGGCAGACGGCCACATAG --gene OR2W5 --application TIDE`

**Output:** the two cuts are 37 bp apart, so one combined **2 kb** amplicon is designed with a single PCR pair and one Sanger F+R pair. The report notes that because the spread (37 bp) is ≤ 200 bp (TIDE), a single forward read covers both cuts *if each gRNA is run in a separate single-cut sample* — but if both are co-delivered, Sanger-F reads the left cut and Sanger-R the right. (Had the two cuts been > 1 kb apart, as with the two example TCL1A gRNAs, the script would instead emit two independent designs.)

**Input:** "Design TIDE primers for TCL1A gRNA `GGGTAGAGCTGCCACATGAT`."

**Output:** the default-size forward window sits inside an **AluY** (chr14:95,711,178–95,711,481). Repeat screening rejects the Alu-overlapping forward candidates and steps the forward primer upstream into unique sequence; the amplicon enlarges to ~2.15 kb (within the 1.5× cap) and the report's "Repeat screening" section shows all primers `clear` with a note that the amplicon was sized up to avoid the repeat. (Before this feature the tool returned the Alu primer `TTAGCCAGGTGTGGTGGC`, which mispriced genome-wide.)
