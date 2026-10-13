// Executive Actions — shared helpers for the explorer pages
const EA = (() => {
  const API = new URL("api/v1/", document.baseURI).href;
  const BASE = "https://executiveactions.labs.trlibrary.com";
  const cache = new Map();
  const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const CATS = {
    "forests": "Forests", "monuments": "National monuments", "wildlife": "Wildlife and bird reservations",
    "public-lands": "Public lands", "indian-lands": "Indian lands", "water-reclamation": "Water and reclamation",
    "coal-minerals": "Coal and minerals", "conservation-policy": "Conservation policy", "military-naval": "Military and naval",
    "lighthouses": "Lighthouses", "civil-service": "Civil service", "government-administration": "Government administration",
    "canal-zone": "Panama Canal Zone", "insular-territories": "Island territories", "foreign-affairs": "Foreign affairs",
    "trade-reciprocity": "Trade and reciprocity", "copyright": "Copyright", "ceremonial": "Ceremonial", "congress": "Congress",
    "statehood": "Statehood", "labor-business": "Labor and business"
  };
  const GROUPS = [
    ["land", "Forests, parks and public land", ["forests","monuments","wildlife","public-lands","water-reclamation","coal-minerals","conservation-policy"]],
    ["indian", "Indian lands", ["indian-lands"]],
    ["civil", "Civil service", ["civil-service"]],
    ["gov", "Running the government", ["government-administration","congress","copyright","ceremonial","statehood","labor-business"]],
    ["military", "Army, Navy and lighthouses", ["military-naval","lighthouses"]],
    ["territories", "Canal Zone and island territories", ["canal-zone","insular-territories"]],
    ["foreign", "Foreign affairs and trade", ["foreign-affairs","trade-reciprocity"]],
    ["other", "Not yet sorted", []]
  ];
  const GROUP_OF = {}; GROUPS.forEach(([g, , cs]) => cs.forEach(c => GROUP_OF[c] = g));
  const TYPES = { executive_order: "Executive order", proclamation: "Proclamation", unnumbered_order: "Unnumbered order" };
  const TYPES_PLURAL = { executive_order: "Executive orders", proclamation: "Proclamations", unnumbered_order: "Unnumbered orders" };
  const SIG = { 1: "Individual action", 2: "Routine", 3: "Substantive", 4: "Notable", 5: "Landmark" };
  const ACTIONS = { "amend-rules": "amend rules" };

  async function get(path) {
    if (!cache.has(path)) cache.set(path, fetch(API + path).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }));
    return cache.get(path);
  }
  function esc(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
  function fmtDate(iso, opts = {}) {
    if (!iso) return "Date not known";
    const [y, m, d] = iso.split("-").map(Number);
    if (!m) return String(y);
    if (!d) return `${MONTHS[m - 1]} ${y}`;
    if (opts.short) return `${MONTHS[m - 1].slice(0, 3)}. ${d}, ${y}`.replace("May.", "May").replace("Jun.", "June").replace("Jul.", "July").replace("Sep.", "Sept.");
    return `${MONTHS[m - 1]} ${d}${opts.noYear ? "" : ", " + y}`;
  }
  function param(name) { return new URLSearchParams(location.search).get(name); }
  function slug(s) { return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
  function catLabel(c) { return CATS[c] || c.replace(/-/g, " "); }
  function groupOf(cats) { return (cats && cats.length && GROUP_OF[cats[0]]) || "other"; }
  // Keep links inside this copy of the site (local preview, staging) instead of jumping to the live domain.
  function localize(html) { return String(html).split(BASE + "/").join(""); }
  // Minimal inline Markdown for short notes: escape, then **bold**, *italic*.
  function inlineMd(s) {
    return esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|[^\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)/g, "$1<em>$2</em>");
  }
  function docHref(id) { return `document.html?id=${encodeURIComponent(id)}`; }

  function tagsHTML(c, opts = {}) {
    const t = (c.categories || []).map(x => `<li><a href="index.html?category=${encodeURIComponent(x)}">${esc(catLabel(x))}</a></li>`);
    const s = (c.states || []).slice(0, opts.maxStates || 4).map(x => `<li><a class="st" href="index.html?state=${encodeURIComponent(slug(x))}">${esc(x)}</a></li>`);
    if ((c.states || []).length > (opts.maxStates || 4)) s.push(`<li><span class="st">+${c.states.length - (opts.maxStates || 4)} more</span></li>`);
    return t.length || s.length ? `<ul class="tags">${t.join("")}${s.join("")}</ul>` : "";
  }

  function rowHTML(c) {
    const color = `var(--g-${groupOf(c.categories)})`;
    const typeLine = c.type === "executive_order" ? `EO ${esc(c.number || "")}` : c.type === "proclamation" ? (c.number ? `Proc. ${esc(c.number)}` : "Proclamation") : "Unnumbered";
    const sub = [c.type === "executive_order" ? "Executive order" : c.type === "proclamation" ? (c.number ? "" : "Not in numbered series") : "Lord's list",
                 c.duplicate_of ? "Duplicate entry" : ""].filter(Boolean).join(" · ");
    const summary = c.summary && c.summary !== c.title ? `<p>${esc(c.summary)}</p>` : "";
    return `<li style="border-left-color:${color}"><div class="meta-row"><span class="d">${esc(fmtDate(c.date, { short: true }))}</span><span class="t">${typeLine}${sub ? `<small>${esc(sub)}</small>` : ""}</span></div>
      <div><a class="ti" href="${docHref(c.id)}">${esc(c.title)}</a>${summary}${tagsHTML(c)}</div></li>`;
  }

  function textHTML(t) {
    if (!t || !t.paragraphs || !t.paragraphs.length) return "";
    const kind = { statutes_digitization: "Machine digitization of the printed Statutes at Large", wikisource_transcription: "Volunteer transcription from Wikisource", collated: "Collated against the printed page" }[t.kind] || "Transcription";
    const ok = t.verified === true || t.kind === "collated";
    const prov = ok
      ? `<p class="prov ok"><b>${esc(kind)}.</b> ${esc(t.source || "")}${t.collated_against ? ` Checked against ${esc(t.collated_against)}.` : ""}${t.note ? `<br><span class="small">${esc(t.note)}</span>` : ""}</p>`
      : `<p class="prov"><b>${esc(kind)}. Not yet verified.</b> ${esc(t.note || "This text has not been checked against the printed original.")}${/before quoting/i.test(t.note || "") ? "" : " Check the printed page before quoting."}</p>`;
    let h = `<div class="doctext">${prov}<div class="body">${t.paragraphs.map(p => `<p>${esc(p)}</p>`).join("")}`;
    if (t.signed || t.place_date) h += `<p class="sig">${esc(t.signed || "")}${t.place_date ? `<br>${esc(t.place_date)}` : ""}</p>`;
    h += `</div>`;
    if (t.marginal_notes && t.marginal_notes.length) h += `<details><summary>Margin notes printed beside the text</summary><ul>${t.marginal_notes.map(n => `<li>${esc(n)}</li>`).join("")}</ul></details>`;
    if (t.notes) h += `<p class="small">${esc(t.notes)}</p>`;
    return h + `</div>`;
  }

  function citationsHTML(d) {
    const c = d.citations || {}, out = [];
    if (c.statutes) {
      const s = c.statutes;
      out.push(`<li><b>Statutes at Large</b>${esc(s.cite || `${s.volume} Stat. ${s.page}`)}${s.table_title ? `<br><span class="small">Listed as “${esc(s.table_title)}”</span>` : ""}${s.page_image ? `<br><a href="${esc(s.page_image)}" target="_blank" rel="noopener">See the printed page (PDF, GovInfo)</a>` : ""}</li>`);
    }
    if (c.app && c.app.url) out.push(`<li><b>American Presidency Project</b><a href="${esc(c.app.url)}" target="_blank" rel="noopener">Proclamation ${esc(c.app.number)} at UC Santa Barbara</a></li>`);
    if (c.wikisource && c.wikisource.url) out.push(`<li><b>Wikisource</b><a href="${esc(c.wikisource.url)}" target="_blank" rel="noopener">${esc(decodeURIComponent(c.wikisource.url.split("/wiki/")[1] || "Transcription").replace(/_/g, " "))}</a>${c.wikisource.printed_source ? `<br><span class="small">Printed source: ${esc(c.wikisource.printed_source)}</span>` : ""}</li>`);
    if (c.lord) {
      const l = c.lord;
      out.push(`<li><b>Lord's List and Index (1943)</b>Clifford L. Lord, ed., <i>List and Index of Presidential Executive Orders: Unnumbered Series</i>, no. ${esc(l.number)}${l.page ? `, p. ${esc(l.page)}` : ""}${l.citations ? `<br><span class="small">Lord cites: ${esc(l.citations)}</span>` : ""}</li>`);
    }
    out.push(`<li><b>On trlibrary.com</b><a href="https://www.trlibrary.com/tr/presidency/executive-actions/action?id=${encodeURIComponent(d.id)}">This action on the Library's website</a></li>`);
    if (d.title_source) out.push(`<li><b>Title</b>${/^Corrected/.test(d.title_source) ? "Corrected by the Library; see the note on the title" : `As given by ${esc(d.title_source)}`}</li>`);
    return out.length ? `<ul class="cites">${out.join("")}</ul>` : `<p class="small">No published citation yet.</p>`;
  }

  const REL = { enlarges: "Enlarges", enlarged_by: "Enlarged by", reduces: "Reduces", reduced_by: "Reduced by", modifies: "Modifies",
    modified_by: "Modified by", revokes: "Revokes", revoked_by: "Revoked by", restores: "Restores", restored_by: "Restored by",
    renames: "Renames", renamed_by: "Renamed by", amends: "Amends", amended_by: "Amended by", supersedes: "Replaces",
    superseded_by: "Replaced by", implements: "Carries out", implemented_by: "Carried out by", same_subject: "Same subject" };
  const TODAY_REL = { origin: "Began with this document", part: "Includes land set aside here", renamed: "Renamed", absorbed_into: "Later absorbed into",
    abolished: "No longer exists", transferred: "Transferred" };
  const KIND = { national_park: "National park", national_monument: "National monument", national_forest: "National forest",
    national_grassland: "National grassland", wildlife_refuge: "Wildlife refuge", state_park: "State park", indian_reservation: "Reservation",
    military_installation: "Military installation", lighthouse: "Lighthouse", other: "" };

  function pointHTML(p) {
    if (typeof p === "string") return `<li>${esc(p)}</li>`;
    const meta = [p.date ? fmtDate(p.date) : "", p.source && p.source !== "research entry" ? p.source : ""].filter(Boolean).join(" · ");
    return `<li>${esc(p.text)}${meta ? ` <span class="src">${esc(meta)}</span>` : ""}</li>`;
  }
  function byDate(a, b) { return String(a.date || "9999").localeCompare(String(b.date || "9999")); }

  function impactHTML(d) {
    const i = d.impact || {}, rel = d.related || [];
    if (!Object.keys(i).length && !rel.length) return "";
    let h = `<section class="impact"><h2>What happened next</h2>`;
    if ((i.today || []).length) {
      h += `<h3>Where it stands today</h3><ul class="today">${i.today.map(t => `<li><a href="then-and-now.html#${slug(t.name)}"><b>${esc(t.name)}</b></a>
        <span class="small">${esc([KIND[t.kind] || "", TODAY_REL[t.relation] || "", t.state || ""].filter(Boolean).join(" · "))}</span>
        ${t.note ? `<br>${esc(t.note)}` : ""}${t.source && t.source !== "research entry" ? ` <span class="src">${esc(t.source)}</span>` : ""}</li>`).join("")}</ul>`;
    }
    const atTime = [...(i.reception || []).map(x => ({ ...x, _k: "r" })), ...(i.political_impact || [])].sort(byDate);
    if (atTime.length) h += `<h3>At the time</h3><ul class="points">${atTime.map(pointHTML).join("")}</ul>`;
    const later = [...(i.legacy || []), ...(i.later_actions || [])].sort(byDate);
    if (later.length) h += `<h3>In the years after</h3><ul class="points">${later.map(pointHTML).join("")}</ul>`;
    if (rel.length) h += `<h3>Connected documents</h3><ul class="related">${rel.map(r => `<li><span class="rel">${esc(REL[r.relation] || r.relation)}</span>
        <a href="${docHref(r.id)}">${esc(r.label)}</a>${r.date ? `, ${esc(fmtDate(r.date))}` : ""}<br><span class="small">${esc(r.title || "")}${r.note ? ` — ${esc(r.note)}` : ""}</span></li>`).join("")}</ul>`;
    if ((i.uncertain || []).length) h += `<div class="stillbox"><b>Still being researched</b><ul>${i.uncertain.map(pointHTML).join("")}</ul></div>`;
    return h + `</section>`;
  }

  function renderDocument(d) {
    const color = `var(--g-${groupOf(d.categories)})`;
    const dateLine = d.date ? (d.date.length === 7 ? `${fmtDate(d.date)} <span class="small">(the day is not recorded)</span>` : esc(fmtDate(d.date))) : "Date not known";
    let h = `<article class="card" style="border-top-color:${color}">
      <p class="kicker">${esc(d.label)}</p>
      <div class="date">${dateLine}</div>
      <h1 class="doc-title">${esc(d.title)}</h1>`;
    if (d.duplicate_of_ref) {
      const o = d.duplicate_of_ref;
      h += `<p class="dnote"><b>Same document as <a href="${docHref(o.id)}">${esc(o.label)}</a>.</b> This entry in Lord's list of unnumbered orders turns out to describe ${esc(o.label)}${o.date ? ` (${esc(fmtDate(o.date))})` : ""}. It is kept here as a cross-reference and is not counted separately.</p>`;
    }
    if (d.summary) h += `<p class="summary">${esc(d.summary)}</p>`;
    else if (d.lord_description && d.lord_description !== d.title) h += `<p class="summary">${esc(d.lord_description)}</p>`;
    h += tagsHTML(d, { maxStates: 20 });
    const facts = [];
    if (d.action) facts.push(["Action", esc((ACTIONS[d.action] || d.action).replace(/^./, m => m.toUpperCase()))]);
    if (d.significance) facts.push(["Weight", `${esc(SIG[d.significance] || "")} <span class="small">(${d.significance} of 5)</span>`]);
    if (d.places && d.places.length) facts.push(["Places", d.places.map(p => esc(p.name) + (p.state ? ` <span class="small">${esc(p.state)}</span>` : "")).join("; ")]);
    if (d.people && d.people.length) facts.push(["People", d.people.map(p => esc(typeof p === "string" ? p : p.name)).join("; ")]);
    if (d.signed_as) facts.push(["Signed", esc(d.signed_as)]);
    if (d.countersigned_by && d.countersigned_by.name) facts.push(["Countersigned", `${esc(d.countersigned_by.name)}${d.countersigned_by.role ? `, ${esc(d.countersigned_by.role)}` : ""}`]);
    if (facts.length) h += `<dl class="facts">${facts.map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join("")}</dl>`;
    for (const n of d.title_notes || []) h += `<p class="dnote"><b>About the title.</b> ${esc(n)}</p>`;
    for (const n of d.date_notes || []) h += `<p class="dnote"><b>About the date.</b> ${esc(n)}</p>`;
    if (d.numbering_note) h += `<p class="dnote"><b>About the number.</b> ${esc(d.numbering_note)}</p>`;
    if (d.duplicates && d.duplicates.length) h += `<p class="dnote"><b>Also listed by Lord.</b> ${d.duplicates.map(x => `<a href="${docHref(x.id)}">${esc(x.label)}</a>${x.date ? `, dated ${esc(fmtDate(x.date))}` : ""}`).join("; ")}, describes this same document.</p>`;
    if (d.reconciliation_note_html) h += `<details class="dnote"><summary><b>${d.reconciliation === "numbered_duplicate" ? "How the match was made" : "Research note on this entry"}</b></summary><p style="margin:6px 0 0">${localize(d.reconciliation_note_html)}</p></details>`;

    h += impactHTML(d);
    h += `<h2>The text</h2>`;
    h += d.has_text ? textHTML(d.text)
      : `<p class="notext">${d.duplicate_of_ref ? "See the numbered order for the text." : "No transcription of this document is available here yet."}${(d.citations?.statutes?.page_image) ? ` The printed page is linked under Sources.` : ""}</p>`;
    if (d.prev || d.next) {
      h += `<nav class="daynav" aria-label="Previous and next documents">`;
      if (d.prev) h += `<a href="${docHref(d.prev.id)}">← ${esc(d.prev.label)}<span>${esc(fmtDate(d.prev.date))}</span></a>`;
      if (d.next) h += `<a class="nx" href="${docHref(d.next.id)}">${esc(d.next.label)} →<span>${esc(fmtDate(d.next.date))}</span></a>`;
      h += `</nav>`;
    }
    return h + `</article>`;
  }

  function storyCard(s) {
    const yrs = s.date_start ? (s.date_end && s.date_end.slice(0, 4) !== s.date_start.slice(0, 4) ? `${s.date_start.slice(0, 4)}–${s.date_end.slice(0, 4)}` : s.date_start.slice(0, 4)) : "";
    return `<article class="scard"><span class="yr">${esc(yrs)}</span><a class="ti" href="story.html?n=${s.number}">${esc(s.title)}</a>${s.dek ? `<p>${esc(s.dek)}</p>` : ""}
      <span class="small">${s.document_count ? `${s.document_count} document${s.document_count === 1 ? "" : "s"}` : "Background story"}${(s.theme_labels || []).length ? ` · ${esc(s.theme_labels.slice(0, 2).join(", "))}` : ""}</span></article>`;
  }

  return { API, BASE, get, esc, fmtDate, param, slug, catLabel, groupOf, localize, inlineMd, docHref, tagsHTML, rowHTML,
           renderDocument, citationsHTML, storyCard, impactHTML, pointHTML, KIND, TODAY_REL, MONTHS, CATS, GROUPS, TYPES, TYPES_PLURAL, SIG };
})();
