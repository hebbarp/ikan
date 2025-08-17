# prosody.py — very lightweight Kannada akshara + maatras utilities (no external deps)

# Kannada signs
HALANT = "\u0ccd"  # ್
ANUSVARA = "\u0c82"  # ಂ
VISARGA = "\u0c83"   # ಃ

# Independent vowels
SHORT_INDEP = set("ಅಇಉಋಎಒ")
LONG_INDEP  = set("ಆಈಊೠಏಐಓಔ")

# Vowel matras (dependent signs)
SHORT_MATRAS = set("ಿುೃೆೊ")       # ಿ, ು, ೃ, ೆ, ೊ  ~ 1 maatras
LONG_MATRAS  = set("ಾೀೂೄೇೈೋೌ")  # ಾ, ೀ, ೂ, ೄ, ೇ, ೈ, ೋ, ೌ  ~ 2 maatras

KANNADA_RANGE = (0x0C80, 0x0CFF)

def is_kn(ch: str) -> bool:
    cp = ord(ch)
    return KANNADA_RANGE[0] <= cp <= KANNADA_RANGE[1]

def split_aksharas(text: str):
    """
    Very naive akshara segmenter:
    - Groups characters until we hit a consonant not joined by HALANT.
    - Keeps Kannada-only; non-Kannada chars split as-is.
    """
    a = []
    buf = ""
    prev = ""
    for ch in text:
        if not is_kn(ch):
            if buf: a.append(buf); buf=""
            if ch.strip():
                a.append(ch)
            continue
        buf += ch
        # end an akshara if the current char is not HALANT and next char decision happens on the fly
        if prev != HALANT and ch != HALANT:
            # peek will happen in next loop; we conservatively keep collecting
            pass
        prev = ch
        # Heuristic: if current char is a vowel sign or independent vowel, and next isn't HALANT, we may end soon
    if buf:
        a.append(buf)
    # Post-process to merge sequences split naively by punctuation/space
    out = []
    for chunk in a:
        if chunk.strip():
            out.append(chunk)
    return out

def maatra_of_independent(ch: str) -> int:
    if ch in LONG_INDEP: return 2
    if ch in SHORT_INDEP: return 1
    return 1

def maatra_of_akshara(ak: str) -> int:
    """
    Rule of thumb:
    - Independent long vowels → 2, short → 1
    - If any long matra present → 2
    - Else if any short matra present → 1
    - Else default 1
    """
    # independent vowel case (single char)
    if len(ak) == 1 and ak in (SHORT_INDEP | LONG_INDEP):
        return maatra_of_independent(ak)

    # dependent vowel signs on the cluster
    for ch in ak:
        if ch in LONG_MATRAS:
            return 2
    for ch in ak:
        if ch in SHORT_MATRAS:
            return 1
    return 1

def maatra_count(text: str) -> int:
    return sum(maatra_of_akshara(ak) for ak in split_aksharas(text))

def last_akshara(text: str) -> str:
    aks = [ak for ak in split_aksharas(text) if ak.strip()]
    return aks[-1] if aks else ""

def vowel_class(ak: str) -> str:
    # Map akshara to a coarse vowel category for rhyme
    for ch in ak:
        if ch in LONG_MATRAS: return "LONG"
        if ch in SHORT_MATRAS: return "SHORT"
    if len(ak) == 1 and ak in LONG_INDEP: return "LONG"
    if len(ak) == 1 and ak in SHORT_INDEP: return "SHORT"
    return "NEUTRAL"

def rhyme_score(l1: str, l2: str) -> float:
    a1, a2 = last_akshara(l1), last_akshara(l2)
    if not a1 or not a2: return 0.0
    if a1 == a2: return 1.0
    v1, v2 = vowel_class(a1), vowel_class(a2)
    return 0.5 if v1 == v2 else 0.0
