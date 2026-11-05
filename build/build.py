"""Refreshes the home page from the channel's public YouTube feed (no API key).

Run by .github/workflows/update.yml every few hours, or by hand: python build/build.py
- data/videos.json   every public video seen so far (the feed only lists the latest 15; older ones are kept)
- data/site.json     hand-made settings: hidden ids, featured video, upcoming releases
- assets/yt/<id>.webp thumbnails (Shorts 540x960 from the vertical cover, videos 960x540)
- index.html         the parts between <!-- AUTO:name --> and <!-- /AUTO:name --> are rewritten
"""
import html
import io
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHANNEL = "UCFHg-SfAo30zWIBugVMwTaw"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL}"
UA = {"User-Agent": "GyaanoxaSite/1.0 (+https://gyaanoxa.com)"}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "m": "http://search.yahoo.com/mrss/"}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def get(url, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def is_short(vid):
    """YouTube answers /shorts/<id> with 200 for a Short and a redirect for a normal video."""
    opener = urllib.request.build_opener(NoRedirect)
    try:
        return opener.open(urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", headers=UA),
                           timeout=30).status == 200
    except urllib.error.HTTPError:
        return False


def read_feed():
    root = ET.fromstring(get(FEED))
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        stats = e.find("m:group/m:community/m:statistics", NS)
        out.append({"id": vid, "title": e.findtext("a:title", namespaces=NS),
                    "published": e.findtext("a:published", namespaces=NS)[:10],
                    "views": int(stats.get("views")) if stats is not None else 0})
    return out


def pic(v):
    """The picture a card shows: our own Short cover (assets/covers, added from the studio) or YouTube's."""
    own = ROOT / "assets" / "covers" / f"{v['id']}.webp"
    return f"assets/covers/{v['id']}.webp" if own.exists() else f"assets/yt/{v['id']}.webp"


def thumb(v):
    """Small WebP thumbnail next to the page (made once per video)."""
    out = ROOT / "assets" / "yt" / f"{v['id']}.webp"
    if out.exists() or (ROOT / pic(v)).exists():
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    names = ["oar2.jpg", "hqdefault.jpg"] if v["kind"] == "short" else ["maxresdefault.jpg", "hqdefault.jpg"]
    size = (540, 960) if v["kind"] == "short" else (960, 540)
    for n in names:
        try:
            im = Image.open(io.BytesIO(get(f"https://i.ytimg.com/vi/{v['id']}/{n}"))).convert("RGB")
            break
        except Exception:
            im = None
    if im is None:
        return
    tw, th = size                      # cut to the exact shape, keep the middle
    r = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - tw) // 2, (im.height - th) // 2
    im.crop((x, y, x + tw, y + th)).save(out, "WEBP", quality=80, method=6)


def split_title(t):
    t = re.sub(r"\s*#\w+", "", t).strip()
    hi, _, en = t.partition(" | ")
    return hi.strip(), en.strip()


def e(s):
    return html.escape(s, quote=True)


NEW = '<span class="tag">New</span>'
PLAY = '<span class="play"><svg><use href="#i-play"/></svg></span>'


def doc_card(v, featured=False):
    hi, en = split_title(v["title"])
    extra = ('<span class="watch"><svg><use href="#i-play"/></svg>Watch the full story</span>' if featured else "")
    return (f'        <a class="card" href="https://www.youtube.com/watch?v={e(v["id"])}" target="_blank" rel="noopener">\n'
            f'          <div class="thumb"><img loading="lazy" src="{pic(v)}" alt="" width="960" height="540">'
            f'{NEW if v.get("new") else ""}{PLAY}</div>\n'
            f'          <div class="meta"><h3>{e(hi)}</h3><span class="en">{e(en or "Full video")}</span>{extra}</div>\n'
            f'        </a>')


def short_card(v):
    hi, _ = split_title(v["title"])
    return (f'        <a class="short" href="https://www.youtube.com/shorts/{e(v["id"])}" target="_blank" rel="noopener" '
            f'aria-label="{e(hi)}"><img loading="lazy" src="{pic(v)}" alt="" width="540" height="960">'
            f'{PLAY}<span class="views notranslate">{fmt_views(v["views"])} views</span></a>')


def fmt_views(n):
    return f"{n / 1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)


def upcoming_cards(items, now):
    cards = []
    for u in items:
        at = datetime.fromisoformat(u["at"])
        if at < now:
            continue
        hh = at.hour % 12 or 12
        tm = f"{hh}{':%02d' % at.minute if at.minute else ''} {'PM' if at.hour >= 12 else 'AM'} IST"
        cls = " fest" if u.get("festival") else ""
        cards.append(f'''        <div class="up" data-at="{e(u["at"])}">
          <div class="date"><b>{at.day}</b><small>{MONTHS[at.month - 1]}</small></div>
          <div class="what"><div class="kind{cls}">{e(u["kind"])}</div><h3>{e(u["title"])}</h3><div class="time">{e(u["label"])} · {tm}</div></div>
        </div>''')
    return "\n".join(cards[:8])


def put(page, name, body):
    pat = re.compile(rf"(<!-- AUTO:{name} -->).*?(<!-- /AUTO:{name} -->)", re.S)
    if not pat.search(page):
        sys.exit(f"marker AUTO:{name} missing in index.html")
    return pat.sub(lambda m: m.group(1) + "\n" + body + "\n        " + m.group(2), page)


def main():
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    vfile = ROOT / "data" / "videos.json"
    videos = {v["id"]: v for v in json.loads(vfile.read_text(encoding="utf-8"))}
    try:
        feed = read_feed()
    except Exception as ex:                       # keep the last good page when YouTube does not answer
        print("feed failed:", ex)
        feed = []
    for f in feed:
        v = videos.get(f["id"])
        if v:
            v.update(title=f["title"], views=max(f["views"], v.get("views", 0)))
        else:
            f["kind"] = "short" if is_short(f["id"]) else "video"
            videos[f["id"]] = f
            print("new", f["kind"], f["id"], f["title"])
    allv = sorted(videos.values(), key=lambda v: v["published"], reverse=True)
    vfile.write_text(json.dumps(allv, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    hidden = set(site.get("hide", []))
    shown = [v for v in allv if v["id"] not in hidden]
    for v in shown:
        thumb(v)
    shown = [v for v in shown if (ROOT / pic(v)).exists()]
    longs = [v for v in shown if v["kind"] == "video"]
    shorts = [v for v in shown if v["kind"] == "short"]
    today = datetime.now(timezone.utc).date().isoformat()
    for v in longs + shorts:
        v["new"] = (datetime.fromisoformat(today) - datetime.fromisoformat(v["published"])).days <= 3

    feat = next((v for v in longs if v["id"] == site.get("featured")), None) or (longs[0] if longs else None)
    docs = ([feat] if feat else []) + [v for v in longs if v is not feat][:4]
    tile = '''        <a class="sub-tile" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener">
          <img src="assets/logo.webp" alt="" width="256" height="256">
          <h3>नई कहानी मिस न करें</h3>
          <p>Subscribe on YouTube and get every new story — a Short every evening, a documentary every week.</p>
          <span class="btn sm"><svg><use href="#i-yt"/></svg>Subscribe</span>
        </a>'''
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    page = put(page, "docs", "\n".join(doc_card(v, i == 0) for i, v in enumerate(docs)) + "\n" + tile)
    page = put(page, "latest", "\n".join(short_card(v) for v in shorts[:5]))
    page = put(page, "top", "\n".join(short_card(v) for v in sorted(shorts, key=lambda v: -v["views"])[:10]))
    total = sum(v.get("views", 0) for v in allv)
    k = f"{total // 1000}K" if total >= 1000 else str(total)
    count = len(allv) // 10 * 10
    page = put(page, "stats", f'''        <div class="stat"><b>{k}<em>+</em></b><span>views so far</span></div>
        <div class="stat"><b>{count}<em>+</em></b><span>videos &amp; Shorts</span></div>
        <div class="stat"><b>{site.get("series_count", 3)}</b><span>story series</span></div>
        <div class="stat"><b>7<em> PM</em></b><span>new Short every evening</span></div>''')
    now = datetime.now(timezone.utc)
    page = put(page, "next", upcoming_cards(site.get("upcoming", []), now))
    (ROOT / "index.html").write_text(page, encoding="utf-8", newline="\n")

    import pages                                  # series pages + timeline (same folder)
    urls = ["/"] + pages.build({v["id"]: v for v in allv}) + ["/privacy.html", "/terms.html", "/data-deletion.html"]
    sm = "".join(f"  <url><loc>https://gyaanoxa.com{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + sm + "</urlset>\n", encoding="utf-8", newline="\n")
    print(f"ok: {len(longs)} videos, {len(shorts)} shorts, {total} views, feed {len(feed)}, pages {len(urls)}")


if __name__ == "__main__":
    main()
