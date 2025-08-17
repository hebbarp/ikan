# generator.py — MVP dwipadi generator using your DB word list and prosody checks
import random
from typing import List, Tuple
from prosody import maatra_count, rhyme_score

# Simple beam search over words to approach a target maatra count
def assemble_line(words: List[str], target: int = 12, beam_size: int = 20, max_words: int = 6) -> List[Tuple[str,int]]:
    # state: (line_text, maatra_sum)
    beams = [("", 0)]
    for _ in range(max_words):
        new_beams = []
        for line, msum in beams:
            # keep finished candidates too
            if msum >= target:
                new_beams.append((line, msum))
                continue
            # sample a small subset for speed
            for w in random.sample(words, min(len(words), 80)):
                if line.endswith(" " + w):
                    continue
                new_line = (line + " " + w).strip()
                new_m = msum + maatra_count(w)
                # allow a tiny overshoot
                if new_m <= target + 1:
                    new_beams.append((new_line, new_m))
        # keep beams closest to target
        new_beams.sort(key=lambda x: (abs(target - x[1]), len(x[0])))
        beams = new_beams[:beam_size]
    beams.sort(key=lambda x: (abs(target - x[1]), len(x[0])))
    return beams[:beam_size]

def score_couple(l1: str, l2: str, target:int=12) -> float:
    m1, m2 = maatra_count(l1), maatra_count(l2)
    prosody = 1.0 / (1 + abs(target - m1) + abs(target - m2) + abs(m1 - m2))
    rhyme = rhyme_score(l1, l2)
    return 0.7*prosody + 0.3*rhyme

def generate_dwipadi(words: List[str], target:int=12, k:int=5, seed:int|None=None):
    # Optional deterministic seed; otherwise vary naturally
    if seed is not None:
        random.seed(seed)

    # prefilter super-short/long words (coarse)
    filtered = [w for w in words if 1 <= maatra_count(w) <= 6 and len(w) <= 12]
    if not filtered:
        return []

    # diversify runs
    random.shuffle(filtered)
    L1 = assemble_line(filtered, target=target)
    results = []
    for l1, _ in L1[:20]:
        random.shuffle(filtered)
        L2 = assemble_line(filtered, target=target)
        L2.sort(key=lambda x: abs(target - x[1]))
        candidates = []
        for l2, _ in L2[:20]:
            s = score_couple(l1, l2, target)
            candidates.append((s, l1, l2))
        candidates.sort(reverse=True, key=lambda x: x[0])
        if candidates:
            results.append(candidates[0])

    # global top-k, dedup
    results.sort(reverse=True, key=lambda x: x[0])
    seen=set()
    out=[]
    for s,l1,l2 in results:
        key=(l1,l2)
        if key in seen: continue
        seen.add(key)
        out.append((s,l1,l2))
        if len(out)>=k: break
    return out
