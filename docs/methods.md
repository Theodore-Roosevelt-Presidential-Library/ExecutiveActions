# How Executive Actions was built

## 1. Sources

| Source | Used for | Where it lives |
| --- | --- | --- |
| Wikipedia, *List of executive actions by Theodore Roosevelt* | numbers, dates and titles of the 1,006 numbered executive orders (EOs 141–1050, including lettered and half numbers such as 389-A and 288½) | transcribed into `sources/executive_actions_index.md` |
| The American Presidency Project (UC Santa Barbara) | numbers, dates and titles of Proclamations 465–871 (407, checked contiguous: no gaps, no duplicates) | `sources/executive_actions_index.md` |
| Clifford L. Lord, ed., *List and Index of Presidential Executive Orders, Unnumbered Series, 1789–1941* (WPA Historical Records Survey, 1943), book pp. 186–204 | the unnumbered orders: 126 Roosevelt entries, Sept. 20, 1901 to Dec. 1, 1908 | `sources/TR_Unnumbered_Orders_Catalog.md` |
| *United States Statutes at Large*, vols. 32–36, GovInfo USLM XML | printed text, margin notes, signatures and page images of the proclamations | `private/statutes/` (not committed; download from `https://www.govinfo.gov/content/pkg/STATUTE-NN/uslm/STATUTE-NN.xml`) |
| Wikisource, "Executive Order N" pages linked from *Author:Theodore Roosevelt/Executive orders* | volunteer transcriptions of numbered executive orders | `data/sources/wikisource_eo.json` |
| The Library's research file on Roosevelt's executive actions | 114 research entries, verified October 12, 2026: corrections, collated texts, stories | `private/` (not committed) |

Lord's list is a two-column typescript whose OCR scrambles dates and descriptions, so every entry in the catalog was transcribed by reading the scanned page images. A date in Lord's brackets is his own inference and is kept as a note.

## 2. Catalog (`pipeline/parse_sources.py`)

Parses the two Markdown catalogs into `data/base.jsonl`: one row per numbered EO, per numbered proclamation, and per Lord entry. Runs from committed files.

## 3. Reconciling Lord's list with the numbered series

Each of Lord's 126 entries was compared with all 1,413 numbered documents: by date (same day, then ±10 days), by every place name and subject keyword across all numbered titles, and by reading candidates against Lord's citation key and the research entries. A parenthesized "(EO ####)" in Lord is a later order that refers back to the entry, never the entry's own number, so it was not treated as a match on its own.

Result (final, October 12, 2026): 105 entries are distinct unnumbered orders and 21 are numbered documents listed a second time (19 entries for executive orders, EO 328-B twice, and 2 for Proclamations 502 and 563). The last seven open identifications were settled from Lord's numbered-series volume (*Presidential Executive Orders, Numbered 1–8030*, 1944) and period printings. One example: Lord's no. 18 (Prince Henry of Prussia, Feb. 5, 1902) is EO 162 of January 24, 1902; February 5 is the publication date.

The 21 duplicates stay in the data as cross-references (`duplicate_of`) and are left out of every count. That gives **1,006 + 105 = 1,111 executive orders**.

Lord warns that a cluster of same-day entries may be one order rather than several. The three Oklahoma land entries of January 20, 1902 (nos. 15–17) may be a single order; if so, the unnumbered count would fall by up to two.

## 4. Proclamations in the Statutes at Large (`pipeline/parse_statutes.py`, `pipeline/match_statutes.py`)

`parse_statutes.py` reads every `<presidentialDoc role="proclamation">` in vols. 32–36 and keeps those dated within Roosevelt's term and signed by him (or with no signature block in the XML): 410 proclamations, all in vols. 32–35. For each it records the volume, starting and last page (from the page markers), the date, the paragraphs with margin notes removed, the margin notes, the signatures and countersignature, whether a seal is printed, and the caption from the volume's own list of proclamations. Needs the private XML files.

`match_statutes.py` pairs each of the 407 APP proclamations with its printing. The volumes' tables of contents run out of step with the documents in vols. 34–36, so matching rests on the names in the APP title (forest, reservation, place, country; generic words like "establishing" or "forest reserve" removed) found in the printed text, especially its opening, plus date proximity within 45 days; the table caption is a tie-breaker. Pairs are taken best score first, each side used once. One pairing is forced in `data/statutes_overrides.json` (Proc. 796, Pinnacles, which APP dates January 28 and the Statutes and signed original date January 16, 1908). The script prints unmatched documents, date differences and weak matches for review.

All 407 matched. Where the APP date and the Statutes date still differ, the record carries a note (Procs. 530 and 543).

### The three Statutes-only proclamations

Three proclamations printed in the Statutes as signed by Roosevelt are not in the APP numbering. They are included as `proc-x-{date}`, which brings proclamations to **407 + 3 = 410**:

| Id | Subject | Printing |
| --- | --- | --- |
| `proc-x-1907-01-24` | Reciprocity with Portugal | 34 Stat. 3268 |
| `proc-x-1907-12-05` | Reciprocal commercial arrangement with Great Britain | 35 Stat. 2163 |
| `proc-x-1908-08-12` | Reciprocity with the Netherlands | 35 Stat. 2199 |

None has been checked against the State Department's register of proclamations. Each carries a `numbering_note` saying so.

## 5. Executive order texts from Wikisource (`pipeline/fetch_wikisource.py`, `pipeline/parse_wikisource.py`)

`fetch_wikisource.py` reads the link list on *Author:Theodore Roosevelt/Executive orders* and pulls the wikitext of every existing "Executive Order N" page through the MediaWiki API, 50 at a time, with backoff on rate limits. It stores each page's revision id. `parse_wikisource.py` reads the Potus-eo template (number, date, printed source), strips markup, and separates the signature and dateline. Of 761 pages, 33 have no body text and one is marked "text not located"; 728 executive orders end up with a text (708 from Wikisource, 20 replaced by collated texts). Where Wikisource's date differs from the Wikipedia list, the record says so (seven orders) rather than choosing.

## 6. Summaries and index fields (`pipeline/enrich_brief.md`)

Every distinct document was given a summary, categories, an action, places, states, people and a 1–5 weight by an AI worker following the brief, in 18 chunks (`data/enrich/00–17.jsonl`). The worker saw only the title, Lord's description, the Statutes margin notes and the first ~2,200 characters of the text, plus a keyword guess at categories and states to correct. The brief forbids outside facts: no later history, motives, acreage the text does not state, or claims about importance. When only a title exists, the summary restates it plainly. The inputs (`private/enrich_in/`) are not committed. `significance` is an editorial ranking aid, not a finding.

## 7. Stories and collated texts (`pipeline/story_brief.md`)

The research file's 114 entries, each verified on or before October 12, 2026, were turned into 114 public stories (`data/stories/001–114.md`). The work was editorial only: cut, condense and rephrase, add nothing. Working notes and correction histories were removed, keeping the corrected fact. Every ⚠️ VERIFY flag was either left out or written as uncertain and listed in `open_questions` (249 across the stories). Roosevelt's words appear verbatim with the source named, or not at all. Some stories are thematic (the Reclamation Act, the 1902 coal strike) and list no document of their own.

Where an entry reproduced a document's full text and said it had been collated against the Statutes page image or another named primary printing, that text was saved in `data/stories/texts/NNN.json` exactly as given. These 101 texts (74 files) replace the machine texts and are the only ones marked `verified: true`.

Documents link to stories two ways: through each story's `documents` list, and through the document numbers in the research entries' headings (read from `private/TR_Executive_Actions_Research.md`). 1,518 of 1,521 documents belong to at least one story.

## 8. Corrections (`data/corrections.json`)

The research entries and the story workers turned up errors in the source lists. 97 documents carry corrections, each with its source in `why`:

- **Dates** (12), e.g. Proc. 579 to July 14, 1905 from its dating clause (34 Stat. 3113); EO 342-A from 1904 to 1905; Lord's no. 23 from "Mar." to May 27, 1902 (Lord copied Richardson's misprint).
- **Titles** (50): typos in the source lists (Nebo, Kaniksu, Maury Mountain, Maui), captions that misdescribe the document (Proc. 589 reserves no townsites; Proc. 524 reduced the Yellowstone reserve rather than enlarging it), and wrong names (EO 1001 concerns C. M. Huntington, not W. W. Adams).
- **Notes** (10 date notes, 29 title notes): cautions added without changing the value, mostly where sources disagree and the original has not been checked, e.g. Pelican Island (Lord gives March 13, 1903; contemporary records give March 14).
- **Summaries, states, people** where the correction changes what the document did or where.

`build_dataset.py` applies them on top of the catalog, keeping the old value in a "Corrected from …" note.

## 9. Assembly (`pipeline/build_dataset.py`) and API (`pipeline/build_api.py`)

`build_dataset.py` merges catalog, Statutes texts and citations (with page-image links), Wikisource texts, collated texts, corrections, enrichment and story links into `data/documents.jsonl`, `documents.csv`, `stories.json` and `stats.json`. Text precedence: collated, then Statutes (proclamations) or Wikisource (executive orders). It adds the three Statutes-only proclamations and a Day by Day link for every fully dated document.

`build_api.py` turns those files into the static API in `site/api/v1/` and copies the bulk files to `site/data/`. GitHub Actions runs it on every push to `main` and deploys `site/` to GitHub Pages; nothing else in the pipeline runs in CI.

## Counts and how they reconcile

| | |
| --- | --- |
| Numbered executive orders | 1,006 |
| Lord's unnumbered entries | 126, of which 21 duplicate numbered documents → 105 distinct |
| Executive orders | 1,006 + 105 = **1,111** |
| Numbered proclamations (APP) | 407 |
| Statutes-only proclamations | 3 |
| Proclamations | **410** |
| Distinct documents | 1,111 + 410 = **1,521** (1,542 records with the 21 cross-references) |

Older figures in the research catalogs (117, 106, 1,530, 1,519) are superseded by the October 12, 2026 reconciliation.

## Known limitations

- **Missing texts.** 278 numbered executive orders and 103 distinct unnumbered orders have no text here.
- **Unproofread texts.** Statutes texts are GPO's vendor digitization and contain slips ("dpublic", "eclare"); Wikisource texts are volunteer transcriptions of later compilations. Both are `verified: false`. Check the page image or original before quoting.
- **The numbered EO list is Wikipedia's.** A numbered order missing from or misdated in that list would also hide a Lord match.
- **Statutes-only proclamations** are unverified against the State Department register.
- **Dates in dispute** are noted, not resolved, where the original has not been checked (Pelican Island, EO 162, EOs 154, 176, 468, 475, 613, 1049, Proc. 818 and others in `date_notes`). Two orders are dated only to the month and one number (EO 310-A) is a blank in the official file.
- **Lord's entries are not always separate orders.** Same-day clusters may be single orders.
- **Open questions.** Each story lists what remains unconfirmed; 249 such questions are open.
- **Summaries and weights** are written from the document alone and are editorial aids. The categories, actions and `significance` are judgments, not findings.
- **Statutes captions.** In vols. 34–36 the list of proclamations runs out of step with the documents; `table_title` comes from the matched printing, but a caption can still disagree with the text it sits beside.
