# Tm Calculation Methods for Primer Design

There are three common ways to estimate DNA duplex melting temperature. They give different answers for the same primer — know which you're using.

## Quick comparison

| Method | Formula | Accuracy for ~20-bp primers | Used by |
|---|---|---|---|
| **Wallace** (1979) | `Tm = 2(A+T) + 4(G+C)` | Poor — only strictly valid for oligos <14 bp | Quick lab rule of thumb |
| **Marmur** (1962) | `Tm = 64.9 + 41·(GC/N) − 600/N` (at 50 mM Na+) | OK, but ignores sequence context | Older pipelines |
| **SantaLucia NN** (1998) | Sums base-stacking ΔH/ΔS for every dinucleotide + small salt correction | **Gold standard** | NEB TmCalculator, Primer3, IDT OligoAnalyzer, Primer-BLAST, Phusion recommended Ta |

## Why this skill uses SantaLucia NN

The script `design_primers.py` uses the SantaLucia 1998 nearest-neighbor method with the proper salt correction (small at typical Na+ concentrations, not the older `16.6·log10[Na+]` formula which drops Tms by ~20 °C at low salt). This matches what the NEB TmCalculator shows and what Phusion's recommended Ta is based on.

For reference, both Wallace and NN are reported in the output. Wallace is the "lab quick check" number; NN is the number to trust.

## Common Tm-calculation bugs to avoid

1. **Wrong salt correction formula**: applying `Tm + 16.6·log10[Na+]` to a SantaLucia NN Tm is a category error — that correction belongs to the Marmur formula. The SantaLucia 1998 paper has its own correction:  
   `ΔTm = (4.29·fGC − 3.95)·1e-5·ln[Na+] + 9.40e-6·(ln[Na+])²`  
   At 50 mM Na+ this is ~0 °C, not −21 °C.

2. **`x = 4` in the primer-concentration term**: for non-self-complementary PCR primers, `x = 1`. Setting `x = 4` artificially raises the apparent Tm by ~2 °C.

3. **Mixing `Tm(1M Na+)` and the salt correction**: if you compute `Tm(1M Na+)` and then add `16.6·log10[Na+]`, you're double-counting. The SantaLucia formula already has the salt correction baked in; the standalone `Tm(1M Na+)` is for the reference state.

4. **Ignoring terminal penalties**: SantaLucia 1998 subtracts ~2.8 cal/(mol·K) from dS for each terminal G/C. Skipping this shifts Tm by ~1 °C per terminal clamp.

5. **For Phusion: Mg²⁺/dNTP corrections are NOT in SantaLucia NN**: the IDT OligoAnalyzer "with PCR conditions" option applies additional corrections (dNTP sequesters Mg²⁺, lowering free [Mg²⁺] and thus Tm). For most Phusion reactions the difference is small (~1-2 °C), but if you want one number, use the NEB TmCalculator with the "PCR" product preset.

## Phusion-specific notes

- Phusion manual recommends **Ta = Tm − 3 to − 5 °C** as the starting point. With the Tm values the script reports, `Tm_NN − 3 °C` is a reasonable first try.
- If you see non-specific amplification, increase Ta in 2 °C steps. If yield is low, decrease Ta in 2 °C steps.
- Phusion's buffer contains 50 mM KCl (treated as monovalent cation for Tm purposes).

## References

- Wallace RB, et al. (1979) *Nucleic Acids Res* 6:3543-3557.  
- Marmur J, Schildkraut CL (1961) *Nature* 189:637-638.  
- SantaLucia J Jr (1998) *Proc Natl Acad Sci USA* 95:1460-1465.  
- NEB TmCalculator: https://tmcalculator.neb.com/  
- Owczarzy R, et al. (2004) *Biochemistry* 43:3537-3554 (salt correction refinements).
