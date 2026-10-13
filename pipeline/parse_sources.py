"""Parse the research catalogs into one base record per document.

Inputs (committed under sources/):
  executive_actions_index.md       numbered EOs 141-1050 (Wikipedia list) and Procs. 465-871 (APP)
  TR_Unnumbered_Orders_Catalog.md  Lord's 126 unnumbered-series entries, reconciled 2026-10-12

Output: data/base.jsonl  (one JSON object per document, sorted by date then id)
"""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "sources"
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September",
     "October", "November", "December"], 1)}
ABBR = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "June": 6, "Jun": 6, "July": 7, "Jul": 7,
        "Aug": 8, "Sept": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


def iso_long(s):
    s = s.strip().replace("  ", " ")
    m = re.match(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", s)
    if not m:
        raise ValueError(s)
    return f"{int(m.group(3)):04d}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"


def lenient_date(s):
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", s)
    if m:
        return iso_long(m.group(0)), "day"
    m = re.search(r"([A-Z][a-z]+)\s+(\d{4})", s)
    if m and m.group(1) in MONTHS:
        return f"{int(m.group(2)):04d}-{MONTHS[m.group(1)]:02d}", "month"
    return None, None


def eo_id(num):
    n = num.replace("½", "-half").replace(" ", "").lower()
    n = re.sub(r"^(\d+)([a-z])$", r"\1-\2", n)  # 302A -> 302-a, like 389-A
    return f"eo-{n}"


def number_sort(num):
    m = re.match(r"(\d+)(.*)", num)
    base = int(m.group(1))
    suf = m.group(2)
    return base + (0.5 if "½" in suf else 0) + (0.01 * (ord(suf[-1]) - 64) if suf and suf[-1].isalpha() else 0)


def parse_index():
    text = (SRC / "executive_actions_index.md").read_text(encoding="utf-8")
    eo_part = text[text.index("## Executive orders — full catalog"):text.index("## Presidential proclamations — full catalog")]
    pr_part = text[text.index("## Presidential proclamations — full catalog"):text.index("## Open items")]
    docs = []
    for line in eo_part.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([0-9]+[^|]*?)\s*\|\s*(.+?)\s*\|\s*([^|]*?)\s*\|", line)
        if not m:
            continue
        rel, num, title, date_s = m.groups()
        date, precision = lenient_date(date_s)
        docs.append({"id": eo_id(num), "type": "executive_order", "number": num.strip(),
                     "number_sort": number_sort(num.strip()), "tr_sequence": int(rel),
                     "date": date, "date_precision": precision, "title": title.strip(),
                     "title_source": "Wikipedia, List of executive actions by Theodore Roosevelt"})
    for line in pr_part.splitlines():
        m = re.match(r"^\|\s*(\d{3})\s*\|\s*(.+?)\s*\|\s*([A-Z][a-z]+ \d{1,2}, \d{4})[^|]*\|", line)
        if not m:
            continue
        num, title, date = m.groups()
        docs.append({"id": f"proc-{num}", "type": "proclamation", "number": num, "number_sort": int(num),
                     "date": iso_long(date), "date_precision": "day", "title": title.strip(), "title_source": "American Presidency Project"})
    return docs


def lord_date(s):
    s = re.sub(r"\*.*", "", s).replace("*", "").strip()
    m = re.match(r"(\d{4})\s+\[?([A-Z][a-z]+)\.?\s+(\d{1,2})\]?", s)
    if not m:
        return None, s
    y, mo, d = m.groups()
    return f"{int(y):04d}-{ABBR[mo]:02d}-{int(d):02d}", s


def parse_lord():
    text = (SRC / "TR_Unnumbered_Orders_Catalog.md").read_text(encoding="utf-8")
    docs = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*(\d{1,3})\s*\|\s*([AB?C]+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*(.*?)\s*\|\s*$", line)
        if not m:
            continue
        no, recon, date_s, desc, cites, page, note = m.groups()
        date, raw = lord_date(date_s)
        bracketed = "[" in date_s
        dup = None
        if recon.strip() == "B":
            # pull the numbered identification out of the note
            mm = re.search(r"(?:=|Probably = |part of )\s*\**\s*(EO|Proc\.?|Proclamation|Executive Order)\s*([0-9]+(?:[-–][A-Z]|½)?)", note)
            if mm:
                kind = "eo" if mm.group(1).startswith(("EO", "Exec")) else "proc"
                num = mm.group(2).replace("–", "-")
                dup = eo_id(num) if kind == "eo" else f"proc-{num}"
        docs.append({"id": f"uo-{int(no):03d}", "type": "unnumbered_order", "number": None,
                     "lord_number": int(no), "date": date, "date_note": raw if (bracketed or "*" in date_s or "sic" in date_s) else None,
                     "date_inferred_by_lord": bracketed,
                     "title": re.sub(r"\s*\*\(.*?\)\*", "", desc).strip(), "lord_description": desc.strip(),
                     "lord_citations": cites.strip(), "lord_page": page.strip(),
                     "reconciliation": "numbered_duplicate" if recon.strip() == "B" else "distinct",
                     "duplicate_of": dup, "reconciliation_note": note.strip(),
                     "title_source": "Lord (ed.), List and Index of Presidential Executive Orders, Unnumbered Series (1943)"})
    return docs


def main():
    docs = parse_index() + parse_lord()
    counts = {}
    for d in docs:
        counts[d["type"]] = counts.get(d["type"], 0) + 1
    docs.sort(key=lambda d: (d["date"] or "9999", d["type"] != "proclamation", d.get("number_sort") or 0, d["id"]))
    ids = [d["id"] for d in docs]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, dupes
    out = ROOT / "data/base.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(counts, "->", out)
    bad = [d["id"] for d in docs if d["type"] == "unnumbered_order" and d["reconciliation"] == "numbered_duplicate" and not d["duplicate_of"]]
    print("Lord duplicates without a parsed target:", bad)
    missing = [d["duplicate_of"] for d in docs if d.get("duplicate_of") and d["duplicate_of"] not in set(ids)]
    print("duplicate_of targets not in the numbered series:", missing)


if __name__ == "__main__":
    main()
