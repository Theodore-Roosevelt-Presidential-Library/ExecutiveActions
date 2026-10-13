"""Extract Roosevelt's proclamations from the Statutes at Large (GovInfo USLM XML, vols. 32-36).

Input:  private/statutes/STATUTE-{32..36}.xml  (download: https://www.govinfo.gov/content/pkg/STATUTE-NN/uslm/STATUTE-NN.xml)
Output: data/statutes_proclamations.jsonl — one object per proclamation signed by Roosevelt:
        volume, statutes_number ("[No. N.]"), date, first/last page, list title (the volume's table
        of proclamations), paragraphs (verbatim text, marginal notes removed), marginal_notes,
        signer, countersigner, countersigner_role, has_seal.

The XML text is GPO's vendor digitization of the printed volume. It is public domain but not
proofread; transcription slips occur (e.g. "dpublic", "eclare"). Treat it as a working text and
collate against the page image (STATUTE-NN-PgPPPP.pdf) before quoting.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "private/statutes"
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September",
     "October", "November", "December"], 1)}


def clean_inline(x):
    x = re.sub(r"<sidenote>.*?</sidenote>", " ", x, flags=re.S)
    x = re.sub(r"<page[^>]*>\d+</page>|<page\s*/>", " ", x)
    x = re.sub(r'<inline class="smallCaps">\s*seal\s*</inline>', "SEAL", x, flags=re.I)
    x = re.sub(r"<[^>]+>", "", x)
    x = x.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    x = re.sub(r"\s+", " ", x).strip()
    x = re.sub(r"-\s+(?=[a-z])", "-", x) if False else x
    return x


def sidenotes(x):
    out = []
    for sn in re.findall(r"<sidenote>(.*?)</sidenote>", x, flags=re.S):
        for p in re.findall(r"<p[^>]*>(.*?)</p>", sn, flags=re.S):
            t = clean_inline(p)
            if t:
                out.append(t)
    return out


def list_titles(t, vol):
    """The volume's table of proclamations (<listOfProclamations>): label, date, start page, in printed order."""
    items = []
    blocks = re.findall(r"<listOfProclamations>(.*?)</listOfProclamations>", t, flags=re.S)
    t = "\n".join(blocks)
    for m in re.finditer(r"<referenceItem><label>(.*?)</label>\s*<label[^>]*>([A-Z][a-z]+ \d{1,2}, \d{4})</label>\s*<target>(\d+)</target></referenceItem>", t):
        label, date, page = m.groups()
        mo = re.match(r"([A-Z][a-z]+) (\d{1,2}), (\d{4})", date)
        if mo.group(1) not in MONTHS:
            continue
        iso = f"{mo.group(3)}-{MONTHS[mo.group(1)]:02d}-{int(mo.group(2)):02d}"
        items.append({"label": clean_inline(label).lstrip(". "), "date": iso, "page": int(page)})
    return items


def parse_volume(vol):
    path = SRC / f"STATUTE-{vol}.xml"
    t = path.read_text(encoding="utf-8")
    titles = list_titles(t, vol)
    out = []
    for m in re.finditer(r'<presidentialDoc role="proclamation">(.*?)</presidentialDoc>', t, flags=re.S):
        body = m.group(1)
        # the page this document starts on: last page marker before it
        before = t[:m.start()]
        pm = list(re.finditer(r'<page identifier="/us/stat/\d+/(\d+)"', before[-20000:]))
        start_page = int(pm[-1].group(1)) + (0 if not pm else 0) if pm else None
        inner_pages = [int(p) for p in re.findall(r'<page identifier="/us/stat/\d+/(\d+)"', body)]
        # GovInfo prints page markers at page bottoms ("renderingPosition=bottom") and tops; the
        # document starts on the page after the last bottom marker, or the last top marker
        last = pm[-1] if pm else None
        if last is not None:
            seg = before[-20000:][last.start():last.start() + 120]
            start_page = int(last.group(1)) + (1 if 'renderingPosition="bottom"' in seg else 0)
        num = re.search(r"<docNumber>(\d+)</docNumber>", body)
        ad = re.search(r'<approvedDate date="(\d{4}-\d{2}-\d{2})"', body)
        dcd = re.search(r"<dc:date>([^<]+)</dc:date>", body)
        date = ad.group(1) if ad else None
        if not date and dcd:
            mo = re.match(r"([A-Z][a-z]+)\.? (\d{1,2}), (\d{4})", dcd.group(1).strip())
            if mo and mo.group(1) in MONTHS:
                date = f"{mo.group(3)}-{MONTHS[mo.group(1)]:02d}-{int(mo.group(2)):02d}"
        content = re.search(r"<content>(.*)</content>", body, flags=re.S)
        content = content.group(1) if content else body
        sig_block = re.search(r"<signatures>(.*?)</signatures>", content, flags=re.S)
        sigs = []
        if sig_block:
            for s in re.findall(r"<signature>(.*?)</signature>", sig_block.group(1), flags=re.S):
                sigs.append(clean_inline(s))
            content_wo = content[:sig_block.start()]
        else:
            content_wo = content
        paras = []
        for p in re.findall(r"<(?:recital|p)[^>]*>(.*?)</(?:recital|p)>", re.sub(r"<sidenote>.*?</sidenote>", "", content_wo, flags=re.S), flags=re.S):
            c = clean_inline(p)
            if c:
                paras.append(c)
        notes = sidenotes(content)
        signer = sigs[0] if sigs else None
        counter = None
        role = None
        names = [s for s in sigs if s and not s.lower().startswith("by the president")]
        if len(names) >= 2:
            counter = names[1]
            role = names[2] if len(names) >= 3 else None
        has_seal = bool(re.search(r"\[\s*SEAL\s*\.?\s*\]", " ".join(paras), flags=re.I))
        out.append({"volume": vol, "statutes_number": int(num.group(1)) if num else None, "date": date,
                    "page": start_page, "last_page": max(inner_pages) if inner_pages else start_page,
                    "paragraphs": paras, "marginal_notes": notes, "signatures": sigs,
                    "signer": signer, "countersigner": counter, "countersigner_role": role,
                    "has_seal": has_seal})
    # attach list titles: the list and the documents run in the same printed order
    if len(titles) == len(out):
        for d, it in zip(out, titles):
            d["list_titles"] = [it["label"]]
            d["list_page"] = it["page"]
            d["list_date"] = it["date"]
    else:
        print(f"  vol {vol}: list has {len(titles)} items for {len(out)} documents; matching by date and page order")
        pool = list(titles)
        for d in out:
            pg = d["page"] or 0
            c = next((it for it in pool if it["date"] == d["date"] and abs(it["page"] - pg) <= 1), None)
            d["list_titles"] = [c["label"]] if c else []
            if c:
                d["list_page"] = c["page"]
                d["list_date"] = c["date"]
                pool.remove(c)
    for d in out:
        if d.get("list_page"):
            d["page"] = d["list_page"]
    return out


def main():
    rows = []
    for vol in (32, 33, 34, 35, 36):
        if (SRC / f"STATUTE-{vol}.xml").exists():
            v = parse_volume(vol)
            print(vol, len(v))
            rows += v
    tr = [r for r in rows if r["date"] and "1901-09-14" <= r["date"] <= "1909-03-04"
          and (any("roosevelt" in (s or "").lower() for s in r["signatures"][:1]) or not r["signatures"])]
    for r in tr:
        r["signature_block_missing_in_xml"] = not r["signatures"]
    tr.sort(key=lambda r: (r["date"], r["volume"], r["statutes_number"] or 0))
    with open(ROOT / "data/statutes_proclamations.jsonl", "w", encoding="utf-8") as f:
        for r in tr:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("Roosevelt proclamations in the Statutes:", len(tr))
    nosig = [r for r in rows if r["date"] and "1901-09-14" <= r["date"] <= "1909-03-04" and r not in tr]
    print("in date range but not signed T. Roosevelt in the first signature:", len(nosig))
    for r in nosig[:10]:
        print("  ", r["volume"], r["statutes_number"], r["date"], r["signatures"][:2])


if __name__ == "__main__":
    main()
