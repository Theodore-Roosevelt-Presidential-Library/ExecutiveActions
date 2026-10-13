"""Match each numbered proclamation (APP Nos. 465-871) to its printing in the Statutes at Large.

Matching rests on the *names* in the APP title (forest, reservation, place, country) found in the
text of the printed proclamation, plus date proximity. The volumes' own tables of contents are used
only as a tie-breaker, because in vols. 34-36 they run out of step with the documents.

Writes data/proclamation_statutes_map.json and prints a validation report. Manual pairings for the
handful the text cannot decide live in data/statutes_overrides.json.
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERIC = set("""establishing establishment establish setting apart aside enlarging enlargement enlarge boundaries boundary
modifying modification modify reducing reduction diminishing diminution forest reserve reserves national monument
monuments the of and a an to in for on at by with as from land lands public domain proclamation announcing
granting certain revoking revocation restoring restoration opening open partial part withdrawal withdrawl
reservation reservations indian indians state states united territory day county city town townsite site
eliminating excluding including include adding addition additions transferring transfer consolidating consolidation
change changing extending extension benefits law laws president ex""".split())


def norm(s):
    s = s.lower().replace("’", "'").replace("- ", "")
    return re.sub(r"\s+", " ", s)


def name_tokens(title):
    title = re.sub(r"\*\(.*?\)\*|\(.*?\)", "", title)
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]+", title)
    return [t.lower() for t in toks if t.lower() not in GENERIC and len(t) > 2]


def d(s):
    return date.fromisoformat(s)


def main():
    base = [json.loads(l) for l in open(ROOT / "data/base.jsonl", encoding="utf-8")]
    procs = [b for b in base if b["type"] == "proclamation"]
    st = [json.loads(l) for l in open(ROOT / "data/statutes_proclamations.jsonl", encoding="utf-8")]
    for i, s in enumerate(st):
        s["_i"] = i
        s["_text"] = norm(" ".join(s["paragraphs"]))
        s["_head"] = s["_text"][:1800]
        s["_title"] = norm(" ".join(s.get("list_titles") or []))
    pairs = []
    for p in procs:
        toks = name_tokens(p["title"])
        for s in st:
            gap = abs((d(p["date"]) - d(s["date"])).days)
            if gap > 45:
                continue
            if toks:
                hit_head = sum(1 for t in toks if t in s["_head"]) / len(toks)
                hit_all = sum(1 for t in toks if t in s["_text"]) / len(toks)
                hit_title = sum(1 for t in toks if t in s["_title"]) / len(toks)
                score = 0.55 * hit_head + 0.25 * hit_all + 0.2 * hit_title
            else:
                score = 0.2
            score += (0.25 if gap == 0 else 0.1 if gap <= 3 else 0) - gap * 0.003
            pairs.append((round(score, 4), p["id"], s["_i"], gap))
    pairs.sort(key=lambda x: (-x[0], x[3]))
    used_p, used_s, out = set(), set(), {}
    overrides = json.load(open(ROOT / "data/statutes_overrides.json")) if (ROOT / "data/statutes_overrides.json").exists() else {}
    forced = []
    for pid, key in overrides.items():
        si = next(s["_i"] for s in st if s["volume"] == key["volume"] and s["page"] == key["page"] and s["date"] == key["date"]
                  and key.get("contains", "").lower() in s["_text"])
        pdate = next(p["date"] for p in procs if p["id"] == pid)
        forced.append((9.0, pid, si, abs((d(pdate) - d(st[si]["date"])).days)))
    for score, pid, si, gap in forced + pairs:
        if pid in used_p or si in used_s:
            continue
        used_p.add(pid)
        used_s.add(si)
        s = st[si]
        out[pid] = {"volume": s["volume"], "page": s["page"], "last_page": s["last_page"],
                    "statutes_number": s["statutes_number"], "statutes_date": s["date"],
                    "list_title": (s.get("list_titles") or [None])[0], "score": score, "date_gap_days": gap, "_i": si}
    json.dump(out, open(ROOT / "data/proclamation_statutes_map.json", "w"), indent=0, ensure_ascii=False)
    weak = []
    for p in procs:
        m = out.get(p["id"])
        if not m:
            continue
        toks = name_tokens(p["title"])
        miss = [t for t in toks if t not in st[m["_i"]]["_text"]]
        if miss and len(miss) >= max(1, len(toks) / 2):
            weak.append((p["id"], p["title"][:70], miss, st[m["_i"]]["_head"][:110]))
    print("matched", len(out), "of", len(procs))
    print("unmatched APP:", [(p["id"], p["date"], p["title"][:60]) for p in procs if p["id"] not in out])
    print("Statutes proclamations not in the APP list:")
    for s in st:
        if s["_i"] not in used_s:
            print("  ", s["volume"], s["page"], s["date"], (s.get("list_titles") or [""])[0], "|", s["_head"][:90])
    print("date differences:", [(k, v["statutes_date"], v["date_gap_days"]) for k, v in out.items() if v["date_gap_days"]])
    print("WEAK (name tokens missing from matched text):", len(weak))
    for w in weak:
        print("  ", w)


if __name__ == "__main__":
    main()
