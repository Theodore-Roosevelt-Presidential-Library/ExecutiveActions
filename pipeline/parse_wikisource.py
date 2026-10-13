"""Parse Wikisource executive-order pages (data/sources/wikisource_eo.json) into plain records.

Output: data/wikisource_eo.jsonl — {id, number, title, date, cite, notes, paragraphs, signed, place, not_located, url, revid}
The transcriptions are volunteer work from printed compilations (often the Civil Service Commission
reports, cited in `cite`). They are public-domain texts but unverified; entry-level collations in the
research file supersede them where they exist.
"""
import json
import re
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def field(tpl, name):
    m = re.search(r"\|\s*" + name + r"\s*=\s*(.*?)\n\s*(?:\||}})", tpl + "\n|", flags=re.S)
    return m.group(1).strip() if m else ""


def strip_markup(s):
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\[\[(?:w:)?[^|\]]*\|([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[(?:w:)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{sc\|([^}]*)\}\}", r"\1", s, flags=re.I)
    s = re.sub(r"\{\{(?:smaller|larger|small-caps|uc|lc)\|([^}]*)\}\}", r"\1", s, flags=re.I)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", s, flags=re.S)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"'''?", "", s)
    s = re.sub(r"^[:;*#]+\s*", "", s, flags=re.M)
    return s.strip()


def eo_id(num):
    n = num.replace("½", "-half").replace(" ", "").lower()
    return "eo-" + re.sub(r"^(\d+)([a-z])$", r"\1-\2", n)


def main():
    raw = json.load(open(ROOT / "data/sources/wikisource_eo.json", encoding="utf-8"))
    out = []
    for title, v in raw.items():
        w = v["wikitext"]
        m = re.search(r"\{\{Potus-eo(.*?)\n\}\}", w, flags=re.S)
        tpl = m.group(1) if m else ""
        # the page title carries the suffix (394-A, 288½); the template's eo field often gives only the base number
        num = title.replace("Executive Order ", "").strip() or field(tpl, "eo")
        body = w[m.end():] if m else w
        body = body.split("==Notes==")[0]
        body = re.sub(r"\{\{PD-USGov[^}]*\}\}|\{\{TextQuality[^}]*\}\}", "", body)
        sig = re.search(r'<div style="text-align:right">(.*?)</div>(.*)$', body, flags=re.S)
        signed = place_date = None
        if sig:
            signed = strip_markup(sig.group(1)).strip(" .") or None
            place_date = re.sub(r"\s+", " ", strip_markup(sig.group(2))).strip() or None
            body = body[:sig.start()]
        paras = [re.sub(r"\s+", " ", strip_markup(p)).strip() for p in re.split(r"\n\s*\n", body)]
        paras = [p for p in paras if p]
        y, mo, dd = field(tpl, "year"), field(tpl, "month"), field(tpl, "day")
        date = f"{int(y):04d}-{int(mo):02d}-{int(dd):02d}" if y.isdigit() and mo.strip().isdigit() and dd.strip().isdigit() else None
        out.append({"id": eo_id(num), "number": num, "title": strip_markup(field(tpl, "section")), "date": date,
                    "cite": strip_markup(field(tpl, "cite")) or None, "notes": strip_markup(field(tpl, "notes")) or None,
                    "paragraphs": paras, "signed": signed, "place_date": place_date,
                    "not_located": bool(re.search(r"text not located", w, flags=re.I)),
                    "url": "https://en.wikisource.org/wiki/" + urllib.parse.quote(v["page"].replace(" ", "_")),
                    "revid": v["revid"]})
    out.sort(key=lambda r: r["id"])
    with open(ROOT / "data/wikisource_eo.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(len(out), "records;", sum(1 for r in out if r["not_located"]), "not located;",
          sum(1 for r in out if not r["paragraphs"]), "empty")


if __name__ == "__main__":
    main()
