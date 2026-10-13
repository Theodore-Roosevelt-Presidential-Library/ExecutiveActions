"""Build the static JSON API for Executive Actions into site/api/v1 (served by GitHub Pages).

Endpoints (all GET, all JSON, CORS-open on GitHub Pages):
  /api/v1/index.json                       dataset metadata, counts, endpoint list
  /api/v1/documents.json                   compact list of every document (for the index page)
  /api/v1/documents/{id}.json              one full record + story titles + previous/next by date
  /api/v1/years/{YYYY}.json                documents signed in a year
  /api/v1/categories/index.json            categories with counts
  /api/v1/categories/{slug}.json           documents in a category
  /api/v1/states/index.json                states and territories with counts
  /api/v1/states/{slug}.json               documents acting on a state or territory
  /api/v1/types/{type}.json                executive_order | proclamation | unnumbered_order
  /api/v1/stories/index.json               every published story (meta)
  /api/v1/stories/{number}.json            one story: meta + Markdown + rendered HTML
  /api/v1/stories/{slug}.json              the same story, by slug
  /api/v1/on-this-day/{MM-DD}.json         documents signed on that calendar date, most significant first
  /api/v1/countersigners.json              who countersigned, in what role, how often
  /api/v1/search.json                      id, title, summary, date, type for client-side search
Bulk downloads are copied to /data/.

Lord's unnumbered entries that duplicate a numbered order (duplicate_of set) are kept as
cross-references: they get their own document file but are left out of counts, lists,
years, categories, states, on-this-day and previous/next.

Usage: python pipeline/build_api.py [--stories DIR]   (stdlib only)
"""
import argparse
import html
import json
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "site/api/v1"
BASE_URL = "https://executiveactions.labs.trlibrary.com"

TYPE_LABEL = {"executive_order": "Executive order", "proclamation": "Proclamation", "unnumbered_order": "Unnumbered order"}
TYPE_SLUG = {"executive_order": "executive-orders", "proclamation": "proclamations", "unnumbered_order": "unnumbered-orders"}

CATEGORIES = [
    ("forests", "Forests"), ("monuments", "National monuments"), ("wildlife", "Wildlife and bird reservations"),
    ("public-lands", "Public lands"), ("indian-lands", "Indian lands"), ("water-reclamation", "Water and reclamation"),
    ("coal-minerals", "Coal and minerals"), ("conservation-policy", "Conservation policy"),
    ("military-naval", "Military and naval"), ("lighthouses", "Lighthouses"), ("civil-service", "Civil service"),
    ("government-administration", "Government administration"), ("canal-zone", "Panama Canal Zone"),
    ("insular-territories", "Island territories"), ("foreign-affairs", "Foreign affairs"),
    ("trade-reciprocity", "Trade and reciprocity"), ("copyright", "Copyright"), ("ceremonial", "Ceremonial"),
    ("congress", "Congress"), ("statehood", "Statehood"), ("labor-business", "Labor and business"),
]
CAT_LABEL = dict(CATEGORIES)
# Broad groups used to color the timeline. Every category maps to one group.
GROUPS = [
    ("land", "Forests, parks and public land", ["forests", "monuments", "wildlife", "public-lands", "water-reclamation",
                                                "coal-minerals", "conservation-policy"]),
    ("indian", "Indian lands", ["indian-lands"]),
    ("civil", "Civil service", ["civil-service"]),
    ("gov", "Running the government", ["government-administration", "congress", "copyright", "ceremonial",
                                       "statehood", "labor-business"]),
    ("military", "Army, Navy and lighthouses", ["military-naval", "lighthouses"]),
    ("territories", "Canal Zone and island territories", ["canal-zone", "insular-territories"]),
    ("foreign", "Foreign affairs and trade", ["foreign-affairs", "trade-reciprocity"]),
    ("other", "Not yet sorted", []),
]
GROUP_OF = {c: g for g, _, cs in GROUPS for c in cs}
ACTION_LABEL = {"amend-rules": "amend rules"}
SIG_LABEL = {1: "Individual action", 2: "Routine", 3: "Substantive", 4: "Notable", 5: "Landmark"}

COMPACT_FIELDS = ["id", "type", "number", "date", "title", "summary", "categories", "action", "states",
                  "significance", "stories", "has_text"]


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def load_jsonl(p):
    out = []
    if not p.exists():
        return out
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"  skipped a malformed line in {p.name}")
    return out


def num_key(n):
    """Sort '310-A', '288-half', '302a' after 310 / 288 / 302."""
    m = re.match(r"(\d+)(.*)", str(n or ""))
    return (int(m.group(1)), m.group(2).lower()) if m else (10 ** 6, str(n or ""))


TYPE_ORDER = {"proclamation": 0, "executive_order": 1, "unnumbered_order": 2}


def date_key(r):
    d = r.get("date") or ""
    if len(d) == 7:
        d += "-00"
    return (d or "9999-99-99", TYPE_ORDER.get(r.get("type"), 3), num_key(r.get("number") or r.get("lord_number")))


def doc_label(r):
    t, n = r.get("type"), r.get("number")
    if t == "executive_order":
        return f"Executive Order {n}" if n else "Executive order"
    if t == "proclamation":
        return f"Proclamation {n}" if n else "Proclamation (not in the numbered series)"
    ln = r.get("lord_number")
    return f"Unnumbered order (Lord no. {ln})" if ln else "Unnumbered order"


TODAY_KIND = {"national_park": "National parks", "national_monument": "National monuments", "national_forest": "National forests",
              "national_grassland": "National grasslands", "wildlife_refuge": "Wildlife refuges", "state_park": "State parks",
              "indian_reservation": "Reservations and tribal lands", "military_installation": "Military installations",
              "lighthouse": "Lighthouses", "other": "Other places and institutions"}
TODAY_REL = {"origin": "began with this document", "part": "includes land from this document", "renamed": "renamed from it",
             "absorbed_into": "absorbed into it", "abolished": "no longer exists", "transferred": "transferred to it"}


PLACE_ALIASES = {"Grand Canyon Game Preserve": "Grand Canyon National Game Preserve",
                 "Lewis and Clark National Forest": "Helena–Lewis and Clark National Forest",
                 "Shasta National Forest": "Shasta-Trinity National Forest",
                 "Wallowa–Whitman National Forest": "Wallowa-Whitman National Forest"}
# Present-day institutions and abstractions: kept on document pages, left out of the then-and-now list of places.
NOT_PLACES = {'"USS" ship prefix of the U.S. Navy', "Tsinghua University", "U.S. Commission of Fine Arts", "U.S. Board on Geographic Names",
              "United States Geographic Board", "Library of Congress Manuscript Division", "Bureau of Insular Affairs",
              "National Archives Record Group 360 (Records of the Continental and Confederation Congresses)",
              "U.S. Coast Guard aids to navigation in Hawaii", "State of Oklahoma", "National Wildlife Refuge System"}


def canon_place(name):
    """'Caribou-Targhee National Forest (Westside Ranger District)' -> ('Caribou-Targhee National Forest', 'Westside Ranger District')."""
    name = re.sub(r"\s+", " ", name.strip())
    m = re.match(r"^(Alaska Maritime National Wildlife Refuge)\s*\((.*)\)$", name)
    if m:
        return m.group(1), m.group(2)[0].upper() + m.group(2)[1:].replace(" unit", " Unit")
    m = re.match(r"^(.*?)\s*\((.*Ranger District)\)$", name) or re.match(r"^(.*National Forests?),\s*(.*Ranger District)$", name)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    m = re.match(r"^(.*Ranger District),\s*(.*National Forests?)$", name)
    if m:
        return m.group(2).strip(), m.group(1).strip()
    return name, None


def has_text(r):
    return bool((r.get("text") or {}).get("paragraphs"))


def compact(r):
    c = {k: r.get(k) for k in COMPACT_FIELDS}
    c["summary"] = r.get("summary") or None
    c["categories"] = r.get("categories") or []
    c["states"] = r.get("states") or []
    c["stories"] = r.get("stories") or []
    c["has_text"] = has_text(r)
    c["has_impact"] = bool(r.get("impact"))
    c["today"] = sorted({t["name"] for t in (r.get("impact") or {}).get("today", []) if t.get("name")})
    c["label"] = doc_label(r)
    if r.get("duplicate_of"):
        c["duplicate_of"] = r["duplicate_of"]
    return c


# ---------------------------------------------------------------- Markdown

def _inline(s, base_url):
    """Escape, then apply code, links, bold and italic."""
    codes = []

    def keep_code(m):
        codes.append(f"<code>{html.escape(m.group(1), quote=False)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", keep_code, s)
    s = html.escape(s, quote=False)
    links = []

    def link(m):
        text, href = m.group(1), html.unescape(m.group(2)).strip()
        sm = re.fullmatch(r"story:\s*0*(\d+)", href)
        dm = re.fullmatch(r"doc:\s*([a-z]+-[0-9a-z\-]+)", href)
        if sm:
            url, cls = f"{base_url}/story.html?n={int(sm.group(1))}", "story-link"
        elif dm:
            url, cls = f"{base_url}/document.html?id={dm.group(1)}", "doc-link"
        elif re.match(r"^(https?:|mailto:|/|#)", href):
            url, cls = href, ""
        else:
            return text
        links.append(f'<a href="{html.escape(url)}"{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}>{text}</a>')
        return f"\x01{len(links) - 1}\x01"

    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"__(.+?)__", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<em>\1</em>", s)
    s = re.sub(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])", r"<em>\1</em>", s)
    s = re.sub(r"\x01(\d+)\x01", lambda m: links[int(m.group(1))], s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)
    return s


def md_to_html(md, base_url=BASE_URL):
    """Small Markdown converter: headings, paragraphs, lists (one level), bold/italic, links
    (incl. story:NN and doc:ID), blockquotes, horizontal rules."""
    lines = md.replace("\r\n", "\n").split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + _inline(" ".join(x.strip() for x in para), base_url) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        st = line.strip()
        if not st:
            flush()
            i += 1
            continue
        h = re.match(r"^(#{1,6})\s+(.*?)\s*#*$", st)
        if h:
            flush()
            lvl = min(6, len(h.group(1)) + 1)  # page owns <h1>; story ## becomes <h3>
            lvl = max(2, lvl)
            out.append(f'<h{lvl} id="{slugify(h.group(2))}">{_inline(h.group(2), base_url)}</h{lvl}>')
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})$", st):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if st.startswith(">"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                block.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + md_to_html("\n".join(block), base_url) + "</blockquote>")
            continue
        lm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if lm:
            flush()
            ordered = lm.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                m2 = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
                if m2 and (m2.group(2)[0].isdigit()) == ordered:
                    items.append(m2.group(3))
                elif lines[i].strip() and lines[i].startswith((" ", "\t")) and items:
                    items[-1] += " " + lines[i].strip()  # continuation or nested line, flattened
                else:
                    break
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x, base_url)}</li>" for x in items) + f"</{tag}>")
            continue
        para.append(line)
        i += 1
    flush()
    return "\n".join(out)


def md_inline_plain(s):
    """Markdown inline -> HTML for short notes (no block structure)."""
    return _inline(s or "", BASE_URL)


# ---------------------------------------------------------------- stories

def parse_front_matter(raw):
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*\n?(.*)$", raw, flags=re.S)
    if not m:
        return {}, raw
    meta, key = {}, None
    for line in m.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", line)
        if item and key:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(_scalar(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not kv:
            continue
        key, val = kv.group(1), _strip_comment(kv.group(2)).strip()
        if val.startswith("["):
            meta[key] = _flow_list(val)
        elif val == "":
            meta[key] = []
        else:
            meta[key] = _scalar(val)
    return meta, m.group(2)


def _strip_comment(v):
    out, q = [], None
    for idx, ch in enumerate(v):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch == "#" and (idx == 0 or v[idx - 1].isspace()):
            break
        out.append(ch)
    return "".join(out)


def _scalar(v):
    v = _strip_comment(v).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
        if '\\"' in v:
            v = v.replace('\\"', '"')
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _flow_list(v):
    v = v.strip()
    if v.startswith("["):
        v = v[1:]
    if v.endswith("]"):
        v = v[:-1]
    items, cur, q = [], "", None
    for ch in v:
        if q:
            cur += ch
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur += ch
        elif ch == ",":
            items.append(cur)
            cur = ""
        else:
            cur += ch
    items.append(cur)
    return [_scalar(x) for x in items if x.strip()]


def load_stories(story_dir):
    stories = {}
    for f in sorted(Path(story_dir).glob("*.md")):
        if not re.fullmatch(r"\d+", f.stem):
            continue
        try:
            raw = f.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, body = parse_front_matter(raw)
        n = int(meta.get("number") or int(f.stem))
        listify = lambda v: v if isinstance(v, list) else ([v] if v not in (None, "") else [])
        s = {
            "number": n,
            "slug": str(meta.get("slug") or f"story-{n}").strip(),
            "title": str(meta.get("title") or f"Story {n}").strip(),
            "dek": str(meta.get("dek") or "").strip() or None,
            "documents": [str(x) for x in listify(meta.get("documents"))],
            "related_documents": [str(x) for x in listify(meta.get("related_documents"))],
            "date_start": str(meta["date_start"]) if meta.get("date_start") else None,
            "date_end": str(meta["date_end"]) if meta.get("date_end") else None,
            "themes": [str(x) for x in listify(meta.get("themes"))],
            "places": [str(x) for x in listify(meta.get("places"))],
            "open_questions": [str(x) for x in listify(meta.get("open_questions"))],
            "markdown": body.strip(),
        }
        stories[n] = s
    return stories


# ---------------------------------------------------------------- build

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stories", default=str(DATA / "stories"), help="folder of NNN.md story files")
    args = ap.parse_args()

    if OUT.exists():
        shutil.rmtree(OUT)
    docs = load_jsonl(DATA / "documents.jsonl")
    if not docs:
        raise SystemExit("data/documents.jsonl is missing or empty")
    stats = json.load(open(DATA / "stats.json", encoding="utf-8")) if (DATA / "stats.json").exists() else {}
    stories = load_stories(args.stories)
    by_id = {r["id"]: r for r in docs}

    distinct = sorted((r for r in docs if not r.get("duplicate_of")), key=date_key)
    duplicates = [r for r in docs if r.get("duplicate_of")]
    dupes_of = defaultdict(list)
    for r in duplicates:
        dupes_of[r["duplicate_of"]].append(r)

    # Story membership: union of document records' story lists and story files' document lists.
    story_docs = defaultdict(set)
    for r in docs:
        for n in r.get("stories") or []:
            story_docs[n].add(r["id"])
    for n, s in stories.items():
        for d in s["documents"]:
            if d in by_id:
                story_docs[n].add(d)
                if n not in (by_id[d].get("stories") or []):
                    by_id[d]["stories"] = sorted(set((by_id[d].get("stories") or []) + [n]))

    def story_ref(n):
        s = stories.get(n)
        if not s:
            return None
        return {"number": n, "slug": s["slug"], "title": s["title"], "dek": s["dek"],
                "url": f"{BASE_URL}/story.html?n={n}"}

    order = {r["id"]: i for i, r in enumerate(distinct)}

    def mini(r):
        return {"id": r["id"], "label": doc_label(r), "date": r.get("date"), "title": r.get("title")} if r else None

    # --- documents
    for r in docs:
        full = dict(r)
        full["label"] = doc_label(r)
        full["type_label"] = TYPE_LABEL.get(r.get("type"), r.get("type"))
        full["has_text"] = has_text(r)
        full["category_labels"] = [{"slug": c, "label": CAT_LABEL.get(c, c)} for c in r.get("categories") or []]
        full["state_refs"] = [{"name": s, "slug": slugify(s)} for s in r.get("states") or []]
        full["story_refs"] = [x for x in (story_ref(n) for n in r.get("stories") or []) if x]
        full["significance_label"] = SIG_LABEL.get(r.get("significance"))
        if r.get("duplicate_of"):
            full["duplicate_of_ref"] = mini(by_id.get(r["duplicate_of"]))
            i = order.get(r["duplicate_of"])
        else:
            full["duplicates"] = [mini(x) for x in dupes_of.get(r["id"], [])]
            i = order.get(r["id"])
        full["prev"] = mini(distinct[i - 1]) if i is not None and i > 0 else None
        full["next"] = mini(distinct[i + 1]) if i is not None and i + 1 < len(distinct) else None
        full["url"] = f"{BASE_URL}/document.html?id={r['id']}"
        full["related"] = [{**x, "label": doc_label(by_id[x["id"]])} for x in r.get("related") or [] if x["id"] in by_id]
        full["reconciliation_note_html"] = md_inline_plain(r["reconciliation_note"]) if r.get("reconciliation_note") else None
        dump(OUT / f"documents/{r['id']}.json", full)

    compact_all = [compact(r) for r in distinct] + [compact(r) for r in sorted(duplicates, key=date_key)]
    dump(OUT / "documents.json", compact_all)

    # --- groupings (distinct documents only)
    by_year, by_cat, by_state, by_type, by_md = (defaultdict(list) for _ in range(5))
    for r in distinct:
        c = compact(r)
        if r.get("date"):
            by_year[r["date"][:4]].append(c)
        for cat in r.get("categories") or []:
            by_cat[cat].append(c)
        for s in r.get("states") or []:
            by_state[s].append(c)
        by_type[r["type"]].append(c)
        if r.get("date") and len(r["date"]) == 10:
            by_md[r["date"][5:]].append(c)
    for y, v in by_year.items():
        dump(OUT / f"years/{y}.json", {"year": int(y), "count": len(v), "documents": v})
    cat_index = []
    for slug in sorted(by_cat, key=lambda s: -len(by_cat[s])):
        v = by_cat[slug]
        dump(OUT / f"categories/{slug}.json", {"slug": slug, "label": CAT_LABEL.get(slug, slug),
                                               "group": GROUP_OF.get(slug, "other"), "count": len(v), "documents": v})
        cat_index.append({"slug": slug, "label": CAT_LABEL.get(slug, slug), "group": GROUP_OF.get(slug, "other"),
                          "count": len(v), "primary": sum(1 for x in v if x["categories"][0] == slug)})
    dump(OUT / "categories/index.json", cat_index)
    state_index = []
    for name in sorted(by_state):
        v = by_state[name]
        dump(OUT / f"states/{slugify(name)}.json", {"name": name, "slug": slugify(name), "count": len(v), "documents": v})
        state_index.append({"name": name, "slug": slugify(name), "count": len(v)})
    dump(OUT / "states/index.json", state_index)
    for t, v in by_type.items():
        dump(OUT / f"types/{t}.json", {"type": t, "label": TYPE_LABEL.get(t, t), "count": len(v), "documents": v})
    # every calendar date gets a file, so widgets never hit a 404
    for m in range(1, 13):
        for d in range(1, 32):
            if (m, d) in ((2, 30), (2, 31), (4, 31), (6, 31), (9, 31), (11, 31)):
                continue
            md = f"{m:02d}-{d:02d}"
            v = sorted(by_md.get(md, []), key=lambda x: (-(x["significance"] or 0), x["date"], num_key(x["number"])))
            dump(OUT / f"on-this-day/{md}.json", {"month_day": md, "count": len(v), "documents": v})

    # --- countersigners
    cs = defaultdict(lambda: {"roles": Counter(), "documents": []})
    for r in distinct:
        c = r.get("countersigned_by") or {}
        if c.get("name"):
            cs[c["name"]]["roles"][c.get("role") or ""] += 1
            cs[c["name"]]["documents"].append({"id": r["id"], "date": r.get("date"), "label": doc_label(r),
                                               "role": c.get("role")})
    dump(OUT / "countersigners.json", sorted(
        ({"name": k, "count": len(v["documents"]), "roles": [{"role": a, "count": b} for a, b in v["roles"].most_common() if a],
          "first": min((d["date"] for d in v["documents"] if d["date"]), default=None),
          "last": max((d["date"] for d in v["documents"] if d["date"]), default=None),
          "documents": v["documents"]} for k, v in cs.items()), key=lambda x: -x["count"]))

    dump(OUT / "search.json", [{"id": r["id"], "title": r.get("title"), "summary": r.get("summary"),
                                "date": r.get("date"), "type": r.get("type"), "label": doc_label(r)} for r in distinct])

    # --- stories
    story_impact = json.load(open(DATA / "story_impact.json", encoding="utf-8")) if (DATA / "story_impact.json").exists() else {}
    story_index = []
    for n in sorted(stories):
        s = stories[n]
        members = [by_id[d] for d in s["documents"] if d in by_id] or \
                  [by_id[d] for d in sorted(story_docs.get(n, [])) if d in by_id and not by_id[d].get("duplicate_of")]
        members = sorted({m["id"]: m for m in members}.values(), key=date_key)
        related = [by_id[d] for d in s["related_documents"] if d in by_id]
        meta = {k: s[k] for k in ("number", "slug", "title", "dek", "date_start", "date_end", "themes", "places")}
        meta["theme_labels"] = [CAT_LABEL.get(t, t.replace("-", " ").capitalize()) for t in s["themes"]]
        meta["document_count"] = len(members)
        meta["open_question_count"] = len(s["open_questions"])
        meta["url"] = f"{BASE_URL}/story.html?n={n}"
        story_index.append(meta)
        full = {**meta, "open_questions": s["open_questions"],
                "documents": [compact(m) for m in members], "related_documents": [compact(m) for m in related],
                "markdown": s["markdown"], "html": md_to_html(s["markdown"]),
                "impact": story_impact.get(str(n)) or None,
                "documents_impact": {m["id"]: m["impact"] for m in members if m.get("impact")}}
        dump(OUT / f"stories/{n}.json", full)
        if s["slug"] and not s["slug"].isdigit():
            dump(OUT / f"stories/{s['slug']}.json", full)
    dump(OUT / "stories/index.json", story_index)

    # --- then and now: present-day places and institutions that trace to a Roosevelt document
    places = {}
    for r in distinct:
        for t in (r.get("impact") or {}).get("today", []):
            if not t.get("name"):
                continue
            if t["name"].strip() in NOT_PLACES:
                continue
            name, district = canon_place(t["name"])
            name = PLACE_ALIASES.get(name, name)
            key = (name.lower().replace("–", "-").replace("—", "-"), t.get("kind") or "other")
            p = places.setdefault(key, {"name": name, "kind": key[1], "kind_label": TODAY_KIND.get(key[1], key[1]),
                                        "slug": slugify(key[0]), "states": set(), "documents": []})
            for st_ in re.split(r",\s*|\s+and\s+", t.get("state") or ""):
                if st_.strip():
                    p["states"].add(st_.strip())
            p["documents"].append({"id": r["id"], "label": doc_label(r), "date": r.get("date"), "title": r.get("title"),
                                   "relation": t.get("relation"), "relation_label": TODAY_REL.get(t.get("relation"), t.get("relation")),
                                   "since": t.get("since"), "district": district, "note": t.get("note"), "source": t.get("source"), "story": t.get("story")})
    then_now = []
    for p in places.values():
        if not p["states"] and p["kind"] != "other":
            p["states"] = {s for d in p["documents"] for s in (by_id[d["id"]].get("states") or [])}
        p["states"] = sorted(p["states"])
        p["documents"].sort(key=lambda d: d["date"] or "9999")
        p["first"] = p["documents"][0]["date"]
        p["origin"] = any(d["relation"] == "origin" for d in p["documents"])
        p["count"] = len(p["documents"])
        then_now.append(p)
    then_now.sort(key=lambda p: (list(TODAY_KIND).index(p["kind"]) if p["kind"] in TODAY_KIND else 99, p["name"]))
    kinds = Counter(p["kind"] for p in then_now)
    dump(OUT / "then-and-now/index.json", {"count": len(then_now),
         "kinds": [{"kind": k, "label": TODAY_KIND.get(k, k), "count": kinds[k]} for k in TODAY_KIND if kinds.get(k)],
         "places": then_now,
         "note": "Present-day places and institutions that the Library's research traces to a Roosevelt order or proclamation. "
                 "Relation says how: origin (the document created it), part (its lands are now part of it), renamed, absorbed into, transferred, or abolished."})
    for k in kinds:
        dump(OUT / f"then-and-now/{k}.json", {"kind": k, "label": TODAY_KIND.get(k, k), "places": [p for p in then_now if p["kind"] == k]})

    # --- meta
    months = Counter(r["date"][:7] for r in distinct if r.get("date"))
    lord = [r for r in docs if r.get("type") == "unnumbered_order"]
    meta = {
        "title": "Theodore Roosevelt's Executive Orders and Proclamations",
        "publisher": "Theodore Roosevelt Presidential Library",
        "url": BASE_URL,
        "api": f"{BASE_URL}/api/v1/",
        "version": "1.0",
        "coverage": {"start": min((r["date"] for r in distinct if r.get("date")), default=None),
                     "end": max((r["date"] for r in distinct if r.get("date")), default=None),
                     "term": {"start": "1901-09-14", "end": "1909-03-04"}},
        "counts": {
            "records": len(docs),
            "documents": len(distinct),
            "lord_duplicates": len(duplicates),
            "by_type": dict(Counter(r["type"] for r in distinct)),
            "numbered_executive_orders": sum(1 for r in distinct if r["type"] == "executive_order"),
            "unnumbered_orders": sum(1 for r in distinct if r["type"] == "unnumbered_order"),
            "lord_entries": len(lord),
            "numbered_proclamations": sum(1 for r in distinct if r["type"] == "proclamation" and r.get("number")),
            "unnumbered_proclamations": sum(1 for r in distinct if r["type"] == "proclamation" and not r.get("number")),
            "with_text": sum(1 for r in distinct if has_text(r)),
            "text_kinds": dict(Counter((r.get("text") or {}).get("kind") for r in distinct if has_text(r))),
            "with_summary": sum(1 for r in distinct if r.get("summary")),
            "with_story": sum(1 for r in distinct if r.get("stories")),
            "uncategorized": sum(1 for r in distinct if not r.get("categories")),
            "undated": sum(1 for r in distinct if not r.get("date")),
            "month_only": sum(1 for r in distinct if r.get("date") and len(r["date"]) == 7),
            "stories": len(stories),
            "countersigners": len(cs),
            "with_impact": sum(1 for r in distinct if r.get("impact")),
            "with_related": sum(1 for r in distinct if r.get("related")),
            "then_and_now_places": len(then_now),
        },
        "by_year": dict(sorted(Counter(r["date"][:4] for r in distinct if r.get("date")).items())),
        "by_month": dict(sorted(months.items())),
        "by_category": {c["slug"]: c["count"] for c in cat_index},
        "categories": [{"slug": s, "label": l, "group": GROUP_OF.get(s, "other")} for s, l in CATEGORIES],
        "groups": [{"id": g, "label": l, "categories": cs_} for g, l, cs_ in GROUPS],
        "significance_labels": SIG_LABEL,
        "dataset_stats": stats,
        "sources": [
            {"name": "The American Presidency Project (UC Santa Barbara)", "use": "Proclamation numbers, dates and titles", "url": "https://www.presidency.ucsb.edu/"},
            {"name": "United States Statutes at Large, vols. 32–35 (GovInfo)", "use": "Printed text and page images of the proclamations", "url": "https://www.govinfo.gov/app/collection/statute"},
            {"name": "Wikisource", "use": "Volunteer transcriptions of numbered executive orders", "url": "https://en.wikisource.org/"},
            {"name": "Wikipedia, List of executive actions by Theodore Roosevelt", "use": "Numbered executive order list, dates and titles", "url": "https://en.wikipedia.org/wiki/List_of_executive_actions_by_Theodore_Roosevelt"},
            {"name": "Clifford L. Lord, ed., List and Index of Presidential Executive Orders: Unnumbered Series, 1789–1941 (1943)", "use": "Unnumbered executive orders"},
        ],
        "text_note": "Texts are machine digitizations of the printed Statutes at Large or volunteer Wikisource transcriptions. "
                     "Each is marked verified:false until collated against the printed page; check the page image before quoting.",
        "license": "Data: CC BY 4.0, Theodore Roosevelt Presidential Library. Code: MIT. Source texts: public domain.",
        "cite_as": "Theodore Roosevelt Presidential Library, Theodore Roosevelt's Executive Orders and Proclamations, "
                   "https://executiveactions.labs.trlibrary.com",
        "endpoints": {
            "documents": "/api/v1/documents.json", "document": "/api/v1/documents/{id}.json",
            "year": "/api/v1/years/{YYYY}.json", "categories": "/api/v1/categories/index.json",
            "category": "/api/v1/categories/{slug}.json", "states": "/api/v1/states/index.json",
            "state": "/api/v1/states/{slug}.json", "type": "/api/v1/types/{executive_order|proclamation|unnumbered_order}.json",
            "stories": "/api/v1/stories/index.json", "story": "/api/v1/stories/{number|slug}.json",
            "on_this_day": "/api/v1/on-this-day/{MM-DD}.json", "countersigners": "/api/v1/countersigners.json",
            "search": "/api/v1/search.json", "then_and_now": "/api/v1/then-and-now/index.json",
            "then_and_now_kind": "/api/v1/then-and-now/{kind}.json"},
        "downloads": ["/data/documents.jsonl", "/data/documents.csv", "/data/stats.json"],
    }
    dump(OUT / "index.json", meta)

    dl = ROOT / "site/data"
    dl.mkdir(parents=True, exist_ok=True)
    for f in ["documents.jsonl", "documents.csv", "stats.json"]:
        if (DATA / f).exists():
            shutil.copy(DATA / f, dl / f)
    n = sum(1 for _ in OUT.rglob("*.json"))
    print(f"API built: {n} files | {len(distinct)} documents, {len(duplicates)} Lord duplicates, {len(stories)} stories")


if __name__ == "__main__":
    main()
