# Theodore Roosevelt's Executive Orders and Proclamations

Every executive order and proclamation Theodore Roosevelt signed as president, from September 14, 1901 to March 4, 1909, as a structured, open dataset with a static JSON API, an explorer site, embeddable widgets and 114 public stories.

**Live:** https://executiveactions.labs.trlibrary.com · **API:** https://executiveactions.labs.trlibrary.com/api/v1/index.json · **Widgets:** https://executiveactions.labs.trlibrary.com/widget.html

| | |
| --- | --- |
| Documents | 1,521 distinct documents (1,542 records, counting 21 cross-references) |
| Executive orders | 1,111: 1,006 numbered (EOs 141–1050, with lettered and half numbers) + 105 distinct unnumbered orders |
| Proclamations | 410: 407 numbered (Nos. 465–871) + 3 printed in the Statutes at Large but outside that numbering |
| Lord's unnumbered list | 126 Roosevelt entries; 21 are numbered documents listed a second time, kept as cross-references |
| Texts | 1,140 documents with a text: 101 collated against a primary printing, 331 Statutes at Large digitizations, 708 Wikisource transcriptions |
| Stories | 114 public stories, written from research entries verified October 12, 2026 |
| Summaries | Every distinct document has a one- or two-sentence plain-language summary, categories, an action, places, states and a 1–5 weight |

## What's in a record

```json
{
  "id": "proc-563", "type": "proclamation", "number": "563", "date": "1905-06-02",
  "title": "Redesignating the Wichita Forest Reserve, Oklahoma, as a Game Preserve",
  "summary": "…",
  "categories": ["wildlife", "forests"], "action": "transfer",
  "places": [{"name": "Wichita Forest Reserve", "kind": "forest", "state": "Oklahoma"}],
  "states": ["Oklahoma"], "significance": 4,
  "signed_as": "T. Roosevelt",
  "countersigned_by": {"name": "Francis B. Loomis", "role": "Acting Secretary of State"},
  "citations": {
    "app": {"number": 563, "url": "https://www.presidency.ucsb.edu/documents/proclamation-563"},
    "statutes": {"volume": 34, "page": 3062, "cite": "34 Stat. 3062–3063", "page_image": "https://www.govinfo.gov/…"}
  },
  "text": {"paragraphs": ["WHEREAS, …"], "kind": "statutes_digitization", "verified": false, "source": "Statutes at Large, 34 Stat. 3062"},
  "date_notes": [], "stories": [ … ],
  "day_by_day": "https://daybyday.labs.trlibrary.com/day.html?date=1905-06-02"
}
```

Full field reference: [docs/schema.md](docs/schema.md). How the data was assembled and reconciled: [docs/methods.md](docs/methods.md).

## Repository layout

```
sources/              research catalogs the base list is parsed from (committed)
  executive_actions_index.md        numbered EOs (Wikipedia list) and proclamations 465–871 (APP)
  TR_Unnumbered_Orders_Catalog.md   Lord's 126 unnumbered entries, reconciled 2026-10-12
data/                 canonical dataset (committed)
  base.jsonl          one catalog row per document (built by parse_sources.py; never edit by hand)
  corrections.json    date, title, summary and state corrections, each with its source
  statutes_proclamations.jsonl      Roosevelt's proclamations as printed in the Statutes at Large
  proclamation_statutes_map.json    numbered proclamation → Statutes printing
  statutes_overrides.json           manual pairings the matcher cannot decide
  sources/wikisource_eo.json        raw Wikisource wikitext   wikisource_eo.jsonl  parsed
  enrich/*.jsonl      summaries, categories, places, states, people, significance (18 chunks)
  stories/NNN.md      public stories          stories/texts/NNN.json  collated full texts
  documents.jsonl/.csv, stories.json, stats.json   assembled output (built)
pipeline/             build scripts and the worker briefs (enrich, story, site)
site/                 explorer pages, assets/, widgets/executiveactions.js (site/api and site/data are built)
docs/                 schema and methods
private/              research inputs, never committed (gitignored): the research file, the
                      Statutes XML (symlink), research entries, enrichment inputs
```

## Rebuilding

```bash
python pipeline/build_dataset.py   # data/ → documents.jsonl/.csv, stories.json, stats.json
python pipeline/build_api.py       # data/ → site/api/v1 and site/data (GitHub Actions runs only this, on every push to main)
python -m http.server -d site 8000 # preview at http://localhost:8000
```

Both scripts use the Python standard library only. `build_api.py` runs from committed files alone. `build_dataset.py` also runs from committed files, but it reads `private/TR_Executive_Actions_Research.md` to link documents to the research entries their stories came from; without that file about 42 records lose a story link. Earlier steps (parsing the Statutes XML, fetching Wikisource, enrichment, stories) are described in [docs/methods.md](docs/methods.md) and [CLAUDE.md](CLAUDE.md).

## Sources

- **Wikipedia, *List of executive actions by Theodore Roosevelt*:** numbers, dates and titles of the numbered executive orders.
- **The American Presidency Project** (UC Santa Barbara): numbers, dates and titles of Proclamations 465–871.
- **Clifford L. Lord, ed., *List and Index of Presidential Executive Orders, Unnumbered Series, 1789–1941*** (Historical Records Survey, WPA, 1943): the unnumbered orders, transcribed from the page images.
- ***United States Statutes at Large*, vols. 32–35** (GovInfo USLM XML and page images): the printed text of the proclamations.
- **Wikisource:** volunteer transcriptions of numbered executive orders, mostly from printed compilations such as the Civil Service Commission reports.
- The Library's research file on Roosevelt's executive actions (114 entries, verified October 12, 2026), which supplies the stories, the collated texts and the corrections.

## Verification status

Texts marked `verified: true` (`kind: "collated"`) were checked word for word against a named primary printing or image. All other texts are working copies: the Statutes text is GPO's unproofread digitization and the Wikisource texts are volunteer transcriptions. Check the page image or original before quoting any of them. Summaries are written by the Library from each document's title, text and margin notes only. 278 numbered executive orders and 103 distinct unnumbered orders have no text here yet.

## License

Data: CC BY 4.0, Theodore Roosevelt Presidential Library. Code: MIT (see LICENSE). Source texts (the orders and proclamations themselves, the Statutes at Large, Lord's 1943 list) are U.S. government works in the public domain.

## How to cite

Theodore Roosevelt Presidential Library, *Theodore Roosevelt's Executive Orders and Proclamations*, https://executiveactions.labs.trlibrary.com (accessed *date*).

For a single document, cite the document page (`/document.html?id=proc-563`) and, for its text, the printing named in `text.source` (for example, 34 Stat. 3062).

Corrections are welcome at hello@trlibrary.com.
