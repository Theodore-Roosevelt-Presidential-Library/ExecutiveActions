"""Assemble data/documents.jsonl — one record per executive action — from the parsed sources.

Inputs
  data/base.jsonl                       catalog rows (parse_sources.py)
  data/statutes_proclamations.jsonl     Statutes at Large texts (parse_statutes.py)
  data/proclamation_statutes_map.json   proclamation -> Statutes printing (match_statutes.py)
  data/wikisource_eo.jsonl              Wikisource EO transcriptions (parse_wikisource.py)
  data/enrich/*.jsonl                   Library-written summary, categories, places per document (worker output)
  data/stories/NNN.md (+ texts/NNN.json) public stories and collated texts (worker output)
  data/corrections.json                 date/title corrections established by the research

Output
  data/documents.jsonl, data/documents.csv, data/stories.json, data/stats.json
"""
import csv
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
APP = "https://www.presidency.ucsb.edu/documents/"
GOVINFO_PAGE = "https://www.govinfo.gov/content/pkg/STATUTE-{v}/pdf/STATUTE-{v}-Pg{p}.pdf"
DAYBYDAY = "https://daybyday.labs.trlibrary.com/day.html?date={d}"

STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida",
          "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
          "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
          "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
          "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
          "West Virginia", "Wisconsin", "Wyoming", "Indian Territory", "Puerto Rico", "Porto Rico", "Philippine", "Philippines",
          "Guam", "Samoa", "Midway", "Panama", "Canal Zone", "Cuba", "District of Columbia"]
STATE_NORM = {"Porto Rico": "Puerto Rico", "Philippine": "Philippines", "Panama": "Panama Canal Zone", "Canal Zone": "Panama Canal Zone"}
ABBR = {"Ariz.": "Arizona", "Calif.": "California", "Colo.": "Colorado", "Fla.": "Florida", "Mont.": "Montana", "Nebr.": "Nebraska",
        "Nev.": "Nevada", "N. Mex.": "New Mexico", "N.M.": "New Mexico", "N. Dak.": "North Dakota", "S. Dak.": "South Dakota",
        "Okla.": "Oklahoma", "Oreg.": "Oregon", "Ore.": "Oregon", "Wash.": "Washington", "Wyo.": "Wyoming", "Mo.": "Missouri",
        "Minn.": "Minnesota", "Mich.": "Michigan", "Wis.": "Wisconsin", "La.": "Louisiana", "Ark.": "Arkansas", "Ida.": "Idaho",
        "Kans.": "Kansas", "Tex.": "Texas", "Miss.": "Mississippi", "Ala.": "Alabama", "Cal.": "California"}

CATEGORY_RULES = [
    ("forests", r"forest reserve|national forest|forest\b"),
    ("monuments", r"national monument"),
    ("wildlife", r"bird|game preserve|wildlife|bison|fish hatcher|reservation for the protection of native birds|breeding ground"),
    ("indian-lands", r"indian|reservation lands|allot|ceded|sioux|ute|uinta|creek|kiowa|comanche|apache|crow\b|cheyenne|chippewa|pueblo|navajo|shoshone|osage|agency"),
    ("public-lands", r"public domain|withdraw|restor|townsite|town site|land district|land office|public lands|homestead|entry|reserving lands|reservation of lands|cemetery|park\b"),
    ("water-reclamation", r"reclamation|reservoir|irrigation|water power|power site|powersite"),
    ("coal-minerals", r"coal|mineral|oil|phosphate|petroleum"),
    ("military-naval", r"military|naval|navy|army|marine|fort\b|target|rifle range|signal corps|coaling station|war department"),
    ("lighthouses", r"light-house|lighthouse|light house|light station"),
    ("civil-service", r"civil service|without examination|classif|competitive|examination|reinstate|appointment|appoint|transfer of|eligib|schedule a|schedule b"),
    ("canal-zone", r"canal|isthmian|panama"),
    ("insular-territories", r"philippine|porto rico|puerto rico|hawaii|alaska|guam|samoa|tutuila|midway|cuba"),
    ("foreign-affairs", r"consul|diplomat|passport|neutral|embargo|export of arms|legation|treaty|foreign"),
    ("trade-reciprocity", r"reciproc|tariff|duties|commercial arrangement|tonnage"),
    ("copyright", r"copyright"),
    ("ceremonial", r"thanksgiving|death of|mourning|half-mast|anniversary|celebration|exposition|holiday|memorial|earthquake|relief|funeral"),
    ("congress", r"convening|extraordinary session|special session|senate"),
    ("statehood", r"admission of|statehood|as a state"),
    ("government-administration", r"department|commission|bureau|records|printing|spelling|employees|officers|salar|pay\b|compensation|leave|holiday"),
]
ACTION_RULES = [
    ("establish", r"^(establish|setting apart|set apart|setting aside|creating|creation|reserving|reservation of|withdraw)"),
    ("enlarge", r"enlarg|adding|addition|extend"),
    ("reduce", r"reduc|diminish|diminution|eliminat|exclud"),
    ("modify", r"modif|boundar|amend|changing|change"),
    ("revoke", r"revok|revocation|abolish|discontinu|restor|vacat"),
    ("transfer", r"transfer|consolidat|merg|combin"),
    ("open", r"opening|open"),
    ("appoint", r"appoint|without examination|reinstat|classification of|authorizing.*(clerk|employment|position)"),
    ("announce", r"announc|thanksgiving|death|proclaim"),
]


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")] if Path(p).exists() else []


def states_in(text):
    found = []
    for a, full in ABBR.items():
        if re.search(r"(?<![A-Za-z])" + re.escape(a), text):
            found.append(full)
    for s in STATES:
        if re.search(r"\b" + re.escape(s) + r"\b", text):
            found.append(STATE_NORM.get(s, s))
    # "Washington" as a city (Done at the City of Washington) is not the state
    out = []
    for f in found:
        if f not in out:
            out.append(f)
    return out


def countersign(signatures):
    if not signatures or len(signatures) < 2:
        return None, None
    rest = " ".join(signatures[1:])
    rest = re.sub(r"(?i)by the president\s*:?", "", rest).strip()
    m = re.match(r"(.*?)[,\s]+((?:Acting\s+)?Secretary of State|Acting Secretary)\.?\s*$", rest)
    name, role = (m.group(1), m.group(2)) if m else (rest, None)
    name = re.sub(r"\s+", " ", name).strip(" .,")
    name = re.sub(r"^Francis B\.? Loomis$|^F\. B\.? Loomis$", "Francis B. Loomis", name)
    name = re.sub(r"^John Hay.*", "John Hay", name)
    return (name or None), role


def parse_heading_docs(heading):
    ids = []
    m = re.search(r"Proclamations? ([0-9][0-9 ,–\-andof()A-Za-záé]*)$", heading)
    if m:
        part = re.sub(r"\([^)]*\)", "", m.group(1))
        for a, b in re.findall(r"(\d{3})–(\d{3})", part):
            ids += [f"proc-{n}" for n in range(int(a), int(b) + 1)]
        part = re.sub(r"\d{3}–\d{3}", "", part)
        ids += [f"proc-{n}" for n in re.findall(r"\d{3}", part)]
    m = re.search(r".*Executive Orders? ([0-9].*)$", heading)
    if m:
        ids.append(("EO", m.group(1)))
    m = re.search(r"Lord catalog nos\. (\d+)–(\d+)", heading)
    if m:
        ids += [f"uo-{n:03d}" for n in range(int(m.group(1)), int(m.group(2)) + 1)]
    return ids


def entry_links(base):
    """Map document ids to research entry numbers using the entry headings."""
    text = (ROOT / "private/TR_Executive_Actions_Research.md").read_text(encoding="utf-8") if (ROOT / "private/TR_Executive_Actions_Research.md").exists() else ""
    eo_order = [b for b in base if b["type"] == "executive_order"]
    eo_index = {b["number"]: i for i, b in enumerate(eo_order)}
    links = defaultdict(list)
    for m in re.finditer(r"^#{2,4}\s*(\d{1,3})\.\s*(.*)$", text, re.M):
        n, h = int(m.group(1)), m.group(2)
        for x in parse_heading_docs(h):
            if isinstance(x, tuple):
                spec = x[1].replace("and", ",")
                for piece in spec.split(","):
                    piece = piece.strip()
                    r = re.match(r"([0-9]+(?:[-–][A-Z]|½)?)\s*–\s*([0-9]+(?:[-–][A-Z]|½)?)$", piece)
                    if r:
                        a, b = r.group(1).replace("–", "-"), r.group(2).replace("–", "-")
                        if a in eo_index and b in eo_index:
                            for doc in eo_order[eo_index[a]:eo_index[b] + 1]:
                                links[doc["id"]].append(n)
                    elif piece.replace("–", "-") in eo_index:
                        links[eo_order[eo_index[piece.replace("–", "-")]]["id"]].append(n)
            else:
                links[x].append(n)
    return links


def main():
    base = load_jsonl(DATA / "base.jsonl")
    st = load_jsonl(DATA / "statutes_proclamations.jsonl")
    smap = json.load(open(DATA / "proclamation_statutes_map.json"))
    ws = {r["id"]: r for r in load_jsonl(DATA / "wikisource_eo.jsonl")}
    corrections = {k: v for k, v in json.load(open(DATA / "corrections.json")).items() if not k.startswith("_")} if (DATA / "corrections.json").exists() else {}
    enrich = {}
    for f in sorted(glob.glob(str(DATA / "enrich/*.jsonl"))):
        for r in load_jsonl(f):
            enrich[r["id"]] = r
    collated = {}
    for f in sorted(glob.glob(str(DATA / "stories/texts/*.json"))):
        n = int(Path(f).stem)
        for k, v in json.load(open(f, encoding="utf-8")).items():
            collated[k] = {**v, "story": n}
    stories = {}
    for f in sorted(glob.glob(str(DATA / "stories/*.md"))):
        raw = Path(f).read_text(encoding="utf-8")
        fm = re.match(r"^---\n(.*?)\n---\n", raw, flags=re.S)
        meta = {}
        if fm:
            for line in fm.group(1).splitlines():
                mm = re.match(r"^(\w+):\s*(.*)$", line)
                if mm:
                    meta[mm.group(1)] = mm.group(2)
        n = int(Path(f).stem)
        docs = re.findall(r"[a-z]+-[0-9a-z\-]+", meta.get("documents", ""))
        stories[n] = {"number": n, "slug": meta.get("slug", "").strip(), "title": meta.get("title", "").strip().strip('"'), "documents": docs}
    links = entry_links(base)
    for n, s in stories.items():
        for d in s["documents"]:
            if n not in links[d]:
                links[d].append(n)

    docs = []
    for b in base:
        r = {k: b.get(k) for k in ("id", "type", "number", "tr_sequence", "lord_number", "date", "date_precision", "title", "title_source")}
        r["date_precision"] = r.get("date_precision") or ("day" if r["date"] and len(r["date"]) == 10 else None)
        r["date_notes"] = []
        r["citations"] = {}
        r["text"] = None
        if b["type"] == "proclamation":
            r["citations"]["app"] = {"number": int(b["number"]), "url": APP + "proclamation-" + b["number"]}
            m = smap.get(b["id"])
            if m:
                s = st[m["_i"]]
                r["citations"]["statutes"] = {"volume": s["volume"], "page": s["page"], "last_page": s["last_page"],
                                              "cite": f"{s['volume']} Stat. {s['page']}" + (f"–{s['last_page']}" if s['last_page'] and s['last_page'] != s['page'] else ""),
                                              "page_image": GOVINFO_PAGE.format(v=s["volume"], p=s["page"]),
                                              "statutes_date": s["date"], "table_title": m.get("list_title")}
                if s["date"] != b["date"]:
                    r["date_notes"].append(f"The American Presidency Project dates this {b['date']}; the Statutes at Large print it under {s['date']}.")
                name, role = countersign(s["signatures"])
                r["signed_as"] = s["signatures"][0] if s["signatures"] else None
                r["countersigned_by"] = {"name": name, "role": role} if name else None
                r["text"] = {"paragraphs": s["paragraphs"], "source": f"Statutes at Large, {s['volume']} Stat. {s['page']}",
                             "kind": "statutes_digitization", "verified": False,
                             "note": "GovInfo digitization of the printed Statutes at Large; not proofread. Check the page image before quoting.",
                             "marginal_notes": s["marginal_notes"]}
        elif b["type"] == "executive_order":
            w = ws.get(b["id"])
            if w:
                r["citations"]["wikisource"] = {"url": w["url"], "revid": w["revid"], "printed_source": w["cite"]}
                if w["date"] and w["date"] != b["date"]:
                    r["date_notes"].append(f"Wikisource dates this order {w['date']}; the Wikipedia list gives {b['date']}.")
                if w["paragraphs"] and not w["not_located"]:
                    r["text"] = {"paragraphs": w["paragraphs"], "source": "Wikisource" + (f" (from {w['cite']})" if w["cite"] else ""),
                                 "kind": "wikisource_transcription", "verified": False, "signed": w["signed"], "place_date": w["place_date"],
                                 "note": "Volunteer transcription of a printed compilation; not verified against the original."}
        else:
            r["citations"]["lord"] = {"number": b["lord_number"], "page": b["lord_page"], "citations": b["lord_citations"]}
            r["lord_description"] = b["lord_description"]
            r["reconciliation"] = b["reconciliation"]
            r["duplicate_of"] = b["duplicate_of"]
            r["reconciliation_note"] = b["reconciliation_note"]
            if b.get("date_inferred_by_lord"):
                r["date_notes"].append("Lord printed this date in brackets: his own inference.")
        if b["id"] in collated:
            c = collated[b["id"]]
            r["text"] = {"paragraphs": c["paragraphs"], "source": c.get("collated_against"), "kind": "collated", "verified": True,
                         "note": c.get("notes"), "story": c["story"]}
        c = corrections.get(b["id"], {})
        for k in ("date", "title"):
            if k in c:
                notes = "date_notes" if k == "date" else "title_notes"
                r[notes] = r.get(notes, []) + [f"Corrected from \u201c{r[k]}\u201d. {c.get('why', '')}".strip()]
                r[k] = c[k]
                if k == "title":
                    r["title_source"] = "Corrected by the Library (see title note)"
        if "date" in c:
            r["date_precision"] = "day" if len(c["date"]) == 10 else r["date_precision"]
            if c["date"] == (r["citations"].get("statutes") or {}).get("statutes_date"):
                r["date_notes"] = [n for n in r["date_notes"] if not n.startswith("The American Presidency Project dates this")]
        if "date_note" in c:
            r["date_notes"].append(c["date_note"])
        if "title_note" in c:
            r["title_notes"] = r.get("title_notes", []) + [c["title_note"]]
        e = enrich.get(b["id"], {})
        hay = " ".join([r["title"] or "", " ".join((r["text"] or {}).get("paragraphs", [])[:3])])
        r["summary"] = e.get("summary")
        r["categories"] = e.get("categories") or [c for c, rx in CATEGORY_RULES if re.search(rx, (r["title"] or "").lower())]
        r["action"] = e.get("action") or next((a for a, rx in ACTION_RULES if re.search(rx, (r["title"] or "").lower())), None)
        r["places"] = e.get("places") or []
        r["states"] = e.get("states") or states_in(r["title"] or "") or states_in(hay)
        r["people"] = e.get("people") or []
        r["significance"] = e.get("significance")
        for k in ("summary", "states", "people", "action"):
            if k in c:
                r[k] = c[k]
        r["stories"] = sorted(set(links.get(b["id"], [])))
        r["day_by_day"] = DAYBYDAY.format(d=r["date"]) if r["date"] and len(r["date"]) == 10 else None
        docs.append(r)

    # Statutes proclamations that are not in the APP numbering
    used = {v["_i"] for v in smap.values()}
    extra = 0
    for i, s in enumerate(st):
        if i in used:
            continue
        extra += 1
        title = (s.get("list_titles") or [""])[0].rstrip(".") or "Untitled proclamation"
        name, role = countersign(s["signatures"])
        pid = f"proc-x-{s['date']}"
        e = enrich.get(pid, {})
        docs.append({"id": pid, "type": "proclamation", "number": None, "date": s["date"], "date_precision": "day",
                     "title": title, "title_source": "Statutes at Large, list of proclamations", "date_notes": [],
                     "numbering_note": "Printed in the Statutes at Large as a proclamation signed by Roosevelt, but not among the American Presidency Project's numbered Proclamations 465–871. Unverified: needs checking against the State Department's proclamation register.",
                     "citations": {"statutes": {"volume": s["volume"], "page": s["page"], "last_page": s["last_page"],
                                                "cite": f"{s['volume']} Stat. {s['page']}", "page_image": GOVINFO_PAGE.format(v=s["volume"], p=s["page"]), "statutes_date": s["date"]}},
                     "signed_as": s["signatures"][0] if s["signatures"] else None,
                     "countersigned_by": {"name": name, "role": role} if name else None,
                     "text": {"paragraphs": s["paragraphs"], "source": f"Statutes at Large, {s['volume']} Stat. {s['page']}", "kind": "statutes_digitization", "verified": False,
                              "note": "GovInfo digitization; not proofread.", "marginal_notes": s["marginal_notes"]},
                     "summary": e.get("summary"), "categories": e.get("categories") or ["trade-reciprocity", "foreign-affairs"], "action": e.get("action") or "announce",
                     "places": e.get("places") or [], "states": [], "people": [], "significance": e.get("significance"), "stories": [],
                     "day_by_day": DAYBYDAY.format(d=s["date"])})

    docs.sort(key=lambda d: (d["date"] or "9999", {"proclamation": 0, "executive_order": 1, "unnumbered_order": 2}[d["type"]], d["id"]))
    with open(DATA / "documents.jsonl", "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    with open(DATA / "documents.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "number", "date", "title", "categories", "action", "states", "statutes_cite", "countersigned_by", "stories", "duplicate_of", "text_source", "summary"])
        for d in docs:
            w.writerow([d["id"], d["type"], d["number"] or "", d["date"] or "", d["title"], ";".join(d["categories"]), d["action"] or "",
                        ";".join(d["states"]), (d["citations"].get("statutes") or {}).get("cite", ""), ((d.get("countersigned_by") or {}).get("name") or ""),
                        ";".join(map(str, d["stories"])), d.get("duplicate_of") or "", ((d["text"] or {}).get("kind") or ""), d.get("summary") or ""])
    json.dump(stories, open(DATA / "stories.json", "w"), ensure_ascii=False, indent=0)
    distinct = [d for d in docs if not d.get("duplicate_of")]
    stats = {"documents": len(docs), "distinct_documents": len(distinct),
             "by_type": Counter(d["type"] for d in distinct), "extra_statutes_proclamations": extra,
             "with_text": sum(1 for d in distinct if d["text"]), "text_kinds": Counter((d["text"] or {}).get("kind") for d in distinct),
             "categories": Counter(c for d in distinct for c in d["categories"]),
             "uncategorized": sum(1 for d in distinct if not d["categories"]),
             "with_story": sum(1 for d in distinct if d["stories"]), "with_summary": sum(1 for d in distinct if d["summary"])}
    json.dump(stats, open(DATA / "stats.json", "w"), indent=1, default=dict)
    print(json.dumps(stats, indent=1, default=dict))


if __name__ == "__main__":
    main()
