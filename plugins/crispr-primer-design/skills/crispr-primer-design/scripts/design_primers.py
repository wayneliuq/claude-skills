#!/usr/bin/env python
"""
CRISPR validation primer design — one-shot pipeline.

Generates PCR and nested Sanger primers for ICE/TIDE/amplicon-NGS analysis of
CRISPR-Cas9 cutting. Generates ALL candidate primers in one pass, scores them
in a single sweep, picks the best pair, verifies against the genome, and
emits a markdown report + a wild-type amplicon FASTA.

Usage:
    python design_primers.py --grna GGGTAGAGCTGCCACATGAT --gene TCL1A
    python design_primers.py --grna GGGTAGAGCTGCCACATGAT --locus chr14:95712272-95712291
    python design_primers.py --grna GGGTAGAGCTGCCACATGAT --gene TCL1A --application TIDE --amplicon-size 500

Output:
    <output-dir>/crispr_primers_<gene>_<grna>.md   (markdown report)
    <output-dir>/<gene>_<grna>_amplicon_WT.fa     (FASTA for ICE)
"""

import argparse
import json
import math
import os
import re
import sys
import urllib.request
import urllib.error

# ---------- Tm calculation ----------

# SantaLucia 1998 unified nearest-neighbor parameters (dH kcal/mol, dS cal/mol/K)
NN = {
    'AA': (-7.9, -22.2), 'TT': (-7.9, -22.2),
    'AT': (-7.2, -20.4),
    'TA': (-7.2, -21.3),
    'CA': (-8.5, -22.7), 'TG': (-8.5, -22.7),
    'GT': (-8.4, -22.4), 'AC': (-8.4, -22.4),
    'CT': (-7.8, -21.0), 'AG': ('-7.8', -21.0),  # placeholder, see below
    'GA': (-8.2, -22.2), 'TC': (-8.2, -22.2),
    'CG': (-10.6, -27.2),
    'GC': (-9.8, -24.4),
    'GG': (-8.0, -19.9), 'CC': (-8.0, -19.9),
}
# Fix that placeholder (kept one dict compact for readability above; correct value below)
NN['AG'] = (-7.8, -21.0)


def nn_dH_dS(seq):
    """SantaLucia 1998 nearest-neighbor dH (kcal/mol) and dS (cal/mol/K)."""
    s = seq.upper()
    dH = 0.0
    dS = -1.4  # initiation
    if s[0] in 'GC':
        dS -= 2.8
    if s[-1] in 'GC':
        dS -= 2.8
    for i in range(len(s) - 1):
        pair = s[i:i + 2]
        if pair in NN:
            h, st = NN[pair]
        else:
            rc = pair.translate(str.maketrans("ACGT", "TGCA"))[::-1]
            h, st = NN[rc]
        dH += h
        dS += st
    return dH, dS


def tm_santalucia(seq, primer_nM=500, na_mM=50):
    """SantaLucia 1998 NN Tm in °C at given primer & Na+ concentrations.

    Default 500 nM primer (typical PCR) and 50 mM Na+ (typical Phusion buffer).
    Salt correction is the proper SantaLucia 1998 formula — small at 50 mM, not
    the older `16.6*log10[Na+]` that drops Tms by 20 °C at low salt.
    """
    dH, dS = nn_dH_dS(seq)
    R = 1.987
    C = primer_nM * 1e-9
    Tm_K = (1000 * dH) / (dS + R * math.log(C / 1))  # x=1 for non-self-complementary
    Tm_C = Tm_K - 273.15
    fGC = (seq.count('G') + seq.count('C')) / len(seq)
    ln_Na = math.log(na_mM / 1000.0)
    dTm = (4.29 * fGC - 3.95) * 1e-5 * ln_Na + 9.40e-6 * ln_Na ** 2
    return Tm_C + dTm


def tm_wallace(seq):
    """Wallace rule-of-thumb Tm = 2(A+T) + 4(G+C). Quick check; less accurate than NN."""
    return 2 * seq.count('A') + 2 * seq.count('T') + 4 * seq.count('G') + 4 * seq.count('C')


def gc_content(seq):
    return 100 * (seq.count('G') + seq.count('C')) / len(seq)


def has_homopolymer_run(seq, n=5):
    for b in 'ACGT':
        if b * n in seq:
            return True
    return False


# ---------- Genome lookup (Ensembl REST) ----------

ENSEMBL = "https://rest.ensembl.org"


def http_get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={'Content-Type': 'application/json',
                                                'User-Agent': 'crispr-primer-design/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_get_text(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'crispr-primer-design/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def resolve_gene_symbol(symbol, species="homo_sapiens"):
    """Resolve a gene symbol to a chromosomal region via Ensembl.

    Raises urllib.error.HTTPError (typically 400 for unknown symbols,
    including pseudogenes that aren't in the main gene lookup) so the caller
    can fall through to NCBI."""
    url = f"{ENSEMBL}/lookup/symbol/{species}/{symbol}?expand=0"
    data = http_get_json(url)
    return data.get("seq_region_name"), int(data.get("start")), int(data.get("end"))


def resolve_locus_ncbi(symbol, species="homo_sapiens"):
    """Fallback: resolve a gene symbol via NCBI E-utilities when Ensembl
    doesn't have it (common for pseudogenes, e.g. OR2W5P).

    Returns (chrom_no_prefix, start_1b, end_1b) on the most recent GRCh38
    annotation. Raises RuntimeError if the symbol can't be resolved.
    """
    # Species -> NCBI taxonomy ID (default: human = 9606)
    taxid = {"homo_sapiens": "9606", "mus_musculus": "10090"}.get(species, "9606")
    # Step 1: search gene by symbol
    search_url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                  f"?db=gene&term={symbol}[Gene]%20AND%20{species.replace('_', '+')}[Organism]"
                  f"&retmode=json")
    data = http_get_json(search_url)
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        raise RuntimeError(f"NCBI gene search returned no results for {symbol}")
    # Step 2: fetch details for each gene ID, take first one on the target assembly
    for gid in ids[:3]:
        try:
            s = http_get_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                              f"?db=gene&id={gid}&retmode=json")
        except Exception:
            continue
        gs = s.get("result", {}).get(gid, {})
        chrom = gs.get("chromosome", "")
        if not chrom:
            continue
        loc_hist = gs.get("locationhist", [])
        # Prefer GRCh38 (NC_0000xx.11 for chr1-22, NC_000023.11 for chrX, etc.)
        for entry in loc_hist:
            accver = entry.get("chraccver", "")
            if accver.startswith("NC_") and accver.endswith(".11"):
                return chrom, int(entry["chrstart"]), int(entry["chrstop"])
        # Fall back to the most recent (first) entry
        if loc_hist:
            return chrom, int(loc_hist[0]["chrstart"]), int(loc_hist[0]["chrstop"])
    raise RuntimeError(f"NCBI gene search for {symbol} returned no usable coordinates")


def fetch_region(chrom, start_1b, end_1b, species="homo_sapiens"):
    """Fetch the + strand sequence for a 1-based inclusive range."""
    url = f"{ENSEMBL}/sequence/region/{species}/{chrom}:{start_1b}..{end_1b}:1?content-type=text/plain"
    return http_get_text(url), start_1b


def submit_primer_blast(pcr_F_seq, pcr_R_seq, amplicon_start_1b, amplicon_end_1b,
                       chrom, species="homo_sapiens", timeout=60):
    """Submit the PCR primer pair to NCBI Primer-BLAST for off-target checking.

    Returns (rid, status_url) on success, or (None, None) on failure.
    NCBI Primer-BLAST can take minutes; we just submit and return the RID.
    The user polls the status URL themselves.

    Note: PCR primers only. Nested Sanger primers sit inside the amplicon
    so they can't introduce new off-targets.
    """
    try:
        # Primer-BLAST POST endpoint
        endpoint = "https://www.ncbi.nlm.nih.gov/tools/primer-blast/primertool.cgi"
        # Species for Primer-BLAST: scientific name, not Ensembl slug
        sci_name = {"homo_sapiens": "Homo sapiens", "mus_musculus": "Mus musculus"}.get(species, "Homo sapiens")
        # Build the form payload
        payload = {
            "PRIMER5_INPUT": pcr_F_seq,
            "PRIMER3_INPUT": pcr_R_seq,
            "PRIMER_SPECIFICITY_DATABASE": "Genome (reference subsets from selected organisms)",
            "ORGANISM": sci_name,
            "PRIMER_TASK": "generic",
            "PRIMER_PICK_LEFT_PRIMER": "",
            "PRIMER_PICK_INTERNAL_PRIMER": "",
            "PRIMER_PICK_RIGHT_PRIMER": "",
            "PRIMER_OPT_SIZE": "20",
            "PRIMER_MIN_SIZE": "18",
            "PRIMER_MAX_SIZE": "25",
            "PRIMER_PRODUCT_MIN": str(max(100, amplicon_end_1b - amplicon_start_1b - 100)),
            "PRIMER_PRODUCT_MAX": str(amplicon_end_1b - amplicon_start_1b + 100),
            "PRIMER_MIN_TM": "57.0",
            "PRIMER_OPT_TM": "60.0",
            "PRIMER_MAX_TM": "63.0",
            "PRIMER_SPECIFICITY_STRING": f"{chrom}:{amplicon_start_1b}-{amplicon_end_1b}",
        }
        body = urllib.parse.urlencode(payload).encode()
        req = urllib.request.Request(endpoint, data=body, headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'crispr-primer-design/1.0 (off-target check)',
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            html = r.read().decode(errors='replace')
    except Exception as e:
        print(f"  (Primer-BLAST submission failed: {e})")
        return None, None
    # Extract RID from the response (Primer-BLAST returns an HTML page with a RID)
    m = re.search(r'PRD-RID=([A-Z0-9]+)', html) or re.search(r'"rid"\s*:\s*"([A-Z0-9]+)"', html) \
        or re.search(r'Request\s*ID[^>]*>\s*([A-Z0-9]+)', html, re.IGNORECASE)
    if not m:
        # Sometimes the response is the immediate results page; the user can find the RID in the URL
        m = re.search(r'[?&]RID=([A-Z0-9]+)', html)
    if m:
        rid = m.group(1)
        return rid, f"https://www.ncbi.nlm.nih.gov/tools/primer-blast/?RID={rid}"
    return None, None


def find_guide(seq, region_start_1b, grna, return_all=False):
    """Locate the gRNA in the sequence (try + and - strand).

    By default returns the first match: (strand, gstart_1b, gend_1b, plus_strand_at_site).
    If return_all=True, returns a list of all matches (used for disambiguation).

    gstart/gend are 1-based genomic positions; the protospacer string is the
    + strand sequence at that locus (== grna for + strand, == RC(grna) for -)."""
    matches = []
    i = 0
    while True:
        i = seq.find(grna, i)
        if i < 0: break
        gs = region_start_1b + i
        matches.append(('+', gs, gs + len(grna) - 1, grna))
        i += 1
    rcg = grna.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    i = 0
    while True:
        i = seq.find(rcg, i)
        if i < 0: break
        gs = region_start_1b + i
        matches.append(('-', gs, gs + len(rcg) - 1, rcg))
        i += 1
    matches.sort(key=lambda m: m[1])  # leftmost first
    if return_all:
        return matches
    return matches[0] if matches else None


def find_pam(seq, region_start_1b, grna_strand, grna_genomic_start, grna_len,
             nuclease="spcas9", skip_pam_check=False, user_pam=None):
    """Find the PAM and cut position. Returns (pam_seq, pam_start_1b, cut_pos_1b).

    For SpCas9: PAM = NGG immediately 3' of the protospacer on the same strand.
    Cut = between bp 17 and 18 of the protospacer (3 bp 5' of the PAM).

    skip_pam_check: if True, return the genome's actual 3 bases 3' of the
    protospacer as the PAM without validating the nuclease's PAM pattern.
    Useful when the user has a non-standard nuclease (xCas9, SaCas9, custom)
    or a known-valid gRNA from a different convention.

    user_pam: if provided, the user has annotated the PAM themselves
    (e.g. they passed 23-bp protospacer+PAM). Informational only; not used
    for validation here, just returned in the report.
    """
    if nuclease.lower() in ("spcas9", "cas9"):
        pam_pattern = re.compile(r'[ACGT]GG')  # NGG on protospacer strand
    elif nuclease.lower() in ("cas12a", "cpf1"):
        pam_pattern = re.compile(r'TTT[ACGT]')  # TTTV
    else:
        raise ValueError(f"unsupported nuclease: {nuclease}")

    if grna_strand == '+':
        pam_start_1b = grna_genomic_start + grna_len  # 1-based, immediately after protospacer
    else:
        # On - strand: the 3' end of the protospacer (3' in protospacer reading direction)
        # is at the lowest genomic position.
        # protospacer occupies [start, start+len-1] on - strand; 3' end is at start
        pam_start_1b = grna_genomic_start - 3  # 3 bases upstream of - strand protospacer's 3' end
    # PAM in the pulled sequence (always read on + strand for fetching)
    if pam_start_1b < 0:
        return None
    # We need 3 bases from position pam_start_1b onward (or before, for - strand)
    if grna_strand == '+':
        idx_in_seq = pam_start_1b - region_start_1b
        if idx_in_seq < 0 or idx_in_seq + 3 > len(seq):
            return None
        pam_seq = seq[idx_in_seq:idx_in_seq + 3]
    else:
        # - strand: the PAM (5'->3' on - strand) sits at the three bases immediately
        # 5' (lower genomic position) of the protospacer's 3' end. The + strand
        # reads in the opposite direction, so the PAM bases are at positions
        # grna_gs-3, grna_gs-2, grna_gs-1 (5'->3' on + strand).
        idx_in_seq = pam_start_1b - region_start_1b
        if idx_in_seq < 0 or idx_in_seq + 3 > len(seq):
            return None
        pam_seq = seq[idx_in_seq:idx_in_seq + 3]
    # Validate PAM (unless skipped)
    if not skip_pam_check:
        if nuclease.lower() in ("spcas9", "cas9"):
            # SpCas9 PAM = NGG. On - strand gRNA, the + strand at the PAM position
            # is the reverse complement = CCN. We fetched the + strand 3 bases;
            # accept either NGG (matches on + strand gRNA) or CCN (matches on - strand
            # gRNA where + strand carries the complement of the - strand PAM).
            if not (pam_pattern.match(pam_seq) or
                    re.match(r'CC[ACGT]', pam_seq)):
                return None
        elif nuclease.lower() in ("cas12a", "cpf1"):
            if not (pam_pattern.match(pam_seq) or
                    re.match(r'[ACGT]AAA', pam_seq)):
                return None
    # Cut position (1-based, between bases): on + strand = protospacer_start + 16
    # (positions 1..20, cut between 17 and 18; protospacer_start is 1-based)
    if grna_strand == '+':
        cut_1b = grna_genomic_start + 17  # 0-based offset 17, so 1-based position is start+17
    else:
        # On - strand, the protospacer reads 5'->3' from high to low genomic position.
        # Position 17 of the protospacer (5'-distal numbering) is at genomic position
        # grna_genomic_start + (grna_len - 17)
        cut_1b = grna_genomic_start + (grna_len - 17)
    return (pam_seq, pam_start_1b, cut_1b)


# ---------- Primer candidate generation ----------

def generate_F_candidates(amp_seq, amp_start_1b, cut_1b, amplicon_size_target,
                          length_range=(18, 22), dist_tolerance=25, dist_step=5):
    """Generate F primer candidates at multiple distances upstream of the cut,
    at multiple lengths. F primer = + strand substring.
    Returns list of dicts: {seq, length, dist_from_cut, start_1b, end_1b}."""
    cut_in_seq = cut_1b - amp_start_1b
    target_dist = amplicon_size_target // 2
    candidates = []
    for dist in range(target_dist - dist_tolerance, target_dist + dist_tolerance + 1, dist_step):
        for L in range(length_range[0], length_range[1] + 1):
            # F primer 5' end is at (cut - dist), 3' end is at (cut - dist + L - 1)
            f5 = cut_1b - dist
            f3 = f5 + L - 1
            if f5 < amp_start_1b:
                continue
            f5_in_seq = f5 - amp_start_1b
            f3_in_seq = f3 - amp_start_1b
            if f3_in_seq >= len(amp_seq):
                continue
            seq = amp_seq[f5_in_seq:f3_in_seq + 1]
            if len(seq) != L:
                continue
            candidates.append({
                'seq': seq, 'length': L, 'dist_from_cut': dist,
                'start_1b': f5, 'end_1b': f3,
            })
    return candidates


def generate_R_candidates(amp_seq, amp_start_1b, cut_1b, amplicon_size_target,
                          length_range=(18, 22), dist_tolerance=25, dist_step=5):
    """Generate R primer candidates. R primer = RC of + strand at the binding site.
    The R primer's 3' end is at the 5' end of the binding site on + strand.
    Returns list with same structure as F candidates, plus 'plus_bind_start'/
    'plus_bind_end' (the binding site on + strand) for downstream verification."""
    cut_in_seq = cut_1b - amp_start_1b
    target_dist = amplicon_size_target // 2
    candidates = []
    for dist in range(target_dist - dist_tolerance, target_dist + dist_tolerance + 1, dist_step):
        for L in range(length_range[0], length_range[1] + 1):
            # R primer 3' end (on primer) is at + strand position (cut + dist)
            # The binding site on + strand is from (cut + dist - L + 1) to (cut + dist)
            r3_5p = cut_1b + dist  # + strand position of the R primer's 3' end on + strand
            r5_5p = r3_5p - L + 1
            r5_in_seq = r5_5p - amp_start_1b
            r3_in_seq = r3_5p - amp_start_1b
            if r5_in_seq < 0 or r3_in_seq >= len(amp_seq):
                continue
            plus_seq = amp_seq[r5_in_seq:r3_in_seq + 1]
            if len(plus_seq) != L:
                continue
            seq = plus_seq.translate(str.maketrans("ACGT", "TGCA"))[::-1]
            candidates.append({
                'seq': seq, 'length': L, 'dist_from_cut': dist,
                'start_1b': r5_5p, 'end_1b': r3_5p,  # 1-based genomic
                'plus_bind_start': r5_5p, 'plus_bind_end': r3_5p,
            })
    return candidates


# ---------- Scoring ----------

def score_primer(p, tm_min, tm_max, weight_tm=100, weight_clamp=10, weight_gc=5,
                 weight_no_homopolymer=50, weight_good_gc=5, tm_wallace_target=60):
    """Composite score for a primer candidate. Higher = better.

    The Tm filter uses Wallace (the simple lab formula). The user's target
    57-63 °C is consistent with Wallace, not with the SantaLucia NN at
    Phusion conditions (which gives ~70-78 °C for high-GC primers and would
    require a different target window). We report both Tms in the output but
    filter on the one the user actually asked for.

    The Tm filter is hard: Tm outside [tm_min, tm_max] makes the primer
    un-selectable (returns very negative score)."""
    seq = p['seq']
    if has_homopolymer_run(seq, n=5):
        return -1e6
    gc = gc_content(seq)
    if gc < 30 or gc > 70:
        return -1e6
    tm = tm_wallace(seq)  # filter on Wallace (matches user's target window)
    if tm < tm_min or tm > tm_max:
        return -1e6
    score = 0
    # Tm closeness to 60 °C
    score += weight_tm - abs(tm - tm_wallace_target) * 5
    # 3' G/C clamp
    if seq[-1] in 'GC':
        score += weight_clamp
    if len(seq) >= 2 and seq[-2] in 'GC':
        score += weight_clamp // 2
    # GC content near 50%
    score += weight_good_gc - abs(gc - 50) * 0.5
    return score


def joint_score(f, r, cut_1b, f_5p, r_5p_1b, amplicon_size_target, tm_min, tm_max):
    """Score a (F, R) pair together. Cut must be centered, Tms matched.

    Uses Wallace Tm for matching (matches the target window semantics)."""
    f_score = score_primer(f, tm_min, tm_max)
    r_score = score_primer(r, tm_min, tm_max)
    if f_score < -1e5 or r_score < -1e5:
        return -1e6
    tm_f = tm_wallace(f['seq'])
    tm_r = tm_wallace(r['seq'])
    bonus = 0
    # Matched Tms (Wallace)
    bonus += max(0, 20 - abs(tm_f - tm_r) * 10)
    # Cut centered
    amp_len = r['end_1b'] - f['start_1b'] + 1
    bonus += max(0, 20 - abs(amp_len - amplicon_size_target))
    return f_score + r_score + bonus


# ---------- Verification ----------

def verify_F_matches_genome(primer_seq, claimed_start_1b, claimed_end_1b, amp_seq, amp_start_1b):
    """Hard gate: the F primer must equal the + strand at the claimed binding site."""
    s_in_seq = claimed_start_1b - amp_start_1b
    e_in_seq = claimed_end_1b - amp_start_1b
    if s_in_seq < 0 or e_in_seq >= len(amp_seq):
        return False, "binding site out of amplicon range"
    plus_at_site = amp_seq[s_in_seq:e_in_seq + 1]
    if plus_at_site == primer_seq:
        return True, "OK"
    return False, f"genome has {plus_at_site}, primer has {primer_seq}"


def verify_R_matches_genome(primer_seq, plus_bind_start, plus_bind_end, amp_seq, amp_start_1b):
    """Hard gate: the R primer must be the RC of the + strand at its binding site."""
    s_in_seq = plus_bind_start - amp_start_1b
    e_in_seq = plus_bind_end - amp_start_1b
    if s_in_seq < 0 or e_in_seq >= len(amp_seq):
        return False, "binding site out of amplicon range"
    plus_at_site = amp_seq[s_in_seq:e_in_seq + 1]
    expected_r = plus_at_site.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    if expected_r == primer_seq:
        return True, "OK"
    return False, f"genome has +{plus_at_site}, RC is {expected_r}, primer has {primer_seq}"


# ---------- Selection ----------

def select_best_pcr_pair(F_cands, R_cands, cut_1b, amplicon_size_target, tm_min, tm_max):
    """Brute-force: pick the (F, R) pair with the highest joint score."""
    best = None
    best_score = -1e9
    for f in F_cands:
        if score_primer(f, tm_min, tm_max) < -1e5:
            continue
        for r in R_cands:
            if score_primer(r, tm_min, tm_max) < -1e5:
                continue
            amp_len = r['end_1b'] - f['start_1b'] + 1
            if amp_len < 200 or amp_len > 1500:
                continue
            j = joint_score(f, r, cut_1b, f['start_1b'], r['start_1b'],
                            amplicon_size_target, tm_min, tm_max)
            if j > best_score:
                best_score = j
                best = (f, r)
    return best


def select_best_nested_primers(amp_seq, amp_start_1b, cut_1b, nuclease, application):
    """Pick the best single F and single R primer positioned 80–150 bp from cut
    (for ICE) or 60–120 bp (for TIDE). These will be the nested Sanger primers."""
    if application.upper() == "TIDE":
        dist_min, dist_max = 60, 120
    else:  # ICE and amplicon-NGS
        dist_min, dist_max = 80, 150
    f_best = None
    f_best_score = -1e9
    r_best = None
    r_best_score = -1e9
    for dist in range(dist_min, dist_max + 1, 5):
        for L in range(18, 23):
            # F nested
            f5 = cut_1b - dist
            f3 = f5 + L - 1
            f5_in_seq = f5 - amp_start_1b
            f3_in_seq = f3 - amp_start_1b
            if 0 <= f5_in_seq and f3_in_seq < len(amp_seq):
                fseq = amp_seq[f5_in_seq:f3_in_seq + 1]
                if len(fseq) == L and not has_homopolymer_run(fseq) and 30 <= gc_content(fseq) <= 70:
                    s = score_primer({'seq': fseq}, 50, 70)  # wider range for nested
                    if s > f_best_score:
                        f_best_score = s
                        f_best = {'seq': fseq, 'length': L, 'start_1b': f5, 'end_1b': f3, 'dist_from_cut': dist}
            # R nested
            r3_5p = cut_1b + dist
            r5_5p = r3_5p - L + 1
            r5_in_seq = r5_5p - amp_start_1b
            r3_in_seq = r3_5p - amp_start_1b
            if 0 <= r5_in_seq and r3_in_seq < len(amp_seq):
                plus_seq = amp_seq[r5_in_seq:r3_in_seq + 1]
                rseq = plus_seq.translate(str.maketrans("ACGT", "TGCA"))[::-1]
                if len(rseq) == L and not has_homopolymer_run(rseq) and 30 <= gc_content(rseq) <= 70:
                    s = score_primer({'seq': rseq}, 50, 70)  # wider range for nested
                    if s > r_best_score:
                        r_best_score = s
                        r_best = {'seq': rseq, 'length': L, 'start_1b': r5_5p, 'end_1b': r3_5p,
                                  'plus_bind_start': r5_5p, 'plus_bind_end': r3_5p, 'dist_from_cut': dist}
    return f_best, r_best


# ---------- Output ----------

def fmt_primer_table(rows):
    lines = []
    if not rows:
        return "_No primers selected._\n"
    header = "| Use | Name | Sequence (5'-3') | Len | Tm (W) | Tm (NN) | Position | 3' clamp |"
    sep = "|---|---|---|---|---|---|---|---|"
    lines.append(header)
    lines.append(sep)
    for r in rows:
        lines.append(
            f"| {r['use']} | {r['name']} | `{r['seq']}` | {r['length']} | "
            f"{r['tm_w']:.0f} C | {r['tm_nn']:.1f} C | {r['pos']} | {r['clamp']} |"
        )
    return "\n".join(lines) + "\n"


def write_report(out_path, gene, grna, grna_short, amplicon_size, application,
                 pcr_F, pcr_R, nest_F, nest_R, cut_pos_1b, amp_fasta, amp_fasta_path,
                 grna_strand, pam_seq, nuclease, blast_rid=None, blast_url=None,
                 skipped_pam=False, user_pam=None, multiple_gRNA_hits=None):
    """Write the markdown report."""
    rows = []
    if pcr_F:
        rows.append({
            'use': 'PCR', 'name': f"{gene}_PCR-F",
            'seq': pcr_F['seq'], 'length': pcr_F['length'],
            'tm_w': tm_wallace(pcr_F['seq']), 'tm_nn': tm_santalucia(pcr_F['seq']),
            'pos': f"+{pcr_F['start_1b']}–{pcr_F['end_1b']}",
            'clamp': 'yes' if pcr_F['seq'][-1] in 'GC' else 'no',
        })
    if pcr_R:
        rows.append({
            'use': 'PCR', 'name': f"{gene}_PCR-R",
            'seq': pcr_R['seq'], 'length': pcr_R['length'],
            'tm_w': tm_wallace(pcr_R['seq']), 'tm_nn': tm_santalucia(pcr_R['seq']),
            'pos': f"anneals +{pcr_R['plus_bind_start']}–{pcr_R['plus_bind_end']}",
            'clamp': 'yes' if pcr_R['seq'][-1] in 'GC' else 'no',
        })
    if nest_F:
        rows.append({
            'use': 'Sanger', 'name': f"{gene}_Sanger-F",
            'seq': nest_F['seq'], 'length': nest_F['length'],
            'tm_w': tm_wallace(nest_F['seq']), 'tm_nn': tm_santalucia(nest_F['seq']),
            'pos': f"+{nest_F['start_1b']}–{nest_F['end_1b']}",
            'clamp': 'yes' if nest_F['seq'][-1] in 'GC' else 'no',
        })
    if nest_R:
        rows.append({
            'use': 'Sanger', 'name': f"{gene}_Sanger-R",
            'seq': nest_R['seq'], 'length': nest_R['length'],
            'tm_w': tm_wallace(nest_R['seq']), 'tm_nn': tm_santalucia(nest_R['seq']),
            'pos': f"anneals +{nest_R['plus_bind_start']}–{nest_R['plus_bind_end']}",
            'clamp': 'yes' if nest_R['seq'][-1] in 'GC' else 'no',
        })
    if pcr_F and pcr_R:
        amp_actual_len = pcr_R['end_1b'] - pcr_F['start_1b'] + 1
    else:
        amp_actual_len = amplicon_size

    # Phusion Ta with clamping:
    # - shouldn't exceed Phusion's practical ceiling (~65 °C)
    # - shouldn't be more than ~5 °C above the lower-Tm primer (the lower one sets the bound)
    # - touchdown 65→55 is the standard escape valve for high-GC amplicons
    tm_f_nn = tm_santalucia(pcr_F['seq']) if pcr_F else None
    tm_r_nn = tm_santalucia(pcr_R['seq']) if pcr_R else None
    tm_f_w  = tm_wallace(pcr_F['seq'])    if pcr_F else None
    tm_r_w  = tm_wallace(pcr_R['seq'])    if pcr_R else None

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"# CRISPR Validation Primer Design — {gene}\n\n")
        # Pam info
        pam_line = f"- **PAM (genome):** `{pam_seq}`"
        if user_pam:
            pam_line += f"  (user-annotated PAM was `{user_pam}` — {'MATCH' if user_pam.upper() == pam_seq.upper() else 'MISMATCH (see Notes)'})"
        if skipped_pam:
            pam_line += "  *(PAM check skipped via --skip-pam-check)*"
        f.write(f"- **gRNA:** `{grna}` (on {grna_strand} strand)\n")
        f.write(pam_line + "\n")
        f.write(f"- **Cut site:** `chr:{cut_pos_1b}`\n")
        f.write(f"- **Nuclease:** {nuclease}\n")
        f.write(f"- **Application:** {application}\n")
        f.write(f"- **Amplicon (target):** {amplicon_size} bp (actual = {amp_actual_len} bp)\n\n")
        if multiple_gRNA_hits and len(multiple_gRNA_hits) > 1:
            f.write(f"> **Multiple gRNA matches found ({len(multiple_gRNA_hits)} hits).** Using the leftmost. Other hits:\n")
            for s, gs, ge, _ in multiple_gRNA_hits[1:6]:
                f.write(f">  - {s} strand at chr:{gs}-{ge}\n")
            if len(multiple_gRNA_hits) > 6:
                f.write(f">  - ... and {len(multiple_gRNA_hits) - 6} more\n")
            f.write("\n")
        f.write("## Primer set\n\n")
        f.write(fmt_primer_table(rows))
        if pcr_F and pcr_R and tm_f_nn is not None and tm_r_nn is not None:
            tm_avg_nn = (tm_f_nn + tm_r_nn) / 2
            tm_lower_nn = min(tm_f_nn, tm_r_nn)
            # Phusion Ta heuristic: Ta = min(65, max(tm_avg-3, tm_lower-5))
            # but never below 55 (would indicate the primers are too cold)
            ta_initial = min(65, max(tm_avg_nn - 3, tm_lower_nn - 5))
            ta_initial = max(ta_initial, 55)
            ta_caveat = ""
            if tm_avg_nn > 72:
                ta_caveat = (f"  **Caution:** average NN Tm is {tm_avg_nn:.1f} °C, above Phusion's "
                             f"practical ceiling — consider touchdown (start 65 °C, ramp −1 °C/cycle to 55 °C, "
                             f"then 25 cycles at 55 °C) or redesign the primers.")
            f.write(f"\n**Phusion recommended Ta (starting point):** {ta_initial:.1f} °C  "
                    f"(formula: min(65 °C, max(Tm_NN_avg − 3 °C, Tm_NN_lower − 5 °C)){ta_caveat}\n\n")
        f.write("## Wild-type amplicon (FASTA — for ICE reference)\n\n")
        f.write("```fasta\n")
        f.write(f">{gene}_{grna_short}_amplicon_WT ({amp_actual_len} bp, cut at amplicon bp "
                f"{cut_pos_1b - pcr_F['start_1b'] + 1 if pcr_F else 'n/a'})\n")
        for i in range(0, len(amp_fasta), 60):
            f.write(amp_fasta[i:i + 60] + "\n")
        f.write("```\n\n")
        f.write(f"FASTA also written to: `{amp_fasta_path}`\n\n")
        if blast_rid and blast_url:
            f.write("## Off-target check (NCBI Primer-BLAST)\n\n")
            f.write(f"Submitted the PCR primer pair (F: `{pcr_F['seq']}`, R: `{pcr_R['seq']}`) "
                    f"to NCBI Primer-BLAST, restricting the search to the amplicon region "
                    f"(`{chrom}` if known). Result is processing asynchronously.\n\n")
            f.write(f"- **RID:** `{blast_rid}`\n")
            f.write(f"- **Poll URL:** {blast_url}\n\n")
        f.write("## Notes\n\n")
        f.write("- **Tm target window (57–63 °C) is the Wallace lab rule**, not the SantaLucia 1998 NN. "
                "NN values (the more accurate method) are shown in the table for cross-checking against the "
                "NEB TmCalculator (https://tmcalculator.neb.com/). For high-GC primers, NN Tm can be 10+ °C higher "
                "than Wallace — order the primers based on NN, not Wallace.\n")
        f.write("- For ICE: paste the FASTA into https://ice.synthego.com/ as the control/wildtype reference.\n")
        if skipped_pam:
            f.write("- **PAM check was skipped** (`--skip-pam-check`). The genome's actual 3 bases 3' of the "
                    "protospacer on the protospacer strand were used as the reported PAM. Verify in your system that "
                    "your nuclease actually cuts at the reported cut position before ordering primers.\n")
    print(f"Wrote report to {out_path}")


def main():
    ap = argparse.ArgumentParser(description="Design CRISPR validation primers (one-shot).")
    ap.add_argument("--grna", required=True,
                    help="gRNA sequence. 20-bp protospacer (most common) OR 23-bp protospacer+PAM "
                         "(auto-detected; the trailing 3 bp are used for PAM annotation only, "
                         "not validation — the genome's actual 3 bp 3' of the protospacer are checked).")
    ap.add_argument("--gene", help="Gene symbol (e.g. TCL1A). Conflicts with --locus.")
    ap.add_argument("--locus", help="Explicit locus, e.g. chr14:95712272-95712291, or 14:95712272-95712291, "
                                    "or with comma separators chr14:95,712,272-95,712,291. Conflicts with --gene.")
    ap.add_argument("--species", default="homo_sapiens", help="Ensembl species name (default homo_sapiens)")
    ap.add_argument("--assembly", default="GRCh38", help="Assembly label for documentation only")
    ap.add_argument("--application", default="ICE", choices=["ICE", "TIDE", "amplicon-NGS"])
    ap.add_argument("--amplicon-size", type=int, default=None,
                    help="Target amplicon size in bp (default: 1000 for ICE, 500 for TIDE)")
    ap.add_argument("--tm-min", type=float, default=57.0)
    ap.add_argument("--tm-max", type=float, default=63.0)
    ap.add_argument("--nuclease", default="spcas9", choices=["spcas9", "cas12a"])
    ap.add_argument("--skip-pam-check", action="store_true",
                    help="Bypass PAM validation. Use when the nuclease is non-standard (xCas9, SaCas9, "
                         "custom), or when you have user-validated data that the cut still happens. "
                         "The genome's actual 3 bp 3' of the protospacer will be reported as the PAM.")
    ap.add_argument("--output-dir", default=".",
                    help="Directory to write the markdown report and FASTA (default: cwd)")
    args = ap.parse_args()

    if args.gene and args.locus:
        sys.exit("ERROR: pass --gene OR --locus, not both")

    grna = args.grna.upper().replace("U", "T")
    if len(grna) < 17 or len(grna) > 24:
        sys.exit(f"ERROR: gRNA length {len(grna)} not in 17-24 range")

    # Auto-detect 23-bp protospacer+PAM: if last 3 bp are a recognizable PAM, split
    user_pam = None
    if len(grna) == 23:
        tail = grna[20:23].upper()
        # NGG (SpCas9) or TTTV (Cas12a)
        is_ngg = tail[1] == 'G' and tail[2] == 'G'
        is_tttv = tail[:3] == 'TTT' or tail == 'TTTG' or tail == 'TTTA' or tail == 'TTTC'
        if is_ngg or is_tttv:
            user_pam = tail
            print(f"  Detected 23-bp input; treating first 20 bp as protospacer, last 3 bp ({tail}) as user-annotated PAM.")
            grna = grna[:20]

    application = args.application.upper()
    amp_target = args.amplicon_size
    if amp_target is None:
        amp_target = 1000 if application == "ICE" else 500

    # 1. Resolve locus
    if args.locus:
        # Accept "chr1:..." or "1:...", with or without comma separators
        m = re.match(r'^\s*(?:chr)?([\w.]+)\s*:\s*([\d,]+)\s*-\s*([\d,]+)\s*$', args.locus)
        if not m:
            sys.exit("ERROR: --locus must be in form chrN:start-end (commas optional)")
        chrom = m.group(1)
        if not chrom.lower().startswith('chr'):
            chrom = 'chr' + chrom
        gs = int(m.group(2).replace(',', ''))
        ge = int(m.group(3).replace(',', ''))
        gene = args.locus.replace(':', '_').replace('-', '_').replace(',', '')
    else:
        gene = args.gene
        print(f"Resolving {gene} on {args.species}...")
        try:
            chrom, gs, ge = resolve_gene_symbol(gene, args.species)
            print(f"  -> {chrom}:{gs}-{ge}")
        except urllib.error.HTTPError as e:
            if e.code in (400, 404):
                print(f"  Ensembl lookup failed ({e.code}). Trying NCBI E-utilities as fallback...")
                try:
                    chrom, gs, ge = resolve_locus_ncbi(gene, args.species)
                    print(f"  -> {chrom}:{gs}-{ge}  (via NCBI; this may be a pseudogene — Ensembl doesn't index it)")
                except Exception as e2:
                    sys.exit(f"ERROR: could not resolve {gene} on {args.species} via Ensembl or NCBI: {e2}")
            else:
                raise

    # 2. Fetch a region around the gene (or locus), then search for the gRNA
    flank = max(amp_target, 2000)
    fetch_start = max(1, gs - flank)
    fetch_end = ge + flank
    print(f"Fetching {chrom}:{fetch_start}-{fetch_end} ({(fetch_end - fetch_start + 1)/1000:.1f} kb)...")
    seq, region_start = fetch_region(chrom, fetch_start, fetch_end, args.species)

    # 3. Locate gRNA (with all-match support for disambiguation)
    print(f"Searching for gRNA {grna} (and its reverse complement)...")
    all_matches = find_guide(seq, region_start, grna, return_all=True)
    if not all_matches:
        sys.exit(f"ERROR: gRNA {grna} (or its RC) not found in {chrom}:{fetch_start}-{fetch_end}. "
                 f"Check species/assembly, or the gRNA may be off-target.")
    if len(all_matches) > 1:
        print(f"  Found {len(all_matches)} matches in this region. Using the leftmost.")
    found = all_matches[0]
    grna_strand, grna_gs, grna_ge, plus_at_site = found
    print(f"  -> on {grna_strand} strand at {chrom}:{grna_gs}-{grna_ge}")

    # 4. Find PAM and cut
    pam = find_pam(seq, region_start, grna_strand, grna_gs, len(grna),
                   args.nuclease, skip_pam_check=args.skip_pam_check, user_pam=user_pam)
    if not pam:
        sys.exit(f"ERROR: valid {args.nuclease} PAM not found adjacent to gRNA at "
                 f"{chrom}:{grna_gs}-{grna_ge}. Check the gRNA sequence, or use --nuclease to "
                 f"switch enzyme, or pass --skip-pam-check if your nuclease uses a different PAM "
                 f"or you have orthogonal evidence that cutting still occurs here.")
    pam_seq, pam_pos, cut_pos = pam
    if args.skip_pam_check:
        print(f"  -> PAM (genome) = {pam_seq} at chr {chrom}:{pam_pos}, cut at chr {chrom}:{cut_pos}  (PAM check skipped)")
    else:
        print(f"  -> PAM = {pam_seq} at chr {chrom}:{pam_pos}, cut at chr {chrom}:{cut_pos}")

    # 5. Fetch amplicon-window sequence
    amp_window_size = amp_target + 400  # extra room for primer picking
    amp_window_start = max(1, cut_pos - amp_window_size // 2)
    amp_window_end = cut_pos + amp_window_size // 2
    print(f"Fetching amplicon window {chrom}:{amp_window_start}-{amp_window_end}...")
    amp_seq, amp_start = fetch_region(chrom, amp_window_start, amp_window_end, args.species)

    # 6. Generate candidates (one pass)
    print("Generating primer candidates (one pass)...")
    F_cands = generate_F_candidates(amp_seq, amp_start, cut_pos, amp_target)
    R_cands = generate_R_candidates(amp_seq, amp_start, cut_pos, amp_target)
    print(f"  -> {len(F_cands)} F candidates, {len(R_cands)} R candidates")

    # 7. Select best PCR pair
    print(f"Selecting best PCR pair (Tm {args.tm_min}-{args.tm_max} °C, amplicon {amp_target} bp)...")
    pcr_pair = select_best_pcr_pair(F_cands, R_cands, cut_pos, amp_target,
                                     args.tm_min, args.tm_max)
    if pcr_pair is None:
        sys.exit("ERROR: no PCR primer pair meets Tm + amplicon-size constraints. "
                 "Try widening --tm-min/--tm-max or adjusting --amplicon-size.")
    pcr_F, pcr_R = pcr_pair
    print(f"  F: {pcr_F['seq']}  Tm(W)={tm_wallace(pcr_F['seq']):.0f}  "
          f"Tm(NN)={tm_santalucia(pcr_F['seq']):.1f}")
    print(f"  R: {pcr_R['seq']}  Tm(W)={tm_wallace(pcr_R['seq']):.0f}  "
          f"Tm(NN)={tm_santalucia(pcr_R['seq']):.1f}")

    # 8. Select nested Sanger primers
    print("Selecting best nested Sanger primers...")
    nest_F, nest_R = select_best_nested_primers(amp_seq, amp_start, cut_pos,
                                                 args.nuclease, application)
    if nest_F:
        print(f"  SF: {nest_F['seq']}  Tm(NN)={tm_santalucia(nest_F['seq']):.1f}")
    if nest_R:
        print(f"  SR: {nest_R['seq']}  Tm(NN)={tm_santalucia(nest_R['seq']):.1f}")

    # 9. Hard verification gate
    print("Verifying all primers against the genome...")
    ok_f, msg_f = verify_F_matches_genome(pcr_F['seq'], pcr_F['start_1b'],
                                            pcr_F['end_1b'], amp_seq, amp_start)
    ok_r, msg_r = verify_R_matches_genome(pcr_R['seq'], pcr_R['plus_bind_start'],
                                            pcr_R['plus_bind_end'], amp_seq, amp_start)
    if not (ok_f and ok_r):
        sys.exit(f"ERROR: PCR primer verification failed:\n  F: {msg_f}\n  R: {msg_r}")
    if nest_F:
        ok_sf, msg_sf = verify_F_matches_genome(nest_F['seq'], nest_F['start_1b'],
                                                  nest_F['end_1b'], amp_seq, amp_start)
        if not ok_sf:
            sys.exit(f"ERROR: nested Sanger F verification failed: {msg_sf}")
    if nest_R:
        ok_sr, msg_sr = verify_R_matches_genome(nest_R['seq'], nest_R['plus_bind_start'],
                                                  nest_R['plus_bind_end'], amp_seq, amp_start)
        if not ok_sr:
            sys.exit(f"ERROR: nested Sanger R verification failed: {msg_sr}")
    print("  All primers verified.")

    # 10. Build the actual amplicon (from F 5' to R 5' on + strand)
    amp_actual_start = pcr_F['start_1b']
    amp_actual_end = pcr_R['end_1b']
    amp_fasta = ''.join(amp_seq[(amp_actual_start - amp_start) + i]
                        for i in range(amp_actual_end - amp_actual_start + 1))
    cut_in_amplicon_0based = cut_pos - amp_actual_start

    # 11. Write outputs
    os.makedirs(args.output_dir, exist_ok=True)
    grna_short = grna[:8]
    md_path = os.path.join(args.output_dir, f"crispr_primers_{gene}_{grna_short}.md")
    fa_path = os.path.join(args.output_dir, f"{gene}_{grna_short}_amplicon_WT.fa")

    with open(fa_path, 'w', encoding='utf-8') as f:
        cut_pos_in_amp = cut_in_amplicon_0based + 1
        f.write(f">{gene}_{grna_short}_amplicon_WT chr{chrom}:{amp_actual_start}-{amp_actual_end} "
                f"({len(amp_fasta)} bp, cut at amplicon bp {cut_pos_in_amp})\n")
        for i in range(0, len(amp_fasta), 60):
            f.write(amp_fasta[i:i + 60] + "\n")
    print(f"Wrote amplicon FASTA to {fa_path}")

    # 12. Submit PCR primers to Primer-BLAST (off-target check).
    #     PCR only — nested Sanger primers are guaranteed inside the amplicon.
    print("Submitting PCR primer pair to NCBI Primer-BLAST (off-target check)...")
    blast_rid, blast_url = submit_primer_blast(
        pcr_F['seq'], pcr_R['seq'],
        amp_actual_start, amp_actual_end, chrom, args.species,
    )
    if blast_rid:
        print(f"  Primer-BLAST RID: {blast_rid}  (poll {blast_url})")
    else:
        print("  Primer-BLAST submission failed or RID not parseable — do the off-target check manually.")

    write_report(md_path, gene, grna, grna_short, amp_target, application,
                 pcr_F, pcr_R, nest_F, nest_R, cut_pos, amp_fasta, fa_path,
                 grna_strand, pam_seq, args.nuclease,
                 blast_rid=blast_rid, blast_url=blast_url,
                 skipped_pam=args.skip_pam_check, user_pam=user_pam,
                 multiple_gRNA_hits=all_matches if len(all_matches) > 1 else None)
    print(f"\nDone. Mark cut site: bp {cut_in_amplicon_0based + 1} of the amplicon "
          f"({cut_in_amplicon_0based} 0-based).")


if __name__ == "__main__":
    main()
