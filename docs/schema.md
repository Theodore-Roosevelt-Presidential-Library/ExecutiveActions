# Executive Actions — data schema

All dates are ISO `YYYY-MM-DD` (or `YYYY-MM` when only the month is known). IDs are lowercase and stable across releases.

**IDs:** `eo-{number}` for numbered executive orders (`eo-1003`; letter suffixes as `eo-389-a`, `eo-302-a`; half numbers as `eo-288-half`), `proc-{number}` for numbered proclamations (`proc-563`), `proc-x-{date}` for the three proclamations printed in the Statutes at Large outside the numbered series, and `uo-{NNN}` for Lord's unnumbered entries (`uo-001` … `uo-126`, Lord's own sequence).

## Document (`data/documents.jsonl`, `/api/v1/documents/{id}.json`)

1,542 records: 1,006 executive orders, 410 proclamations and 126 unnumbered-order entries. The 21 unnumbered entries with `duplicate_of` set are cross-references to a numbered document, so the dataset has 1,521 distinct documents.

### Every record

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | see above |
| `type` | string | `executive_order`, `proclamation` or `unnumbered_order` |
| `number` | string \| null | as printed in the list: `"1003"`, `"194-A"`, `"302A"`, `"288½"`. Null for unnumbered orders and the three `proc-x` proclamations |
| `tr_sequence` | int \| null | executive orders only: the row's relative number in the Wikipedia list (1–1016, not contiguous) |
| `lord_number` | int \| null | unnumbered orders only: Lord's entry number, 1–126 |
| `date` | string \| null | date signed, after corrections. `YYYY-MM` for two orders known only to the month (EOs 400, 401); null for EO 310-A, a blank number in the official file |
| `date_precision` | string \| null | `day`, `month`, or null when there is no date |
| `title` | string | as given by `title_source`, with corrections applied |
| `title_source` | string | `Wikipedia, List of executive actions by Theodore Roosevelt` · `American Presidency Project` · `Lord (ed.), List and Index of Presidential Executive Orders, Unnumbered Series (1943)` · `Statutes at Large, list of proclamations` |
| `title_notes` | string[] | only present when there is something to say: a corrected title ("Corrected from “…”. *why*") or a caution about the title (77 records) |
| `date_notes` | string[] | always present, often empty: disagreements between sources (APP vs. Statutes, Wikisource vs. Wikipedia), corrections ("Corrected from “…”. *why*"), Lord's bracketed dates, and editorial date notes |
| `citations` | object | see below |
| `text` | object \| null | see below; null for 381 distinct documents |
| `summary` | string \| null | 1–2 sentences in the Library's words, based only on the document's title, text and margin notes. Null only on Lord duplicates |
| `categories` | string[] | 1–3 subject slugs, primary first (list below) |
| `action` | string \| null | what the document did (list below) |
| `places` | object[] | `{name, kind, state}`, places the document acts on, in the document's own spelling. `kind`: forest, monument, wildlife-reservation, military-reservation, naval-reservation, lighthouse, indian-reservation, land-district, town, island, state, country, canal-zone, other |
| `states` | string[] | modern state names, plus Puerto Rico, Philippines, Guam, American Samoa, Panama Canal Zone, District of Columbia. Oklahoma covers Oklahoma and Indian Territories |
| `people` | string[] | individuals the document acts on (appointees, people transferred or reinstated), as written; never the signer or countersigner |
| `significance` | int 1–5 \| null | 1 individual action · 2 routine · 3 substantive · 4 notable · 5 landmark. An editorial ranking aid, not a fact. Null on Lord duplicates |
| `stories` | int[] | numbers of the stories that cover the document |
| `day_by_day` | string \| null | link to that date in Day by Day; null without a full date |

### Proclamations only

| Field | Type | Notes |
| --- | --- | --- |
| `signed_as` | string \| null | the signature as printed in the Statutes ("Theodore Roosevelt", "T. Roosevelt") |
| `countersigned_by` | object \| null | `{name, role}`; role is `Secretary of State`, `Acting Secretary of State` or null. Null for two proclamations whose signature block is missing from the digitization |
| `numbering_note` | string | only on the three `proc-x` records: printed in the Statutes but not in the APP numbering; unverified against the State Department register |

### Unnumbered orders only

| Field | Type | Notes |
| --- | --- | --- |
| `lord_description` | string | Lord's entry as transcribed in the research catalog, with the catalog's Markdown and annotations |
| `reconciliation` | string | `distinct` (105) or `numbered_duplicate` (21) |
| `duplicate_of` | string \| null | id of the numbered EO or proclamation this entry repeats |
| `reconciliation_note` | string | how the entry was matched or cleared, in Markdown |

### `citations`

| Key | Present on | Fields |
| --- | --- | --- |
| `app` | the 407 numbered proclamations | `number`, `url` (American Presidency Project document page) |
| `statutes` | all 410 proclamations | `volume`, `page`, `last_page`, `cite` ("34 Stat. 3062–3063"), `page_image` (GovInfo PDF of the first page), `statutes_date` (the date the Statutes print it under), `table_title` (the caption in the volume's list of proclamations; not on `proc-x` records) |
| `wikisource` | 761 executive orders | `url`, `revid` (page revision used), `printed_source` (the compilation the transcription came from, e.g. "General Orders, No. 7, War Dept., January 16, 1909"; may be null) |
| `lord` | all unnumbered entries | `number`, `page` (book page in Lord 1943), `citations` (Lord's own citations, e.g. "X Richardson 521"; a parenthesized "(EO 1014)" is a later order that refers back to this one, not this order's number) |

### `text`

Every text has `paragraphs` (string[]), `source`, `kind`, `verified` and `note`. `kind` decides the rest:

| `kind` | Count (distinct) | `verified` | Extra fields | What it is |
| --- | --- | --- | --- | --- |
| `collated` | 101 (79 proclamations, 20 EOs, 2 unnumbered) | true | `story` (the story whose texts file supplied it) | checked word for word against a named primary printing or image; `source` names it and the date of collation, `note` records the collator's remarks |
| `statutes_digitization` | 331 | false | `marginal_notes` (string[], the printed margin notes) | GPO's USLM digitization of the Statutes at Large, not proofread; `source` is e.g. "Statutes at Large, 34 Stat. 3062" |
| `wikisource_transcription` | 708 | false | `signed`, `place_date` (signature and dateline as transcribed) | volunteer transcription of a printed compilation; `source` names the compilation when Wikisource gives one |

A collated text replaces any machine text for the same document. Quote only collated texts without checking the page image or original first.

### Vocabularies

**Categories** (label, timeline group): forests (Forests), monuments (National monuments), wildlife (Wildlife and bird reservations), public-lands (Public lands), water-reclamation (Water and reclamation), coal-minerals (Coal and minerals), conservation-policy (Conservation policy) — group `land`; indian-lands — `indian`; civil-service — `civil`; government-administration, congress, copyright, ceremonial, statehood, labor-business — `gov`; military-naval, lighthouses — `military`; canal-zone (Panama Canal Zone), insular-territories (Island territories) — `territories`; foreign-affairs, trade-reciprocity — `foreign`.

**Actions:** establish, enlarge, reduce, modify, revoke, restore, transfer, open, appoint, amend-rules, regulate, announce, convene, grant, other.

## Corrections (`data/corrections.json`)

An object keyed by document id (keys starting with `_` are comments). Applied by `build_dataset.py` after the catalog, text and enrichment are merged.

| Key | Effect |
| --- | --- |
| `date` | replaces the date; adds "Corrected from “old”. *why*" to `date_notes`. If the new date equals the Statutes date, the APP-vs-Statutes note is dropped |
| `title` | replaces the title; adds "Corrected from “old”. *why*" to `title_notes` |
| `summary`, `states`, `people`, `action` | replace the enrichment value |
| `text_note` | appends a caution to `text.note` (e.g. a transcription that belongs to another order) |
| `date_note` | adds a note to `date_notes`; the date is unchanged |
| `title_note` | adds a note to `title_notes`; the title is unchanged |
| `why` | the source for the change. Required with any replacement |

## Impact (`data/impact/NNN.json`)

One file per research entry, written under `pipeline/impact_brief.md` from that entry only. `build_dataset.py` merges every file into the records (a Lord duplicate's points also go to the numbered document it matches).

```json
{"story": 22,
 "documents": {"uo-098": {
   "reception":        [{"text": "…", "source": "Evening Star (Washington), October 4, 1904", "date": "1904-10-04"}],
   "political_impact": [{"kind": "administrative", "text": "…", "source": "…", "date": "1905"}],
   "legacy":           [{"text": "…", "source": "…", "date": "1975-01-03"}],
   "today":            [{"name": "Breton National Wildlife Refuge", "kind": "wildlife_refuge", "relation": "origin", "state": "Louisiana", "since": "1904-10-04", "note": "…", "source": "…"}],
   "related":          [{"id": "eo-369-a", "relation": "enlarged_by", "note": "…"}],
   "later_actions":    [{"date": "1938-10-04", "text": "…", "source": "EO 7983"}],
   "uncertain":        ["…"]}},
 "story_level": {"reception": [], "political_impact": [], "legacy": [], "today": []}}
```

- `political_impact.kind`: congress · court · administrative · diplomatic · local · economic · political.
- `today.kind`: national_park · national_monument · national_forest · national_grassland · wildlife_refuge · military_installation · indian_reservation · state_park · lighthouse · other. `today.relation`: origin (the document created it) · part (its land is now part of it) · renamed · absorbed_into · abolished · transferred.
- `related.relation` (from this document's point of view): enlarges/enlarged_by · reduces/reduced_by · modifies/modified_by · revokes/revoked_by · restores · renames/renamed_by · amends/amended_by · supersedes/superseded_by · implements · same_subject.

On each record in `documents.jsonl`:
- `impact`: the merged object above minus `related`, each point tagged with the `story` it came from; `null` when the research says nothing specific about the document.
- `related`: one link per other document, `{id, relation, note, story, inferred, date, title, type, number}`. When only one side states a link, the build adds the inverse (`inferred: true`, no note). A specific relation wins over `same_subject`.

`data/story_impact.json` holds the `story_level` points by story number.

## Statutes overrides (`data/statutes_overrides.json`)

`{"proc-796": {"volume": 35, "page": 2177, "date": "1908-01-16", "contains": "Pinnacles", "why": "…"}}` forces a proclamation's pairing with the Statutes printing at that volume, page and date whose text contains `contains`.

## Enrichment (`data/enrich/NN.jsonl`)

One line per document: `{id, summary, categories, action, places, states, people, significance}`, as defined above. Written by workers under `pipeline/enrich_brief.md`. Where a chunk gives no categories or action, `build_dataset.py` falls back to keyword rules on the title.

## Story (`data/stories/NNN.md`, `/api/v1/stories/{number|slug}.json`)

Front matter, then Markdown:

| Field | Type | Notes |
| --- | --- | --- |
| `number` | int | the research entry number (file name, zero-padded) |
| `slug` | string | unique, lowercase, hyphenated |
| `title` | string | |
| `dek` | string | one plain sentence on what the documents did |
| `documents` | id[] | documents the story is about; empty for thematic stories with no document of their own |
| `related_documents` | id[] | documents mentioned but covered elsewhere |
| `date_start`, `date_end` | date | |
| `themes` | string[] | category slugs |
| `places` | string[] | |
| `open_questions` | string[] | plain-language versions of the entry's unresolved ⚠️ VERIFY flags; shown on the site as "Still being researched" |

Body sections: At a glance, Background, Historical context, Political impact, Legacy, Sources. Links: `[title](story:NN)` to another story, `[label](doc:ID)` to a document.

## Collated texts (`data/stories/texts/NNN.json`)

`{document_id: {"paragraphs": [...], "collated_against": "…", "notes": "…"}}`. 74 files cover 101 documents. `collated_against` becomes `text.source`, `notes` becomes `text.note`.

## Intermediate files

- `data/base.jsonl` — catalog rows from `parse_sources.py`: id, type, number, `number_sort`, `tr_sequence` or `lord_number`, date, `date_precision`, title, `title_source`; unnumbered entries also carry `date_note`, `date_inferred_by_lord`, `lord_description`, `lord_citations`, `lord_page`, `reconciliation`, `duplicate_of`, `reconciliation_note`. 1,539 rows (no `proc-x` records; those are added at assembly).
- `data/statutes_proclamations.jsonl` — 410 proclamations signed by Roosevelt in Statutes vols. 32–35: `volume`, `statutes_number`, `date`, `page`, `last_page`, `paragraphs`, `marginal_notes`, `signatures`, `signer`, `countersigner`, `countersigner_role`, `has_seal`, `list_titles`, `list_page`, `list_date`, `signature_block_missing_in_xml`.
- `data/proclamation_statutes_map.json` — `{proc_id: {volume, page, last_page, statutes_number, statutes_date, list_title, score, date_gap_days, _i}}`; `_i` is the row index in `statutes_proclamations.jsonl`.
- `data/wikisource_eo.jsonl` — `{id, number, title, date, cite, notes, paragraphs, signed, place_date, not_located, url, revid}` for 761 pages.

## API (`site/api/v1/`)

Static JSON on GitHub Pages, built by `pipeline/build_api.py`. Base: `https://executiveactions.labs.trlibrary.com/api/v1/`.

| Endpoint | Contents |
| --- | --- |
| `index.json` | title, publisher, coverage, counts, by year/month/category, categories and groups, significance labels, `dataset_stats` (stats.json), sources, license, `cite_as`, endpoint list, downloads |
| `documents.json` | compact list of every record: `id, type, number, date, title, summary, categories, action, states, significance, stories, has_text, label` (+ `duplicate_of`); distinct documents by date, then the 21 Lord duplicates |
| `documents/{id}.json` | the full record plus `label`, `type_label`, `has_text`, `category_labels`, `state_refs`, `story_refs`, `significance_label`, `duplicates` (Lord entries that repeat it) or `duplicate_of_ref`, `prev`, `next`, `url`, `reconciliation_note_html` |
| `years/{YYYY}.json` | `{year, count, documents}` (1901–1909) |
| `categories/index.json` | `[{slug, label, group, count, primary}]` |
| `categories/{slug}.json` | `{slug, label, group, count, documents}` |
| `states/index.json` | `[{name, slug, count}]` |
| `states/{slug}.json` | `{name, slug, count, documents}` |
| `types/{executive_order\|proclamation\|unnumbered_order}.json` | `{type, label, count, documents}` |
| `stories/index.json` | story metadata with `theme_labels`, `document_count`, `open_question_count`, `url` |
| `stories/{number}.json`, `stories/{slug}.json` | metadata + `open_questions`, `documents`, `related_documents` (compact), `markdown`, `html` |
| `on-this-day/{MM-DD}.json` | `{month_day, count, documents}`, most significant first; a file exists for every calendar date, including 02-29 |
| `countersigners.json` | `[{name, count, roles, first, last, documents}]` |
| `search.json` | `[{id, title, summary, date, type, label}]` for client-side search |

Lord duplicates get their own `documents/{id}.json` but are left out of counts, years, categories, states, types, on-this-day, search and previous/next. Bulk downloads: `/data/documents.jsonl`, `/data/documents.csv`, `/data/stats.json`.

- `then-and-now/index.json` — every present-day place or institution traced to a document: `{name, kind, kind_label, slug, states, first, origin, count, documents: [{id, label, date, title, relation, relation_label, district, since, note, source, story}]}`; `then-and-now/{kind}.json` per kind. Institutions that are not places (e.g. the U.S. Commission of Fine Arts) stay on document pages but are left out of this list.
- Story JSON adds `impact` (story-level points) and `documents_impact` (each member document's points).

### CSV (`documents.csv`)

`id, type, number, date, title, categories, action, states, statutes_cite, countersigned_by, stories, duplicate_of, text_source, summary`; list fields are joined with `;`, and `text_source` holds the text `kind`.

## Page embed for trlibrary.com (`site/embed/executive-actions.js`)

Renders the explorer inside host pages without an iframe, so links stay on the host site:

```html
<div data-ea-view="index" data-base="/tr/presidency/executive-actions"></div>
<script src="https://executiveactions.labs.trlibrary.com/embed/executive-actions.js" defer></script>
```

Views: `index` (filters sync to the URL), `action` (reads `?id=`), `stories`, `story` (reads `?n=`), `then-and-now`, `featured` (landmark actions, `data-limit`). Pages it links to: `{base}`, `{base}/action?id=`, `{base}/stories`, `{base}/story?n=`, `{base}/then-and-now`. The `action` and `story` views set the page title, description, Open Graph tags and canonical link to include the query string (`data-meta="off"` to stop that). Styles are scoped under `.ea` and inherit the host page's fonts.
