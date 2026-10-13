/*! Theodore Roosevelt's Executive Orders and Proclamations — page embed for trlibrary.com
 * Theodore Roosevelt Presidential Library | MIT
 *
 * Renders the index, single actions, stories and Then and Now inside host pages, with links that stay on the host site.
 *
 *   <div data-ea-view="index" data-base="/tr/presidency/executive-actions"></div>
 *   <script src="https://executiveactions.labs.trlibrary.com/embed/executive-actions.js" defer></script>
 *
 * Views (data-ea-view):
 *   index         searchable, filterable list of every action (filters sync to the URL)
 *   action        one action, chosen by ?id=proc-563 in the page URL
 *   stories       every story, grouped by subject
 *   story         one story, chosen by ?n=22 in the page URL
 *   then-and-now  present-day places that trace to a Roosevelt action
 *   featured      the landmark actions (data-limit="12")
 * data-base is the host path the pages live under. The pages it links to:
 *   {base} (index) · {base}/action?id= · {base}/stories · {base}/story?n= · {base}/then-and-now
 * data-api overrides the API (default: the published one, or data-api on the script tag).
 * data-meta="off" stops the action and story views from setting the page title, description and canonical link.
 */
(() => {
  const SCRIPT = document.currentScript;
  const SITE = SCRIPT && SCRIPT.src ? new URL("../", SCRIPT.src).href : "https://executiveactions.labs.trlibrary.com/";
  const LABS = "https://executiveactions.labs.trlibrary.com";
  const API_DEFAULT = (SCRIPT && SCRIPT.dataset.api) || new URL("api/v1/", SITE).href;
  const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const CATS = { "forests": "Forests", "monuments": "National monuments", "wildlife": "Wildlife and bird reservations",
    "public-lands": "Public lands", "indian-lands": "Indian lands", "water-reclamation": "Water and reclamation",
    "coal-minerals": "Coal and minerals", "conservation-policy": "Conservation policy", "military-naval": "Military and naval",
    "lighthouses": "Lighthouses", "civil-service": "Civil service", "government-administration": "Government administration",
    "canal-zone": "Panama Canal Zone", "insular-territories": "Island territories", "foreign-affairs": "Foreign affairs",
    "trade-reciprocity": "Trade and reciprocity", "copyright": "Copyright", "ceremonial": "Ceremonial", "congress": "Congress",
    "statehood": "Statehood", "labor-business": "Labor and business" };
  const TYPES = { executive_order: "Executive order", proclamation: "Proclamation", unnumbered_order: "Unnumbered order" };
  const SIG = { 1: "Individual action", 2: "Routine", 3: "Substantive", 4: "Notable", 5: "Landmark" };
  const REL = { enlarges: "Enlarges", enlarged_by: "Enlarged by", reduces: "Reduces", reduced_by: "Reduced by", modifies: "Modifies",
    modified_by: "Modified by", revokes: "Revokes", revoked_by: "Revoked by", restores: "Restores", restored_by: "Restored by",
    renames: "Renames", renamed_by: "Renamed by", amends: "Amends", amended_by: "Amended by", supersedes: "Replaces",
    superseded_by: "Replaced by", implements: "Carries out", implemented_by: "Carried out by", same_subject: "Same subject" };
  const TODAY_REL = { origin: "Began with this action", part: "Includes land set aside here", renamed: "Renamed",
    absorbed_into: "Later absorbed into", abolished: "No longer exists", transferred: "Transferred" };
  const KIND = { national_park: "National park", national_monument: "National monument", national_forest: "National forest",
    national_grassland: "National grassland", wildlife_refuge: "Wildlife refuge", state_park: "State park",
    indian_reservation: "Reservation", military_installation: "Military installation", lighthouse: "Lighthouse", other: "" };
  const TEXT_KIND = { statutes_digitization: "Machine reading of the printed Statutes at Large",
    wikisource_transcription: "Volunteer transcription from Wikisource", collated: "Checked against the printed page" };

  const cache = new Map();
  const get = (api, path) => {
    const url = api + path;
    if (!cache.has(url)) cache.set(url, fetch(url).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }));
    return cache.get(url);
  };
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const slug = s => String(s).toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const fmt = (iso, short) => {
    if (!iso) return "Date not known";
    const [y, m, d] = iso.split("-").map(Number);
    if (!m) return String(y);
    if (!d) return `${MONTHS[m - 1]} ${y}`;
    const mon = short ? ({ 5: "May", 6: "June", 7: "July", 9: "Sept." }[m] || MONTHS[m - 1].slice(0, 3) + ".") : MONTHS[m - 1];
    return `${mon} ${d}, ${y}`;
  };
  const param = n => new URLSearchParams(location.search).get(n);
  const byDate = (a, b) => String(a.date || "9999").localeCompare(String(b.date || "9999"));

  const CSS = `
  .ea{--ea-night:#092A4D;--ea-green:#1B4532;--ea-sand:#E6E2D7;--ea-sand2:#F3F1EB;--ea-accent:#E7805D;--ea-ink:#25282A;--ea-muted:#4A4F52;
    color:var(--ea-ink);font-size:17px;line-height:1.6}
  .ea *{box-sizing:border-box}
  .ea a{color:var(--ea-green);text-decoration:underline;text-underline-offset:2px}
  .ea a:hover{color:var(--ea-night)}
  .ea h1,.ea h2,.ea h3{color:var(--ea-night);line-height:1.2}
  .ea .ea-kick{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ea-muted);margin:0 0 4px}
  .ea .ea-date{font-size:20px;font-weight:700;color:var(--ea-night);margin:0}
  .ea h1.ea-title{font-size:clamp(28px,4vw,42px);margin:6px 0 14px}
  .ea .ea-summary{font-size:20px;line-height:1.5;margin:0 0 14px}
  .ea .ea-small{font-size:14px;line-height:1.45;color:var(--ea-muted)}
  .ea .ea-tags{display:flex;flex-wrap:wrap;gap:6px;list-style:none;margin:0 0 14px;padding:0}
  .ea .ea-tags a,.ea .ea-tags span{display:inline-block;font-size:13px;font-weight:600;background:var(--ea-sand);color:var(--ea-night);border-radius:999px;padding:3px 10px;text-decoration:none}
  .ea .ea-facts{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:6px 16px;margin:14px 0;font-size:15px}
  .ea .ea-facts dt{font-weight:700;color:var(--ea-muted)} .ea .ea-facts dd{margin:0}
  @media (max-width:560px){.ea .ea-facts{grid-template-columns:1fr;gap:0}.ea .ea-facts dd{margin-bottom:8px}}
  .ea .ea-note{margin:14px 0 0;padding:10px 14px;background:var(--ea-sand2);border-left:3px solid var(--ea-accent);border-radius:4px;font-size:15px}
  .ea .ea-sec{margin-top:34px}
  .ea .ea-sec>h2{font-size:clamp(24px,3vw,32px);margin:0 0 10px}
  .ea .ea-sec h3{font-size:14px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin:22px 0 8px}
  .ea .ea-points{list-style:none;margin:0;padding:0}
  .ea .ea-points li{padding:8px 0 8px 14px;border-left:2px solid var(--ea-sand);margin:0 0 6px}
  .ea .ea-points.today li{border-left-color:var(--ea-night)}
  .ea .ea-src{font-size:13px;color:var(--ea-muted)} .ea .ea-src:before{content:"— "}
  .ea .ea-rel{display:inline-block;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;background:var(--ea-sand);color:var(--ea-night);border-radius:3px;padding:0 6px;margin-right:6px}
  .ea .ea-still{margin:20px 0 0;padding:12px 16px;background:#EEF2F6;border-left:4px solid var(--ea-night);border-radius:4px;font-size:15px}
  .ea .ea-still ul{margin:6px 0 0;padding-left:20px}
  .ea .ea-prov{font-size:14px;background:#FFF6D6;border-left:4px solid #D9A400;padding:10px 14px;margin:0 0 14px}
  .ea .ea-prov.ok{background:#EAF4EB;border-left-color:#3A7D44}
  .ea .ea-text p{margin:0 0 12px;max-width:68ch;font-family:Georgia,"Times New Roman",serif}
  .ea .ea-text .ea-sig{font-variant:small-caps}
  .ea .ea-cites{list-style:none;margin:0;padding:0}
  .ea .ea-cites li{padding:10px 0;border-bottom:1px solid var(--ea-sand);font-size:15px}
  .ea .ea-cites b{display:block;font-size:13px;color:var(--ea-muted);text-transform:uppercase;letter-spacing:.05em}
  .ea .ea-nav{display:flex;justify-content:space-between;gap:12px;margin-top:28px;font-size:15px}
  .ea .ea-nav a{text-decoration:none;max-width:48%} .ea .ea-nav .nx{text-align:right;margin-left:auto}
  .ea .ea-nav span{display:block;color:var(--ea-muted);font-size:13px}
  .ea .ea-btn{display:inline-block;background:var(--ea-night);color:#fff !important;text-decoration:none !important;font-weight:700;font-size:15px;border-radius:4px;padding:9px 16px;border:0;cursor:pointer}
  .ea .ea-btn.sec{background:transparent;color:var(--ea-night) !important;border:2px solid var(--ea-night)}
  .ea .ea-filters{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px 12px;margin:0 0 14px;font-size:14px}
  .ea .ea-filters .q{grid-column:1/-1}
  .ea .ea-filters label{display:block;font-weight:700;color:var(--ea-muted);margin-bottom:3px}
  .ea .ea-filters input[type=search],.ea .ea-filters select{width:100%;font:inherit;font-size:15px;padding:8px 10px;border:1px solid #B9B3A3;border-radius:4px;background:#fff;color:var(--ea-ink)}
  .ea .ea-filters .chk{display:flex;flex-wrap:wrap;gap:14px;align-items:end;grid-column:1/-1}
  .ea .ea-filters .chk label{display:flex;gap:6px;align-items:center;font-weight:600;color:var(--ea-ink);margin:0}
  .ea .ea-bar{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 8px;font-size:15px}
  .ea .ea-linkbtn{background:none;border:0;color:var(--ea-green);text-decoration:underline;cursor:pointer;font:inherit;padding:0}
  .ea .ea-list{list-style:none;margin:0;padding:0}
  .ea .ea-list>li{display:grid;grid-template-columns:150px minmax(0,1fr);gap:4px 18px;padding:14px 0 14px 14px;border-bottom:1px solid var(--ea-sand);border-left:4px solid var(--ea-sand)}
  .ea .ea-list .d{font-weight:700;color:var(--ea-night);font-size:15px} .ea .ea-list .t{display:block;font-size:13px;color:var(--ea-muted)}
  .ea .ea-list .ti{font-weight:700;font-size:18px;line-height:1.3}
  .ea .ea-list p{margin:4px 0 6px;font-size:15px}
  .ea .ea-list .ea-tags{margin:6px 0 0}
  @media (max-width:640px){.ea .ea-list>li{grid-template-columns:1fr}}
  .ea .ea-grid{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
  .ea .ea-grid>li{background:#fff;border:1px solid var(--ea-sand);border-top:4px solid var(--ea-night);border-radius:6px;padding:14px 16px}
  .ea .ea-grid>li.gone{border-top-color:#8A8F93}
  .ea .ea-grid .nm{display:block;font-weight:700;font-size:19px;line-height:1.25;color:var(--ea-night)}
  .ea .ea-grid ul{list-style:none;margin:8px 0 0;padding:0;font-size:14px} .ea .ea-grid ul li{margin:4px 0}
  .ea .ea-grid p{margin:6px 0;font-size:15px}
  .ea .ea-group>h2{font-size:clamp(22px,3vw,30px);margin:34px 0 12px}
  .ea .ea-chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
  .ea .ea-chips button{font:inherit;font-size:14px;font-weight:600;border:1px solid var(--ea-night);background:#fff;color:var(--ea-night);border-radius:999px;padding:6px 12px;cursor:pointer}
  .ea .ea-chips button[aria-pressed=true]{background:var(--ea-night);color:#fff}
  .ea .ea-story{font-size:18px;line-height:1.7}
  .ea .ea-story h2,.ea .ea-story h3{font-size:clamp(22px,3vw,30px);margin:32px 0 10px}
  .ea .ea-story h4{font-size:20px;margin:22px 0 6px}
  .ea .ea-story p,.ea .ea-story li{max-width:70ch}
  .ea .ea-story blockquote{margin:0 0 16px;padding:10px 18px;background:var(--ea-sand2);border-left:4px solid var(--ea-green)}
  .ea .ea-loading{color:var(--ea-muted);font-size:15px}
  .ea .ea-two{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:36px}
  @media (max-width:900px){.ea .ea-two{grid-template-columns:1fr}}
  .ea .ea-aside .ea-card{background:var(--ea-sand2);border-radius:6px;padding:14px 16px;margin:0 0 14px}
  .ea .ea-aside h2{font-size:22px;margin:0 0 8px}
  `;
  function styles() {
    if (document.getElementById("ea-embed-css")) return;
    const s = document.createElement("style"); s.id = "ea-embed-css"; s.textContent = CSS; document.head.appendChild(s);
  }

  class App {
    constructor(el) {
      this.el = el;
      this.api = el.dataset.api || API_DEFAULT;
      this.base = (el.dataset.base || location.pathname.replace(/\/(action|story|stories|then-and-now)\/?$/, "")).replace(/\/$/, "");
      this.meta = el.dataset.meta !== "off";
    }
    actionUrl(id) { return `${this.base}/action?id=${encodeURIComponent(id)}`; }
    storyUrl(n) { return `${this.base}/story?n=${encodeURIComponent(n)}`; }
    placeUrl(name) { return `${this.base}/then-and-now#${slug(name)}`; }
    indexUrl(q) { return this.base + (q ? `?${q}` : ""); }
    paint(html) { this.el.innerHTML = `<div class="ea">${html}</div>`; }
    fail(msg) { this.paint(`<p class="ea-loading">${esc(msg)}</p>`); }

    setMeta(title, desc, canonicalQuery) {
      if (!this.meta) return;
      document.title = `${title} | Theodore Roosevelt Presidential Library`;
      const set = (sel, attr, val) => { let m = document.head.querySelector(sel); if (!m) { m = document.createElement("meta"); const [k, v] = attr; m.setAttribute(k, v); document.head.appendChild(m); } m.setAttribute("content", val); };
      if (desc) {
        set('meta[name="description"]', ["name", "description"], desc);
        set('meta[property="og:description"]', ["property", "og:description"], desc);
        set('meta[name="twitter:description"]', ["name", "twitter:description"], desc);
      }
      set('meta[property="og:title"]', ["property", "og:title"], title);
      set('meta[name="twitter:title"]', ["name", "twitter:title"], title);
      const url = location.origin + location.pathname + canonicalQuery;
      set('meta[property="og:url"]', ["property", "og:url"], url);
      let c = document.head.querySelector('link[rel="canonical"]');
      if (!c) { c = document.createElement("link"); c.rel = "canonical"; document.head.appendChild(c); }
      c.href = url;
    }

    tags(d, max = 5) {
      const c = (d.categories || []).map(x => `<li><a href="${this.indexUrl("category=" + encodeURIComponent(x))}">${esc(CATS[x] || x)}</a></li>`);
      const s = (d.states || []).slice(0, max).map(x => `<li><a href="${this.indexUrl("state=" + encodeURIComponent(slug(x)))}">${esc(x)}</a></li>`);
      return c.length || s.length ? `<ul class="ea-tags">${c.join("")}${s.join("")}</ul>` : "";
    }
    row(c) {
      const num = c.type === "executive_order" ? `EO ${esc(c.number || "")}` : c.type === "proclamation" ? (c.number ? `Proc. ${esc(c.number)}` : "Proclamation") : "Unnumbered order";
      const summary = c.summary && c.summary !== c.title ? `<p>${esc(c.summary)}</p>` : "";
      return `<li><div><span class="d">${esc(fmt(c.date, true))}</span><span class="t">${num}${c.duplicate_of ? " · listed twice" : ""}</span></div>
        <div><a class="ti" href="${this.actionUrl(c.id)}">${esc(c.title)}</a>${summary}${this.tags(c, 3)}</div></li>`;
    }

    // ---------------------------------------------------------------- index
    async index() {
      const [docs, meta] = await Promise.all([get(this.api, "documents.json"), get(this.api, "index.json")]);
      const years = [...new Set(docs.map(d => (d.date || "").slice(0, 4)).filter(Boolean))].sort();
      const states = [...new Set(docs.flatMap(d => d.states || []))].sort();
      const cats = (meta.categories || []).map(c => c.slug).filter(s => docs.some(d => (d.categories || []).includes(s)));
      const opt = (v, l) => `<option value="${esc(v)}">${esc(l)}</option>`;
      this.paint(`
        <form class="ea-filters" role="search" onsubmit="return false">
          <div class="q"><label for="ea-q">Search titles and summaries</label><input type="search" id="ea-q" placeholder="Try “Grand Canyon”, “Pelican Island” or “EO 1003”" autocomplete="off"></div>
          <div><label for="ea-type">Type</label><select id="ea-type">${opt("", "All types")}${Object.entries(TYPES).map(([k, v]) => opt(k, v + "s")).join("")}</select></div>
          <div><label for="ea-year">Year</label><select id="ea-year">${opt("", "All years")}${years.map(y => opt(y, y)).join("")}</select></div>
          <div><label for="ea-cat">Subject</label><select id="ea-cat">${opt("", "All subjects")}${cats.map(c => opt(c, CATS[c] || c)).join("")}</select></div>
          <div><label for="ea-state">State or territory</label><select id="ea-state">${opt("", "Anywhere")}${states.map(s => opt(slug(s), s)).join("")}</select></div>
          <div><label for="ea-sig">Weight</label><select id="ea-sig">${opt("", "Any")}${opt("5", "Landmark only")}${opt("4", "Notable and up")}${opt("3", "Substantive and up")}</select></div>
          <div><label for="ea-sort">Sort by</label><select id="ea-sort">${opt("date", "Date, oldest first")}${opt("-date", "Date, newest first")}${opt("sig", "Weight, biggest first")}${opt("title", "Title, A–Z")}</select></div>
          <div class="chk"><label><input type="checkbox" id="ea-impact"> Has “what happened next”</label><label><input type="checkbox" id="ea-text"> Has text</label><label><input type="checkbox" id="ea-story"> Part of a story</label></div>
        </form>
        <div class="ea-bar"><span id="ea-count" aria-live="polite"></span><button type="button" class="ea-linkbtn" id="ea-clear">Clear all filters</button></div>
        <ol class="ea-list" id="ea-list"></ol>
        <p style="text-align:center;margin-top:16px"><button type="button" class="ea-btn sec" id="ea-more" hidden>Show more</button></p>`);
      const $ = id => this.el.querySelector("#" + id);
      const F = { q: $("ea-q"), type: $("ea-type"), year: $("ea-year"), category: $("ea-cat"), state: $("ea-state"), sig: $("ea-sig"), sort: $("ea-sort"),
                  impact: $("ea-impact"), text: $("ea-text"), story: $("ea-story") };
      const p = new URLSearchParams(location.search);
      for (const [k, el] of Object.entries(F)) { const v = p.get(k); if (v != null) el.type === "checkbox" ? (el.checked = v === "1") : (el.value = v); }
      let rows = [], shown = 0;
      const render = () => {
        const q = F.q.value.trim().toLowerCase();
        const num = q.match(/^(?:eo|executive order|proc\.?|proclamation)\s*([\w½-]+)$/i);
        rows = docs.filter(d => !d.duplicate_of
          && (!F.type.value || d.type === F.type.value)
          && (!F.year.value || (d.date || "").startsWith(F.year.value))
          && (!F.category.value || (d.categories || []).includes(F.category.value))
          && (!F.state.value || (d.states || []).some(s => slug(s) === F.state.value))
          && (!F.sig.value || (d.significance || 0) >= +F.sig.value)
          && (!F.impact.checked || d.has_impact) && (!F.text.checked || d.has_text) && (!F.story.checked || (d.stories || []).length)
          && (!q || (num ? String(d.number || "").toLowerCase() === num[1].toLowerCase()
                         : `${d.title} ${d.summary || ""} ${(d.today || []).join(" ")} ${d.number || ""}`.toLowerCase().includes(q))));
        const s = F.sort.value;
        rows.sort(s === "-date" ? (a, b) => byDate(b, a) : s === "sig" ? (a, b) => (b.significance || 0) - (a.significance || 0) || byDate(a, b)
          : s === "title" ? (a, b) => a.title.localeCompare(b.title) : byDate);
        shown = 0; $("ea-list").innerHTML = ""; more();
        $("ea-count").textContent = `${rows.length.toLocaleString()} of ${docs.filter(d => !d.duplicate_of).length.toLocaleString()} actions`;
        const qs = new URLSearchParams();
        for (const [k, el] of Object.entries(F)) { if (el.type === "checkbox") { if (el.checked) qs.set(k, "1"); } else if (el.value && !(k === "sort" && el.value === "date")) qs.set(k, el.value); }
        history.replaceState(null, "", location.pathname + (qs.toString() ? "?" + qs : "") + location.hash);
      };
      const more = () => { const next = rows.slice(shown, shown + 60); shown += next.length; $("ea-list").insertAdjacentHTML("beforeend", next.map(r => this.row(r)).join("")); $("ea-more").hidden = shown >= rows.length; };
      let t; F.q.addEventListener("input", () => { clearTimeout(t); t = setTimeout(render, 150); });
      for (const el of Object.values(F)) if (el !== F.q) el.addEventListener("change", render);
      $("ea-more").addEventListener("click", more);
      $("ea-clear").addEventListener("click", () => { for (const el of Object.values(F)) el.type === "checkbox" ? (el.checked = false) : (el.value = el === F.sort ? "date" : ""); render(); });
      render();
    }

    // ---------------------------------------------------------------- action
    point(p) {
      if (typeof p === "string") return `<li>${esc(p)}</li>`;
      const m = [p.date ? fmt(p.date) : "", p.source && p.source !== "research entry" ? p.source : ""].filter(Boolean).join(" · ");
      return `<li>${esc(p.text)}${m ? ` <span class="ea-src">${esc(m)}</span>` : ""}</li>`;
    }
    impact(d) {
      const i = d.impact || {}, rel = d.related || [];
      if (!Object.keys(i).length && !rel.length) return "";
      let h = `<section class="ea-sec"><h2>What happened next</h2>`;
      if ((i.today || []).length) h += `<h3>Where it stands today</h3><ul class="ea-points today">${i.today.map(t => `<li><a href="${this.placeUrl(t.name)}"><b>${esc(t.name)}</b></a>
          <span class="ea-small">${esc([KIND[t.kind] || "", TODAY_REL[t.relation] || "", t.state || ""].filter(Boolean).join(" · "))}</span>${t.note ? `<br>${esc(t.note)}` : ""}</li>`).join("")}</ul>`;
      const now = [...(i.reception || []), ...(i.political_impact || [])].sort(byDate);
      if (now.length) h += `<h3>At the time</h3><ul class="ea-points">${now.map(x => this.point(x)).join("")}</ul>`;
      const later = [...(i.legacy || []), ...(i.later_actions || [])].sort(byDate);
      if (later.length) h += `<h3>In the years after</h3><ul class="ea-points">${later.map(x => this.point(x)).join("")}</ul>`;
      if (rel.length) h += `<h3>Connected actions</h3><ul class="ea-points">${rel.map(r => `<li><span class="ea-rel">${esc(REL[r.relation] || r.relation)}</span>
          <a href="${this.actionUrl(r.id)}">${esc(r.label)}</a>${r.date ? `, ${esc(fmt(r.date))}` : ""}<br><span class="ea-small">${esc(r.title || "")}${r.note ? ` — ${esc(r.note)}` : ""}</span></li>`).join("")}</ul>`;
      if ((i.uncertain || []).length) h += `<div class="ea-still"><b>Still being researched</b><ul>${i.uncertain.map(x => this.point(x)).join("")}</ul></div>`;
      return h + `</section>`;
    }
    text(t) {
      if (!t || !(t.paragraphs || []).length) return `<p class="ea-small">No transcription of this action is available yet.</p>`;
      const ok = t.verified === true || t.kind === "collated";
      const prov = ok ? `<p class="ea-prov ok"><b>${esc(TEXT_KIND[t.kind] || "Transcription")}.</b> ${esc(t.source || "")}${t.note ? `<br><span class="ea-small">${esc(t.note)}</span>` : ""}</p>`
        : `<p class="ea-prov"><b>${esc(TEXT_KIND[t.kind] || "Transcription")}. Not yet checked.</b> ${esc(t.note || "")} Check the printed page before quoting.</p>`;
      return `${prov}<div class="ea-text">${t.paragraphs.map(p => `<p>${esc(p)}</p>`).join("")}${t.signed || t.place_date ? `<p class="ea-sig">${esc(t.signed || "")}${t.place_date ? `<br>${esc(t.place_date)}` : ""}</p>` : ""}</div>`;
    }
    cites(d) {
      const c = d.citations || {}, out = [];
      if (c.statutes) out.push(`<li><b>Statutes at Large</b>${esc(c.statutes.cite || "")}${c.statutes.page_image ? ` · <a href="${esc(c.statutes.page_image)}" target="_blank" rel="noopener">see the printed page</a>` : ""}</li>`);
      if (c.app && c.app.url) out.push(`<li><b>American Presidency Project</b><a href="${esc(c.app.url)}" target="_blank" rel="noopener">Proclamation ${esc(c.app.number)} at UC Santa Barbara</a></li>`);
      if (c.wikisource && c.wikisource.url) out.push(`<li><b>Wikisource</b><a href="${esc(c.wikisource.url)}" target="_blank" rel="noopener">Transcription</a>${c.wikisource.printed_source ? `<br><span class="ea-small">Printed source: ${esc(c.wikisource.printed_source)}</span>` : ""}</li>`);
      if (c.lord) out.push(`<li><b>Lord's List and Index (1943)</b>Clifford L. Lord, ed., <i>List and Index of Presidential Executive Orders: Unnumbered Series</i>, no. ${esc(c.lord.number)}${c.lord.page ? `, p. ${esc(c.lord.page)}` : ""}</li>`);
      out.push(`<li><b>Data</b><a href="${LABS}/document.html?id=${encodeURIComponent(d.id)}" target="_blank" rel="noopener">This action in the open dataset</a> · <a href="${this.api}documents/${encodeURIComponent(d.id)}.json" target="_blank" rel="noopener">JSON</a></li>`);
      return `<ul class="ea-cites">${out.join("")}</ul>`;
    }
    async action() {
      const id = param("id");
      if (!id) return this.paint(`<p>Pick an action from the <a href="${this.indexUrl()}">full list</a>.</p>`);
      let d;
      try { d = await get(this.api, `documents/${encodeURIComponent(id)}.json`); }
      catch (e) { return this.paint(`<p>No action with the id “${esc(id)}” was found. <a href="${this.indexUrl()}">Search the full list</a>.</p>`); }
      if (d.duplicate_of && d.duplicate_of_ref) {
        const o = d.duplicate_of_ref;
        return this.paint(`<p class="ea-kick">${esc(d.label)}</p><h1 class="ea-title">${esc(d.title)}</h1>
          <p class="ea-note">This entry in Lord's list of unnumbered orders describes <a href="${this.actionUrl(o.id)}">${esc(o.label)}</a>${o.date ? ` of ${esc(fmt(o.date))}` : ""}. It is kept as a cross-reference and is not counted separately.</p>`);
      }
      this.setMeta(`${d.title} (${d.label}, ${fmt(d.date)})`, d.summary || d.title, `?id=${encodeURIComponent(d.id)}`);
      const facts = [];
      if (d.signed_as) facts.push(["Signed", esc(d.signed_as)]);
      if (d.countersigned_by && d.countersigned_by.name) facts.push(["Countersigned", esc(d.countersigned_by.name) + (d.countersigned_by.role ? `, ${esc(d.countersigned_by.role)}` : "")]);
      if (d.significance) facts.push(["Weight", esc(SIG[d.significance] || "")]);
      if ((d.places || []).length) facts.push(["Places", d.places.map(p => esc(p.name) + (p.state ? ` <span class="ea-small">${esc(p.state)}</span>` : "")).join("; ")]);
      if ((d.people || []).length) facts.push(["People", d.people.map(p => esc(typeof p === "string" ? p : p.name)).join("; ")]);
      let notes = "";
      for (const n of d.title_notes || []) notes += `<p class="ea-note"><b>About the title.</b> ${esc(n)}</p>`;
      for (const n of d.date_notes || []) notes += `<p class="ea-note"><b>About the date.</b> ${esc(n)}</p>`;
      if (d.numbering_note) notes += `<p class="ea-note"><b>About the number.</b> ${esc(d.numbering_note)}</p>`;
      const stories = (d.story_refs || []).map(s => `<div class="ea-card"><a href="${this.storyUrl(s.number)}"><b>${esc(s.title)}</b></a>${s.dek ? `<p class="ea-small" style="margin:6px 0 0">${esc(s.dek)}</p>` : ""}</div>`).join("");
      const dayLink = d.day_by_day ? `<div class="ea-card"><b>That day</b><p class="ea-small" style="margin:6px 0 8px">What else was Roosevelt doing on ${esc(fmt(d.date))}?</p><a class="ea-btn sec" href="${esc(d.day_by_day)}" target="_blank" rel="noopener">See the day in Day by Day</a></div>` : "";
      const cite = `Theodore Roosevelt Presidential Library, “${d.label}: ${d.title},” ${fmt(d.date)}, ${location.origin + location.pathname}?id=${d.id}.`;
      this.paint(`<div class="ea-two"><div>
          <p class="ea-kick">${esc(d.label)}</p>
          <p class="ea-date">${esc(fmt(d.date))}</p>
          <h1 class="ea-title">${esc(d.title)}</h1>
          ${d.summary ? `<p class="ea-summary">${esc(d.summary)}</p>` : ""}
          ${this.tags(d, 20)}
          ${facts.length ? `<dl class="ea-facts">${facts.map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join("")}</dl>` : ""}
          ${notes}
          ${this.impact(d)}
          <section class="ea-sec"><h2>The text</h2>${this.text(d.text)}</section>
          <nav class="ea-nav" aria-label="Previous and next actions">
            ${d.prev ? `<a href="${this.actionUrl(d.prev.id)}">← ${esc(d.prev.label)}<span>${esc(fmt(d.prev.date))}</span></a>` : ""}
            ${d.next ? `<a class="nx" href="${this.actionUrl(d.next.id)}">${esc(d.next.label)} →<span>${esc(fmt(d.next.date))}</span></a>` : ""}
          </nav>
        </div>
        <aside class="ea-aside">
          ${stories ? `<h2>The story</h2>${stories}` : ""}
          ${dayLink}
          <h2>Sources</h2>${this.cites(d)}
          <h2 style="margin-top:18px">Cite this page</h2><p class="ea-small">${esc(cite)}</p>
          <p><a href="${this.indexUrl()}">← All of Roosevelt's executive actions</a></p>
        </aside></div>`);
    }

    // ---------------------------------------------------------------- stories
    async stories() {
      const list = await get(this.api, "stories/index.json");
      const byTheme = {};
      for (const s of list) (byTheme[(s.themes || [])[0] || "other"] ||= []).push(s);
      const order = Object.keys(byTheme).sort((a, b) => byTheme[b].length - byTheme[a].length);
      const span = s => s.date_start ? (s.date_end && s.date_end.slice(0, 4) !== s.date_start.slice(0, 4) ? `${s.date_start.slice(0, 4)}–${s.date_end.slice(0, 4)}` : s.date_start.slice(0, 4)) : "";
      this.paint(order.map(t => `<section class="ea-group"><h2>${esc(CATS[t] || "Other stories")}</h2><ul class="ea-grid">${byTheme[t].sort(byDate).map(s =>
        `<li><span class="ea-small">${esc(span(s))}</span><a class="nm" href="${this.storyUrl(s.number)}" style="text-decoration:none">${esc(s.title)}</a>${s.dek ? `<p>${esc(s.dek)}</p>` : ""}
         <span class="ea-small">${s.document_count ? `${s.document_count} action${s.document_count === 1 ? "" : "s"}` : "Background"}</span></li>`).join("")}</ul></section>`).join(""));
    }
    async story() {
      const n = param("n");
      if (!n) return this.paint(`<p>Pick a story from <a href="${this.base}/stories">the stories</a>.</p>`);
      let s;
      try { s = await get(this.api, `stories/${encodeURIComponent(n)}.json`); }
      catch (e) { return this.paint(`<p>That story was not found. <a href="${this.base}/stories">See all stories</a>.</p>`); }
      this.setMeta(s.title, s.dek, `?n=${s.number}`);
      const seen = new Set(), today = [];
      for (const [id, imp] of Object.entries(s.documents_impact || {})) for (const t of imp.today || [])
        if (t.name && !seen.has(t.name) && t.relation !== "abolished") { seen.add(t.name); today.push({ t, id }); }
      const docs = (s.documents || []);
      this.paint(`<div class="ea-two"><div>
          <p class="ea-kick">Story</p>
          ${s.date_start ? `<p class="ea-date">${esc(fmt(s.date_start))}${s.date_end && s.date_end !== s.date_start ? ` – ${esc(fmt(s.date_end))}` : ""}</p>` : ""}
          <h1 class="ea-title">${esc(s.title)}</h1>
          ${s.dek ? `<p class="ea-summary">${esc(s.dek)}</p>` : ""}
          <div class="ea-story">${s.html}</div>
          ${(s.open_questions || []).length ? `<div class="ea-still"><b>Still being researched</b><ul>${s.open_questions.map(q => `<li>${esc(q)}</li>`).join("")}</ul></div>` : ""}
        </div>
        <aside class="ea-aside">
          ${today.length ? `<h2>Where things stand today</h2><ul class="ea-points today">${today.slice(0, 30).map(({ t }) => `<li><a href="${this.placeUrl(t.name)}">${esc(t.name)}</a><br><span class="ea-small">${esc([KIND[t.kind] || "", TODAY_REL[t.relation] || ""].filter(Boolean).join(" · "))}</span></li>`).join("")}</ul>` : ""}
          ${docs.length ? `<h2 style="margin-top:18px">The actions</h2><ul class="ea-points">${docs.slice(0, 80).map(x => `<li><a href="${this.actionUrl(x.id)}">${esc(x.label)}</a>, ${esc(fmt(x.date, true))}<br><span class="ea-small">${esc(x.title)}</span></li>`).join("")}</ul>${docs.length > 80 ? `<p class="ea-small">And ${docs.length - 80} more.</p>` : ""}` : ""}
          <p><a href="${this.base}/stories">← All stories</a></p>
        </aside></div>`);
      this.rewriteLinks(this.el.querySelector(".ea-story"));
    }
    rewriteLinks(root) {
      if (!root) return;
      for (const a of root.querySelectorAll("a[href]")) {
        let u; try { u = new URL(a.getAttribute("href"), LABS + "/"); } catch (e) { continue; }
        if (u.origin !== LABS && u.origin !== new URL(SITE).origin) continue;
        const f = u.pathname.split("/").pop();
        if (f === "document.html" && u.searchParams.get("id")) a.href = this.actionUrl(u.searchParams.get("id"));
        else if (f === "story.html" && u.searchParams.get("n")) a.href = this.storyUrl(u.searchParams.get("n"));
        else if (f === "then-and-now.html") a.href = `${this.base}/then-and-now${u.hash}`;
        else if (f === "stories.html") a.href = `${this.base}/stories`;
        else if (f === "index.html" || f === "") a.href = this.indexUrl(u.search.slice(1));
      }
    }

    // ---------------------------------------------------------------- then and now
    async thenNow() {
      const d = await get(this.api, "then-and-now/index.json");
      let kind = location.hash.startsWith("#k-") ? location.hash.slice(3) : "all";
      const gone = p => p.documents.every(x => x.relation === "abolished");
      const card = p => `<li id="${esc(p.slug)}" class="${gone(p) ? "gone" : ""}"><span class="nm">${esc(p.name)}</span>
        ${p.states.length ? `<span class="ea-small">${esc(p.states.join(", "))}</span>` : ""}
        <ul>${p.documents.map(x => `<li><b>${esc(TODAY_REL[x.relation] || "")}</b>${x.district ? ` (${esc(x.district)})` : ""}: <a href="${this.actionUrl(x.id)}">${esc(x.label)}</a>, ${esc(fmt(x.date, true))}${x.note ? `<br><span class="ea-small">${esc(x.note)}</span>` : ""}</li>`).join("")}</ul></li>`;
      const draw = () => {
        const groups = d.kinds.filter(k => kind === "all" || k.kind === kind);
        this.paint(`<div class="ea-chips" role="group" aria-label="Show">${[{ kind: "all", label: "Everything", count: d.count }, ...d.kinds].map(k =>
            `<button type="button" data-k="${k.kind}" aria-pressed="${k.kind === kind}">${esc(k.label)} (${k.count})</button>`).join("")}</div>
          ${groups.map(k => `<section class="ea-group"><h2>${esc(k.label)}</h2><ul class="ea-grid">${d.places.filter(p => p.kind === k.kind).sort((a, b) => gone(a) - gone(b)).map(card).join("")}</ul></section>`).join("")}`);
        this.el.querySelector(".ea-chips").addEventListener("click", e => {
          const b = e.target.closest("button"); if (!b) return;
          kind = b.dataset.k; history.replaceState(null, "", location.pathname + location.search + (kind === "all" ? "" : "#k-" + kind)); draw();
        });
      };
      draw();
      if (location.hash && !location.hash.startsWith("#k-")) { const t = document.getElementById(decodeURIComponent(location.hash.slice(1))); if (t) setTimeout(() => t.scrollIntoView({ block: "center" }), 50); }
    }

    // ---------------------------------------------------------------- featured
    async featured() {
      const docs = await get(this.api, "documents.json");
      const limit = +(this.el.dataset.limit || 12);
      const rows = docs.filter(d => !d.duplicate_of && d.significance === 5).sort(byDate).slice(0, limit);
      this.paint(`<ol class="ea-list">${rows.map(r => this.row(r)).join("")}</ol>
        <p style="margin-top:14px"><a class="ea-btn" href="${this.indexUrl("sig=5")}">See every landmark action</a></p>`);
    }

    async run() {
      const v = this.el.dataset.eaView;
      this.paint(`<p class="ea-loading">Loading…</p>`);
      try {
        if (v === "index") await this.index();
        else if (v === "action") await this.action();
        else if (v === "stories") await this.stories();
        else if (v === "story") await this.story();
        else if (v === "then-and-now") await this.thenNow();
        else if (v === "featured") await this.featured();
        else this.fail(`Unknown view “${v}”.`);
      } catch (e) {
        this.fail("The list of Roosevelt's executive actions could not be loaded just now. Please try again in a moment.");
      }
    }
  }

  function boot() { styles(); document.querySelectorAll("[data-ea-view]:not([data-ea-ready])").forEach(el => { el.setAttribute("data-ea-ready", "1"); new App(el).run(); }); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
