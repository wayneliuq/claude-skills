# crispr-primer-design

Design PCR and nested Sanger primers to validate CRISPR-Cas9 cutting at a gRNA locus.

This plugin packages a single skill, `crispr-primer-design`, plus its one-shot
primer-design pipeline. Given a gRNA and a target gene/locus, it resolves the
locus, finds the cut site, generates and scores all primer candidates in one
sweep, hard-verifies every primer against the genome, and emits a markdown
report + a wild-type amplicon FASTA ready for ICE/TIDE/amplicon-NGS analysis.

## Install

```bash
claude plugin marketplace add https://github.com/wayneliuq/claude-skills.git
claude plugin install crispr-primer-design@wayneliuq
```

## Use

Invoke the skill with `/crispr-primer-design:crispr-primer-design`, or just ask
in natural language — e.g. "design ICE primers for my gRNA `GGGTAGAGCTGCCACATGAT`
targeting TCL1A".

The pipeline can also be run directly:

```powershell
python "<plugin-dir>\skills\crispr-primer-design\scripts\design_primers.py" `
  --grna AACCAGGAGGACGCACTCGG --gene OR2W5 --application ICE `
  --output-dir C:\path\to\workspace
```

## Requirements

- Python 3 (standard library only — no third-party packages).
- Network access: the script makes live calls to Ensembl REST, NCBI E-utilities
  (pseudogene fallback), and optionally NCBI Primer-BLAST (off-target check).

## What's inside

| File | Purpose |
|---|---|
| `skills/crispr-primer-design/SKILL.md` | When/how Claude should use the skill |
| `skills/crispr-primer-design/scripts/design_primers.py` | The one-shot design pipeline |
| `skills/crispr-primer-design/references/tm_methods.md` | Wallace vs SantaLucia NN Tm, common bugs |

See the skill's `SKILL.md` for the full input/output contract and failure handling.
