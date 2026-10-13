# Worker brief — enriching document records

You are adding plain-language summaries and index fields to records of Theodore Roosevelt's executive orders and proclamations for the Theodore Roosevelt Presidential Library's public index (trlibrary.com). Accuracy is the product.

## Input
`/home/claude/executiveactions/private/enrich_in/NN.jsonl` — one document per line: id, type, number, date, title, lord_description (unnumbered orders), marginal_notes (the printed margin notes of the Statutes), text_excerpt (first ~2,200 characters of the text, when a text exists — a machine digitization or volunteer transcription, so expect typos), rule_categories / rule_states (a keyword guess — correct them).

## Output
`/home/claude/executiveactions/data/enrich/NN.jsonl` — one line per input document, same order:
```
{"id": "proc-563",
 "summary": "Turned the Wichita Forest Reserve in Oklahoma Territory into a game preserve, setting the ground aside for the protection of game animals and birds.",
 "categories": ["wildlife", "forests"],
 "action": "transfer",
 "places": [{"name": "Wichita Forest Reserve", "kind": "forest", "state": "Oklahoma"}],
 "states": ["Oklahoma"],
 "people": [],
 "significance": 4}
```

### Fields
- **summary** — 1–2 sentences, ≤45 words, in plain, specific Library voice (friendly, concrete, no museum-speak; minimal we/our). Say **what the document did** — who or what, where, how. Base it **only** on the title, Lord's description, the margin notes and the text excerpt. **Add no outside facts** (no later history, no motives, no acreage unless the text states it, no claims about significance). If only a title exists, the summary restates it plainly ("Allowed the Navy Department to hire a coachman without a civil-service examination."). Don't start every summary with the same verb; don't quote unless a short phrase from the text is essential (then quote exactly).
- **categories** — 1–3 from: forests · monuments · wildlife · public-lands · indian-lands · water-reclamation · coal-minerals · military-naval · lighthouses · civil-service · government-administration · canal-zone · insular-territories · foreign-affairs · trade-reciprocity · copyright · ceremonial · congress · statehood · labor-business · conservation-policy. First = primary. (Individual appointments/exceptions/reinstatements → civil-service. Land-office/land-district changes → public-lands. Philippine/Puerto Rico/Hawaii/Alaska/Guam matters → insular-territories plus the subject category.)
- **action** — one of: establish · enlarge · reduce · modify · revoke · restore · transfer · open · appoint · amend-rules · regulate · announce · convene · grant · other.
- **places** — named places the document acts on (forest, monument, reservation, bird reservation, military/naval reservation, lighthouse, island, town, land district, Indian reservation, country). kind ∈ forest · monument · wildlife-reservation · military-reservation · naval-reservation · lighthouse · indian-reservation · land-district · town · island · state · country · canal-zone · other. Use the document's own spelling for the name (e.g. "Porto Rico" stays in the name only if it's part of a proper name; put "Puerto Rico" in state). Empty list if none.
- **states** — modern U.S. state names (or "Puerto Rico", "Philippines", "Guam", "American Samoa", "Panama Canal Zone", "District of Columbia"; foreign countries go in places, not states). "Oklahoma" covers Oklahoma and Indian Territories; "Arizona", "New Mexico" etc. for territories.
- **people** — named individuals the document acts on (appointees, people transferred or reinstated), as written. Not the signer or countersigner.
- **significance** — 1–5. 5: landmark actions (national monuments, major neutrality/amnesty/statehood proclamations, the largest forest creations, first bird reservations). 4: notable policy (new forests or bird reservations, civil-service rule changes of general effect, Canal Zone government, reciprocity agreements). 3: substantive but local (boundary changes, land-office consolidations, military reservations, land openings). 2: routine administrative orders of general application. 1: individual personnel actions.

## Rules
- Every input id appears exactly once in the output, valid JSON per line.
- Don't invent. If the text excerpt is garbled, rely on the title.
- Final reply: ≤40 words — count written and anything you could not do.
