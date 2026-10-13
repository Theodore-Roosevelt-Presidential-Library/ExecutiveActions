"""Fetch Wikisource transcriptions of Roosevelt's executive orders (public-domain U.S. government texts).

Reads the link list on Wikisource's "Author:Theodore Roosevelt/Executive orders" page, then pulls the
wikitext of every existing "Executive Order N" page in batches of 50 through the MediaWiki API.
Output: data/sources/wikisource_eo.json  {page_title: {"wikitext": ..., "revid": ..., "fetched": date}}
Re-run to refresh; parse with pipeline/parse_wikisource.py.
"""
import json
import time
import urllib.parse
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://en.wikisource.org/w/api.php"
UA = "TRPL-ExecutiveActions/1.0 (Theodore Roosevelt Presidential Library research dataset)"


def get(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(15 * (attempt + 1))


def main():
    links = get({"action": "parse", "page": "Author:Theodore_Roosevelt/Executive_orders", "prop": "links"})["parse"]["links"]
    titles = [l["title"] for l in links if l.get("exists") and l["title"].startswith("Executive Order")]
    out = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        data = get({"action": "query", "prop": "revisions", "rvprop": "content|ids", "rvslots": "main",
                    "titles": "|".join(batch), "redirects": "1"})
        redirects = {r["to"]: r["from"] for r in data["query"].get("redirects", [])}
        for p in data["query"]["pages"]:
            if "revisions" not in p:
                continue
            rev = p["revisions"][0]
            out[redirects.get(p["title"], p["title"])] = {"wikitext": rev["slots"]["main"]["content"], "revid": rev["revid"],
                                                          "page": p["title"], "fetched": date.today().isoformat()}
        time.sleep(1)
    path = ROOT / "data/sources/wikisource_eo.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(path, "w"), ensure_ascii=False, indent=0)
    print(len(titles), "linked pages;", len(out), "fetched ->", path)


if __name__ == "__main__":
    main()
