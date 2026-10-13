# Worker brief — impact, legacy and "what happened next"

You are adding the **impact** layer to the Theodore Roosevelt Presidential Library's dataset of Roosevelt's executive orders and proclamations: fuller narrative in the stories, plus structured datapoints on every document. Your job is editorial extraction, not research: **add no new facts.** Everything comes from the research entry.

## Inputs (per entry NNN)
- `/home/claude/executiveactions/private/entries/NNN.md` — the verified research entry (with working notes, corrections history, ⚠️ VERIFY flags).
- `/home/claude/executiveactions/data/stories/NNN.md` — the public story already written from it (read `pipeline/story_brief.md` for its rules; they all still apply).
- `/home/claude/executiveactions/data/documents.jsonl` — every document record (ids like `eo-473`, `eo-288-half`, `eo-389-a`, `proc-563`, `uo-054`, `proc-x-1907-01-24`). Use it to confirm ids, dates and titles.

## Output 1 — fuller narrative in `data/stories/NNN.md`
Rewrite **only** the `## Political impact` and `## Legacy` sections (and you may add to `open_questions`). Leave front matter fields and the other sections as they are.
- Carry over **all substantive** reception, political-impact and legacy material from the entry that the story currently drops: press and public reaction, Congress, courts, agencies, diplomacy, local consequences, what the places and policies became, later reversals. Strip working notes exactly as the story brief says (no "Corrected …", "entry #", "verified", agent/pass talk); keep the corrected fact.
- Political impact is written from inside the period (through about 1909–1912 at most); later outcomes go in Legacy.
- ⚠️ VERIFY claims never become fact: leave out or phrase as uncertain, and add an `open_questions` line.
- Quotations: copy exactly from the entry with the source named in the sentence. Newspaper quotes that the entry says come from unchecked OCR or need collation are **paraphrased**, not quoted. Roosevelt's words verbatim with source named, or not at all.
- Voice: friendly, plain, specific, a knowledgeable park ranger; minimal we/our; nonpartisan; no triumphalism or museum-speak. "Buttes," never "mesa" (except proper nouns). Cross-reference other stories as `[exact story title](story:NN)` (titles: `data/stories.json`).
- Use subheads (`###`) inside a long Legacy if it helps (e.g. one per place). Bulleted roundups are fine for grouped entries.

## Output 2 — structured datapoints in `data/impact/NNN.json`
```json
{
  "story": 22,
  "documents": {
    "uo-098": {
      "reception": [
        {"text": "Bird-Lore hailed the reservation as …", "source": "Bird-Lore VII (1905), p. 72", "date": "1905"}
      ],
      "political_impact": [
        {"kind": "administrative", "text": "The Agriculture Department's Biological Survey took charge of the island and posted a warden.", "source": "Palmer, Circular 87 (1912)", "date": "1905"}
      ],
      "legacy": [
        {"text": "The 1940 renaming made it Breton National Wildlife Refuge.", "source": "Proc. 2416, 54 Stat. 2717", "date": "1940-07-25"}
      ],
      "today": [
        {"name": "Breton National Wildlife Refuge", "kind": "wildlife_refuge", "relation": "origin", "state": "Louisiana", "since": "1904-10-04", "note": "Second-oldest refuge in the system.", "source": "U.S. Fish and Wildlife Service"}
      ],
      "related": [
        {"id": "eo-369-a", "relation": "enlarged_by", "note": "Second Breton order added Old Harbor and Freemason islands."}
      ],
      "later_actions": [
        {"date": "1940-07-25", "text": "Renamed Breton National Wildlife Refuge by Proclamation 2416.", "source": "54 Stat. 2717"}
      ],
      "uncertain": ["Whether …"]
    }
  }
}
```
Only include a document if the entry says something **specific to it**; omit empty arrays; omit documents with nothing specific. A grouped entry (e.g., 53 forest proclamations) should still give each document whatever the entry says about it individually (its successor forest, merger, later fate), and only that.

### Field rules
- Every datapoint `text`: one or two plain sentences in Library voice, standing on its own, no quotation unless exact and short. `source`: the short citation the entry gives for that fact (Statutes vol/page, report and page, newspaper and date, book). If the entry gives no source for it, `"source": "research entry"`. `date`: YYYY, YYYY-MM or YYYY-MM-DD when the entry gives one, else omit.
- **reception** — how people reacted at the time: press, public, interest groups, foreign governments.
- **political_impact** — effects in the period; `kind` ∈ congress · court · administrative · diplomatic · local · economic · political.
- **legacy** — longer-term significance and outcomes after the period.
- **today** — present-day units or institutions that trace to the document. `kind` ∈ national_park · national_monument · national_forest · national_grassland · wildlife_refuge · military_installation · indian_reservation · state_park · lighthouse · other. `relation` ∈ origin (the document created what became it) · part (its lands are now part of it) · renamed · absorbed_into · abolished (no longer exists; `name` = what it was) · transferred. `since` = the Roosevelt document's date when relation is origin. Only what the entry states.
- **related** — links to other documents **in documents.jsonl**, from this document's point of view. `relation` ∈ enlarges · enlarged_by · reduces · reduced_by · modifies · modified_by · revokes · revoked_by · restores · renames · renamed_by · amends · amended_by · supersedes · superseded_by · implements · same_subject. Only include a link when the entry or the document text supports it; check the id exists.
- **later_actions** — later government actions **outside** the corpus (later presidents, Congress, courts, agencies) that changed this document's subject: `date`, `text`, `source`.
- **uncertain** — plain sentences for the entry's unresolved points about this document (same idea as open_questions).

Also add `"story_level"` (optional) to the JSON for impact points that belong to the whole group rather than one document, same field shape (`reception`, `political_impact`, `legacy`, `today`).

## Checks before finishing
- `python3 -c "import json;json.load(open('data/impact/NNN.json'))"` passes; every id exists in documents.jsonl; every `related.id` exists.
- Story front matter still parses (same keys), no working-note leftovers (`grep -n "⚠\|VERIFY\|entry #\|Corrected 20\|research entry" data/stories/NNN.md` returns nothing).
- Nothing in either output that isn't in the entry.

## Final reply
≤80 words: entries done, number of documents with datapoints, count of `today` items, anything you could not finish, and any date/title in documents.jsonl the entry shows to be wrong that isn't already noted in `data/corrections.json`.
