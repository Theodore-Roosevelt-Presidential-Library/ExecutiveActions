# Worker brief — API, explorer site and widgets for Executive Actions

Build the static JSON API, explorer pages and embeddable widgets for the Theodore Roosevelt Presidential Library's dataset of Roosevelt's executive orders and proclamations, modeled closely on the sibling project **Day by Day** (clone at `/home/claude/theodore-roosevelt-presidential-library/daybyday` — read its `pipeline/build_api.py`, `site/*.html`, `site/assets/app.css`, `site/assets/app.js`, `site/widgets/daybyday.js`, `.github/workflows/pages.yml`, `CLAUDE.md`, and reuse its look, structure and conventions). Repo: `/home/claude/executiveactions`. Live address will be **https://executiveactions.labs.trlibrary.com** (GitHub Pages, custom domain via `site/CNAME`).

## Data you build from (read-only; other workers are still filling some fields — handle nulls and missing files gracefully)
- `data/documents.jsonl` — one record per document (≈1,542 incl. 21 Lord entries that duplicate numbered orders: `duplicate_of` set; treat those as cross-references, not separate actions). Key fields: id, type (`executive_order` | `proclamation` | `unnumbered_order`), number, date (YYYY-MM-DD, or YYYY-MM when precision is month, or null), title, summary (may be null for now → fall back to title), categories [], action, places [{name, kind, state}], states [], people [], significance (1–5 or null), stories [story numbers], citations {statutes {cite, page_image, …}, app {url}, wikisource {url, printed_source}, lord {…}}, countersigned_by {name, role}, signed_as, text {paragraphs[], source, kind (`collated` | `statutes_digitization` | `wikisource_transcription`), verified, note}, date_notes [], numbering_note, lord_description, reconciliation_note, day_by_day (URL).
- `data/stories/NNN.md` — public stories (YAML-ish front matter: number, slug, title, dek, documents [ids], related_documents, date_start, date_end, themes, places, open_questions; then Markdown sections). Links of the form `[title](story:NN)` must resolve to the story page. Some story files may not exist yet when you run — build whatever is there.
- `data/stats.json`.

## Build
1. `pipeline/build_api.py` (stdlib only; GitHub Actions runs it) → `site/api/v1/`:
   - `index.json` (dataset meta, counts by type/category/year, endpoint list, license, base URL)
   - `documents.json` (compact list for the index page: id, type, number, date, title, summary, categories, action, states, significance, stories, has_text)
   - `documents/{id}.json` (full record + resolved story titles/slugs + previous/next by date)
   - `years/{YYYY}.json`, `categories/{slug}.json`, `states/{slug}.json`, `types/{type}.json`
   - `stories/index.json`, `stories/{number}.json` and `stories/{slug}.json` (meta + markdown + rendered HTML — write a small Markdown→HTML converter for headings, paragraphs, lists, bold/italic, links incl. `story:NN`, blockquotes)
   - `on-this-day/{MM-DD}.json` (documents signed on that calendar date, most significant first)
   - `countersigners.json`, `search.json` (id, title, summary, date, type for client-side search)
   - copy bulk files to `site/data/` (documents.jsonl, documents.csv, stats.json)
2. Explorer pages in `site/` (plain HTML + `assets/app.css` + `assets/app.js`, no build step, CDN-free or pinned CDN versions only):
   - `index.html` — headline counts; a timeline (documents per month Sept 1901–Mar 1909, stacked by primary category, drawn in SVG/canvas yourself); the **index**: a fast filterable, searchable, sortable table/list (type, year, category, state, significance, has text) that deep-links via URL query params; each row → document page.
   - `document.html?id=…` — title, type/number, date (with date notes), summary, categories/states/places chips, countersignature, citations with links (Statutes page image, APP, Wikisource, Lord), the text (with its provenance label and the "not verified / check the page image before quoting" note when `verified` is false), stories it belongs to, link to Day by Day for that date, previous/next.
   - `stories.html` (cards grouped by theme/year) and `story.html?n=…` (rendered story, its documents listed with links, open questions shown in a calm "Still being researched" box).
   - `about.html` — what's here, counts and how they reconcile (1,006 numbered EOs + 105 distinct unnumbered = 1,111 EOs; 407 numbered proclamations + 3 printed in the Statutes but not in the APP numbering; Lord's 126 entries of which 21 duplicate numbered documents), sources and their limits, verification status, license (data CC BY 4.0 TRPL; code MIT; source texts public domain), how to cite.
   - `api.html` and `widget.html` (documentation with live examples), like Day by Day's.
3. `site/widgets/executiveactions.js` — custom elements for trlibrary.com embeds: `<trpl-action id="proc-563">` (card), `<trpl-actions-on-this-day>`, `<trpl-actions-list category="forests" state="Arizona" year="1908" limit="10">`, `<trpl-story n="2">` (teaser card). Shadow DOM, light/dark aware, no dependencies, fetch from the live API base (overridable via `data-api`).
4. `.github/workflows/pages.yml` (like Day by Day's; check that `site/api/v1/index.json` and one document file exist), `site/CNAME` = `executiveactions.labs.trlibrary.com`, `site/404.html`.

## Design
TRPL look, consistent with Day by Day: reuse its palette, type and components. Accessible (contrast, keyboard, alt text), responsive to phone width, fast with 1,500 rows (render incrementally). Library voice in all UI copy: plain, warm, specific; minimal we/our.

## Check before finishing
Run `python pipeline/build_api.py`, serve `python -m http.server -d site 8000`, and verify with Playwright (Chromium is preinstalled; `executablePath: '/opt/pw-browsers/chromium'` if needed) that index, a document page (a proclamation with Statutes text, an EO with Wikisource text, a Lord duplicate), a story page, and the widget demo render without console errors at desktop and 390px widths. Fix what breaks.

Do not edit anything under `data/` or other pipeline scripts. Final reply: ≤80 words — what you built and anything left undone.
