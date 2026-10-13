/*! Theodore Roosevelt's Executive Orders and Proclamations — widgets | Theodore Roosevelt Presidential Library | MIT
 *
 * <script src="https://executiveactions.labs.trlibrary.com/widgets/executiveactions.js" defer></script>
 *
 * <trpl-action id="proc-563"></trpl-action>                         one document, as a card
 * <trpl-actions-on-this-day count="3"></trpl-actions-on-this-day>   signed on today's date (date="MM-DD" to fix one)
 * <trpl-actions-list category="forests" state="Arizona" year="1908" limit="10"></trpl-actions-list>
 * <trpl-story n="2"></trpl-story>                                   teaser card for a story
 * <trpl-then-and-now kind="wildlife_refuge" state="Florida" limit="8"></trpl-then-and-now>
 *                                                                   places today that trace to a Roosevelt document
 *   kind = national_park | national_monument | national_forest | wildlife_refuge | lighthouse | other (default: all)
 *
 * Optional attributes on every widget:
 *   theme="light|dark|auto"   (default light; auto follows the visitor's system setting)
 *   data-api="https://…/api/v1/"   (default: the published API; also read from the script tag)
 *   cta="off"                 hide the "Plan your visit" link
 * trpl-actions-list also takes type="executive_order|proclamation|unnumbered_order", sort="date|significance",
 *   min="1–5" (lowest weight to include) and heading="…".
 * Fonts inherit the page's --ea-display / --ea-serif / --ea-sans CSS variables when set.
 */
(() => {
  const SCRIPT = document.currentScript;
  const LIVE = "https://executiveactions.labs.trlibrary.com/";
  const SITE = SCRIPT && SCRIPT.src ? new URL("../", SCRIPT.src).href : LIVE;
  const DEFAULT_API = (SCRIPT && SCRIPT.dataset.api) || new URL("api/v1/", SITE).href;
  const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const CATS = { "forests": "Forests", "monuments": "National monuments", "wildlife": "Wildlife", "public-lands": "Public lands",
    "indian-lands": "Indian lands", "water-reclamation": "Water and reclamation", "coal-minerals": "Coal and minerals",
    "conservation-policy": "Conservation policy", "military-naval": "Military and naval", "lighthouses": "Lighthouses",
    "civil-service": "Civil service", "government-administration": "Government administration", "canal-zone": "Panama Canal Zone",
    "insular-territories": "Island territories", "foreign-affairs": "Foreign affairs", "trade-reciprocity": "Trade and reciprocity",
    "copyright": "Copyright", "ceremonial": "Ceremonial", "congress": "Congress", "statehood": "Statehood", "labor-business": "Labor and business" };
  const TYPE_PLURAL = { executive_order: "executive orders", proclamation: "proclamations", unnumbered_order: "unnumbered orders" };
  const cache = new Map();
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const fmt = (iso, noYear) => {
    if (!iso) return "Date not known";
    const [y, m, d] = iso.split("-").map(Number);
    if (!d) return `${MONTHS[m - 1]} ${y}`;
    return `${MONTHS[m - 1]} ${d}${noYear ? "" : ", " + y}`;
  };
  const pad = n => String(n).padStart(2, "0");
  const todayMD = () => { const t = new Date(); return `${pad(t.getMonth() + 1)}-${pad(t.getDate())}`; };
  function get(api, path) {
    const url = api + path;
    if (!cache.has(url)) cache.set(url, fetch(url).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }));
    return cache.get(url);
  }
  const CSS = `
    :host { display: block; --night: #092A4D; --ink: #25282A; --muted: #4A4F52; --line: #D1CCBD; --bg: #fff; --chip: #E6E2D7;
      --accent: #E7805D; --link: #1B4532; --kick: #092A4D;
      --display: var(--ea-display, "Dharma Gothic E", "Oswald", "Arial Narrow", sans-serif);
      --serif: var(--ea-serif, "ITC Clearface", "Lora", Georgia, serif);
      --sans: var(--ea-sans, "Frutiger Next", "Source Sans 3", system-ui, sans-serif); }
    :host([theme=dark]) { --ink: #F3F1EB; --muted: #C9D3DF; --line: #24496F; --bg: #092A4D; --chip: #163E68; --link: #8FC895; --kick: #fff; --accent: #FC924E; }
    @media (prefers-color-scheme: dark) {
      :host([theme=auto]) { --ink: #F3F1EB; --muted: #C9D3DF; --line: #24496F; --bg: #092A4D; --chip: #163E68; --link: #8FC895; --kick: #fff; --accent: #FC924E; }
    }
    :host([hidden]) { display: none; }
    .w { background: var(--bg); color: var(--ink); font: 16px/1.55 var(--serif); padding: 18px 20px; border-top: 5px solid var(--accent); }
    .kicker { font: 700 24px/1 var(--display); text-transform: uppercase; color: var(--kick); margin: 0 0 10px; letter-spacing: .01em; }
    .lab { font: 700 13px/1.3 var(--sans); text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
    ul { list-style: none; margin: 0; padding: 0; }
    li.it { padding: 10px 0; border-top: 1px solid var(--line); }
    li.it:first-child { border-top: 0; padding-top: 0; }
    .h { font-weight: 700; font-size: 17px; line-height: 1.35; color: var(--ink); text-decoration: none; }
    a.h:hover, a.h:focus-visible { text-decoration: underline; }
    .big { font-size: 20px; }
    .s { margin: 4px 0 0; }
    .m { font: 13px/1.4 var(--sans); color: var(--muted); margin-top: 3px; }
    .yr { font: 700 20px/1 var(--display); color: var(--accent); margin-right: 8px; }
    .tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
    .tags span { font: 600 12px/1.3 var(--sans); background: var(--chip); color: var(--ink); padding: 2px 8px; border-radius: 99px; }
    .story { margin-top: 10px; font: 600 14px/1.4 var(--sans); }
    .story a, .foot a { color: var(--link); }
    .foot { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: 12px; font: 600 13px var(--sans); }
    .src { font: 12px/1.4 var(--sans); color: var(--muted); margin-top: 8px; }
    :focus-visible { outline: 3px solid #FC924E; outline-offset: 2px; }`;

  class Base extends HTMLElement {
    static get observedAttributes() { return ["id", "n", "date", "count", "theme", "category", "state", "year", "type", "limit", "sort", "min", "data-api", "api"]; }
    connectedCallback() {
      if (!this.shadowRoot) this.attachShadow({ mode: "open" });
      let api = this.getAttribute("data-api") || this.getAttribute("api") || DEFAULT_API;
      this.api = api.endsWith("/") ? api : api + "/";
      this.site = this.api.replace(/api\/v1\/$/, "");
      this.render().catch(() => this.paint(`<p class="m">This list of Theodore Roosevelt's executive orders and proclamations can't be shown right now.</p>`));
    }
    attributeChangedCallback(n, o, v) { if (this.shadowRoot && o !== v) this.connectedCallback(); }
    paint(inner) {
      const cta = this.getAttribute("cta") === "off" ? "" : `<a href="https://www.trlibrary.com/visit" target="_top">Plan your visit</a>`;
      this.shadowRoot.innerHTML = `<style>${CSS}</style><div class="w" part="card">${inner}<div class="foot"><a href="${this.site}" target="_top">Explore all of Roosevelt's orders</a>${cta}</div><div class="src">Theodore Roosevelt Presidential Library</div></div>`;
    }
    docLink(id) { return `${this.site}document.html?id=${encodeURIComponent(id)}`; }
    storyLink(n) { return `${this.site}story.html?n=${encodeURIComponent(n)}`; }
    item(x, opts = {}) {
      const summary = x.summary && x.summary !== x.title ? `<p class="s">${esc(x.summary)}</p>` : "";
      return `<li class="it">${opts.year && x.date ? `<span class="yr">${x.date.slice(0, 4)}</span>` : ""}<a class="h" href="${this.docLink(x.id)}" target="_top">${esc(x.title)}</a>
        ${opts.summary === false ? "" : summary}<div class="m">${esc(x.label || "")}${x.date ? ` · ${esc(fmt(x.date))}` : ""}</div></li>`;
    }
  }

  class Action extends Base {
    async render() {
      const id = (this.getAttribute("id") || this.getAttribute("doc") || "").toLowerCase();
      const x = await get(this.api, `documents/${encodeURIComponent(id)}.json`);
      const tags = [...(x.categories || []).map(c => CATS[c] || c), ...(x.states || []).slice(0, 3)];
      const st = (x.story_refs || [])[0];
      this.paint(`<p class="lab">${esc(x.label)} · ${esc(fmt(x.date))}</p>
        <p style="margin:6px 0 0"><a class="h big" href="${this.docLink(x.id)}" target="_top">${esc(x.title)}</a></p>
        ${x.summary ? `<p class="s">${esc(x.summary)}</p>` : ""}
        ${tags.length ? `<div class="tags">${tags.map(t => `<span>${esc(t)}</span>`).join("")}</div>` : ""}
        ${st ? `<p class="story">The story: <a href="${this.storyLink(st.number)}" target="_top">${esc(st.title)}</a></p>` : ""}`);
    }
  }

  class OnThisDay extends Base {
    async render() {
      const fixed = this.getAttribute("date");
      const n = Math.max(1, Math.min(12, +(this.getAttribute("count") || 3)));
      let md = fixed || todayMD(), o = await get(this.api, `on-this-day/${md}.json`), note = "";
      if (!o.count && !fixed) {
        // Nothing signed on today's date: look ahead a few days for the next date with documents.
        const t = new Date();
        for (let i = 1; i <= 14 && !o.count; i++) {
          const d = new Date(t.getFullYear(), t.getMonth(), t.getDate() + i);
          md = `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
          o = await get(this.api, `on-this-day/${md}.json`).catch(() => ({ count: 0, documents: [] }));
        }
        note = o.count ? `<p class="m" style="margin:-4px 0 10px">Nothing was signed on today's date. Coming up next:</p>` : "";
      }
      const [m, d] = md.split("-").map(Number);
      const picked = o.documents.slice(0, n).sort((a, b) => a.date.localeCompare(b.date));
      const more = o.count > n ? `<p class="m">${o.count - n} more signed on ${MONTHS[m - 1]} ${d} in other years.</p>` : "";
      this.paint(`<p class="kicker">Signed on ${MONTHS[m - 1]} ${d}</p>${note}<ul>${picked.map(x => this.item(x, { year: true })).join("") || `<li class="it m">Nothing Roosevelt signed as president carries this date.</li>`}</ul>${more}`);
    }
  }

  class List extends Base {
    async render() {
      const cat = this.getAttribute("category"), state = this.getAttribute("state"), year = this.getAttribute("year");
      const type = this.getAttribute("type"), min = +(this.getAttribute("min") || 0);
      const limit = Math.max(1, Math.min(50, +(this.getAttribute("limit") || 10)));
      const sort = this.getAttribute("sort") || (year ? "date" : "significance");
      // Fetch the narrowest list, then filter the rest here.
      let src;
      if (year) src = (await get(this.api, `years/${encodeURIComponent(year)}.json`)).documents;
      else if (cat) src = (await get(this.api, `categories/${encodeURIComponent(cat)}.json`)).documents;
      else if (state) src = (await get(this.api, `states/${slug(state)}.json`)).documents;
      else if (type) src = (await get(this.api, `types/${encodeURIComponent(type)}.json`)).documents;
      else src = (await get(this.api, "documents.json")).filter(x => !x.duplicate_of);
      let rows = src.filter(x => (!cat || (x.categories || []).includes(cat)) && (!state || (x.states || []).some(s => slug(s) === slug(state)))
        && (!year || (x.date || "").startsWith(year)) && (!type || x.type === type) && (!min || (x.significance || 0) >= min));
      const total = rows.length;
      const byDate = (a, b) => (a.date || "9").localeCompare(b.date || "9");
      rows.sort(sort === "date" ? byDate : (a, b) => (b.significance || 0) - (a.significance || 0) || byDate(a, b));
      rows = rows.slice(0, limit);
      if (sort !== "date") rows.sort(byDate);
      const what = type ? TYPE_PLURAL[type] || "documents" : "orders and proclamations";
      const base = cat ? (CATS[cat] || cat) + (type ? `: ${what}` : "") : what.replace(/^./, c => c.toUpperCase());
      const heading = this.getAttribute("heading") || base + (state ? ` in ${state}` : "") + (year ? `, ${year}` : "");
      const q = new URLSearchParams();
      if (cat) q.set("category", cat); if (state) q.set("state", slug(state)); if (year) q.set("year", year); if (type) q.set("type", type);
      const all = total > rows.length ? `<p class="m"><a href="${this.site}index.html?${q}" target="_top" style="color:var(--link)">See all ${total}</a></p>` : "";
      this.paint(`<p class="kicker">${esc(heading)}</p><ul>${rows.map(x => this.item(x)).join("") || `<li class="it m">No documents match.</li>`}</ul>${all}`);
    }
  }

  class Story extends Base {
    async render() {
      const n = this.getAttribute("n") || this.getAttribute("slug");
      const s = await get(this.api, `stories/${encodeURIComponent(n)}.json`);
      const span = s.date_start ? (s.date_end && s.date_end.slice(0, 4) !== s.date_start.slice(0, 4) ? `${s.date_start.slice(0, 4)}–${s.date_end.slice(0, 4)}` : s.date_start.slice(0, 4)) : "";
      const docs = s.documents || [];
      this.paint(`<p class="lab">Story${span ? ` · ${esc(span)}` : ""}</p>
        <p style="margin:6px 0 0"><a class="h big" href="${this.storyLink(s.number)}" target="_top">${esc(s.title)}</a></p>
        ${s.dek ? `<p class="s">${esc(s.dek)}</p>` : ""}
        ${docs.length ? `<p class="m">${docs.length === 1 ? esc(docs[0].label) : `${docs.length} documents, ${esc(docs[0].label)} and more`}</p>` : ""}
        <p class="story"><a href="${this.storyLink(s.number)}" target="_top">Read the story</a></p>`);
    }
  }

  const REL = { origin: "began with", part: "includes land from", renamed: "renamed from", absorbed_into: "absorbed",
    abolished: "no longer exists;", transferred: "transferred by" };
  class ThenNow extends Base {
    async render() {
      const kind = this.getAttribute("kind"), state = this.getAttribute("state");
      const limit = Math.max(1, Math.min(60, +(this.getAttribute("limit") || 8)));
      const d = await get(this.api, kind ? `then-and-now/${encodeURIComponent(kind)}.json` : "then-and-now/index.json");
      let ps = d.places.filter(p => !state || p.states.some(s => slug(s) === slug(state)))
        .filter(p => !p.documents.every(x => x.relation === "abolished"));
      const total = ps.length;
      ps = ps.sort((a, b) => (b.origin - a.origin) || (a.first || "9").localeCompare(b.first || "9")).slice(0, limit);
      const heading = this.getAttribute("heading") || `${kind ? d.label : "Places"} that began with Roosevelt${state ? ` in ${state}` : ""}`;
      const items = ps.map(p => { const x = p.documents[0];
        return `<li class="it"><span class="h" style="font-weight:700">${esc(p.name)}</span><br><span class="m">${esc(REL[x.relation] || "")} <a href="${this.docLink(x.id)}" target="_top" style="color:var(--link)">${esc(x.label)}</a>, ${esc(fmt(x.date))}</span></li>`; }).join("");
      const more = total > ps.length ? `<p class="m"><a href="${this.site}then-and-now.html${kind ? "#k-" + kind : ""}" target="_top" style="color:var(--link)">See all ${total}</a></p>` : "";
      this.paint(`<p class="kicker">${esc(heading)}</p><ul>${items || `<li class="it m">Nothing traced yet.</li>`}</ul>${more}`);
    }
  }

  const def = (n, c) => customElements.get(n) || customElements.define(n, c);
  def("trpl-action", Action);
  def("trpl-actions-on-this-day", OnThisDay);
  def("trpl-actions-list", List);
  def("trpl-story", Story);
  def("trpl-then-and-now", ThenNow);
})();
