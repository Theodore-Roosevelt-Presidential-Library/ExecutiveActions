# Worker brief — turning a research entry into a public story

You are converting one or more research entries about Theodore Roosevelt's executive orders and proclamations into **public stories** for the Theodore Roosevelt Presidential Library's website (trlibrary.com). The research entries are accurate but full of working notes. Your job is editorial, not research: **add no new facts.**

## Inputs
- `/home/claude/executiveactions/private/entries/NNN.md` — the research entry (verified 2026-10-12; contains working notes, corrections history, and ⚠️ VERIFY flags).
- `/home/claude/executiveactions/data/base.jsonl` — the document list (ids: `eo-473`, `eo-288-half`, `eo-389-a`, `proc-563`, `uo-001`…`uo-126` for Lord's unnumbered entries). Use it to get document ids right.

## Output 1 — `data/stories/NNN.md` (NNN = zero-padded entry number)

```
---
number: 37
slug: public-domain-restorations-1902          # short, lowercase, hyphenated, unique
title: "The Public-Domain Restorations of 1902"   # plain title; drop "(a grouped entry)"
dek: "One sentence, plain and specific, saying what these documents did."
documents: [proc-476, proc-478]                # every document this story is ABOUT, as ids from base.jsonl
related_documents: [proc-492]                   # documents mentioned but covered by another story
date_start: 1902-05-29
date_end: 1902-06-23
themes: [public-lands, indian-lands]           # from the vocabulary below
places: ["Capitan Grande, California", "Anadarko, Oklahoma Territory"]
open_questions:                                 # plain-language versions of the entry's remaining ⚠️ VERIFY flags
  - "Whether Jacob Kuhner ever received a patent for Section 7 is not known; the General Land Office patent records would show it."
---

## At a glance
2–4 sentences a visitor can read in 15 seconds.

## Background
## Historical context
## Political impact
## Legacy

## Sources
- Short-form citations of the primary and secondary sources the entry relies on (Statutes at Large volume and page; reports; newspapers with date and page; books). One per line. No URLs needed unless the entry gives a stable one.
```

For a thematic entry with no executive document in the corpus (e.g. the Reclamation Act, the 1902 coal strike, the Bureau of Corporations), `documents: []` and list the relevant ids under `related_documents` if any.

## Output 2 — `data/stories/texts/NNN.json` (only if the entry reproduces verified full text)
If the entry quotes a document's full text **and says it was collated against the Statutes at Large page image (or another named primary printing)**, save that text so it can override machine transcriptions:
```
{"proc-476": {"paragraphs": ["By the President …", "…"], "collated_against": "32 Stat. 2005–2006 (GovInfo page images), 2026-10-12", "notes": "seal restored; …"}}
```
Copy the text **exactly** as the entry gives it (keep `[SEAL.]`, original spelling, `[sic]`). Omit abridgment markers' surrounding commentary but keep the marker itself (e.g. `[Boundary description omitted …]`). If no collated full text, don't create the file.

## Editorial rules
1. **No new facts, no new quotations.** Everything you write must be in the entry. You may cut, condense, reorder and rephrase.
2. **Strip the working apparatus**: "Corrected 2026-10-12 —", "Resolved —", "the entry said…", "an earlier draft…", agent/run/pass/log talk, collation narratives, file and entry cross-reference talk. When a correction note carries a fact, keep the **corrected** fact, stated plainly, and drop the history of the error.
3. **⚠️ VERIFY flags**: never state a flagged claim as fact. Either leave it out or phrase it as uncertain ("may have", "is not known"), and add a plain sentence to `open_questions`.
4. **Roosevelt's words verbatim or not at all**, with the source named in the sentence (speech/letter/message and date). Quotes from documents in the corpus stay exactly as the entry gives them.
5. **Voice**: TRPL — friendly, vivid, plain, intellectually serious; a knowledgeable park ranger, not a professor. Minimal we/our/I/us. No museum-speak, no "world-class", no triumphalism. Nonpartisan.
6. **Write from inside the period** in Background, Historical context and Political impact; keep present-day outcomes in Legacy only.
7. **Length**: keep the substance; a typical story is 40–70% of the research entry's length. Grouped entries may list notable documents in a short bulleted roundup inside Background.
8. Cross-references to other stories: write `[title](story:NN)`.
9. "Buttes," never "mesa" (except proper nouns). Spell names as the historical record does.

## Theme vocabulary
forests · monuments · wildlife · public-lands · indian-lands · water-reclamation · coal-minerals · military-naval · lighthouses · civil-service · government-administration · canal-zone · insular-territories · foreign-affairs · trade-reciprocity · copyright · ceremonial · congress · statehood · labor-business · conservation-policy

## Final reply
≤60 words: stories written, document counts, any entry you could not finish.
