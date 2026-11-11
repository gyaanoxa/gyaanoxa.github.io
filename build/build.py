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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pages import no_dashes, small, srcset, ver  # noqa: E402
import links  # noqa: E402

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
    """The channel's RSS feed. YouTube sometimes answers 404/500 to unknown user agents, so retry with a browser one."""
    data, last = None, None
    for ua in (UA["User-Agent"], "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/130.0 Safari/537.36", "Mozilla/5.0"):
        for _ in range(2):
            try:
                with urllib.request.urlopen(urllib.request.Request(FEED, headers={"User-Agent": ua}), timeout=30) as r:
                    data = r.read()
                break
            except Exception as ex:
                last = ex
        if data:
            break
    if not data:
        raise last
    root = ET.fromstring(data)
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        stats = e.find("m:group/m:community/m:statistics", NS)
        out.append({"id": vid, "title": e.findtext("a:title", namespaces=NS),
                    "published": e.findtext("a:published", namespaces=NS)[:10],
                    "views": int(stats.get("views")) if stats is not None else 0})
    return out


def read_channel_pages():
    """Backup when the RSS feed is down: the channel's Videos and Shorts tabs (ytInitialData). No view counts or dates
    there, so a new video gets today's date; known videos keep theirs."""
    hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/130.0 Safari/537.36", "Accept-Language": "hi"}
    today = datetime.now(timezone.utc).date().isoformat()
    out = []

    def walk(o, kind):
        if isinstance(o, dict):
            if kind == "short" and "shortsLockupViewModel" in o:
                s = o["shortsLockupViewModel"]
                vid = s.get("onTap", {}).get("innertubeCommand", {}).get("reelWatchEndpoint", {}).get("videoId")
                title = s.get("overlayMetadata", {}).get("primaryText", {}).get("content")
                if vid and title:
                    out.append({"id": vid, "title": title, "published": today, "views": 0, "kind": "short"})
            if kind == "video" and "lockupViewModel" in o:
                lk = o["lockupViewModel"]
                title = lk.get("metadata", {}).get("lockupMetadataViewModel", {}).get("title", {}).get("content")
                if lk.get("contentId") and title and lk.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO":
                    out.append({"id": lk["contentId"], "title": title, "published": today, "views": 0, "kind": "video"})
            for x in o.values():
                walk(x, kind)
        elif isinstance(o, list):
            for x in o:
                walk(x, kind)

    for tab, kind in (("videos", "video"), ("shorts", "short")):
        try:
            h = urllib.request.urlopen(urllib.request.Request(f"https://www.youtube.com/@Gyaanoxa/{tab}", headers=hdr),
                                       timeout=30).read().decode("utf-8")
            walk(json.JSONDecoder().raw_decode(h[h.index("{", h.index("ytInitialData")):])[0], kind)
        except Exception as ex:
            print(f"channel {tab} page failed:", ex)
    return out


def pic(v):
    """The picture a card shows: our own Short cover (assets/covers) or YouTube's."""
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
SIZES_SHORT = "(max-width: 760px) 42vw, 190px"
SIZES_DOC = "(max-width: 760px) 92vw, 380px"
SIZES_FEAT = "(max-width: 760px) 92vw, 760px"
PLAY = '<span class="play"><svg><use href="#i-play"/></svg></span>'


def doc_card(v, featured=False):
    """A full video: picture and title open YouTube; the footer has Read article + YouTube / Facebook icons."""
    hi, en = split_title(v["title"])
    yt = f"https://www.youtube.com/watch?v={e(v['id'])}"
    watch = (f'<a class="watch" href="{yt}" target="_blank" rel="noopener"><svg><use href="#i-play"/></svg>Watch the full story</a>'
             if featured else "")
    return (f'        <div class="card">\n'
            f'          <a class="thumb" href="{yt}" target="_blank" rel="noopener" aria-label="{e(hi)}"><img loading="lazy" '
            f'{srcset(pic(v), 480, SIZES_DOC if not featured else SIZES_FEAT, (720,) if featured else ())} alt="" width="960" height="540">'
            f'{NEW if v.get("new") else ""}{PLAY}</a>\n'
            f'          <div class="meta"><h3><a href="{yt}" target="_blank" rel="noopener">{e(hi)}</a></h3>'
            f'<span class="en">{e(en or "Full video")}</span>'
            f'{f"<p class=desc>{e(links.desc(v["id"], 220 if featured else 140))}</p>" if links.desc(v["id"]) else ""}'
            f'{"<ul class=hl-mini>" + "".join(f"<li>{e(h)}</li>" for h in links.highlights(v["id"])) + "</ul>" if featured and links.highlights(v["id"]) else ""}\n'
            f'          <div class="card-foot">{watch}{links.read_link(v["id"])}{links.icons(v["id"], False)}</div></div>\n'
            f'        </div>')


def short_card(v, views=True):
    """A Short as a card: picture opens YouTube (the default); the footer has its title, Read and the platform icons."""
    hi, _ = split_title(v["title"])
    count = f'<span class="views notranslate">{fmt_views(v["views"])} views</span>' if views else ""
    title = re.sub(r"^भाग\s*\d+\s*:\s*", "", hi)
    part = re.match(r"^भाग\s*(\d+)", hi)
    art = links.article(v["id"])
    return (f'        <div class="scard"><a class="short" href="https://www.youtube.com/shorts/{e(v["id"])}" target="_blank" rel="noopener" '
            f'aria-label="{e(hi)}"><img loading="lazy" {srcset(pic(v), 360, SIZES_SHORT)} alt="" width="540" height="960">'
            f'{PLAY}{count}</a>'
            f'<div class="s-foot">{f"<span class=s-k>Part {part.group(1)}</span>" if part else ""}'
            f'<a class="s-t" href="{art or "https://www.youtube.com/shorts/" + e(v["id"])}"{"" if art else " target=_blank rel=noopener"}>{e(title)}</a>'
            f'{f"<p class=s-d>{e(links.desc(v["id"], 110))}</p>" if links.desc(v["id"]) else ""}'
            f'<div class="s-links">{links.read_link(v["id"], "Read")}{links.icons(v["id"], True)}</div></div></div>')


def fmt_views(n):
    return f"{n / 1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)


def upcoming_article(u):
    """The article of an upcoming release, when it is already written: "article" in site.json, else from the label
    ("Ajatashatru · Part 2" -> ajatashatru-part-2, a full video -> <series>-full-story, "Chhath Puja" -> chhath-*)."""
    blog = ROOT / "data" / "blog"
    if u.get("article"):
        return f"/blog/{u['article']}/" if (blog / f"{u['article']}.json").exists() else ""
    name = u.get("label", "").split("·")[0].strip().lower().split(" ")[0]
    part = re.search(r"Part (\d+)", u.get("label", ""))
    if part:
        slug = f"{name}-part-{part.group(1)}"
    elif u.get("kind") == "Full video":
        slug = f"{name}-full-story"
    else:
        slug = next((f.stem for f in sorted(blog.glob(f"{name}*.json"))), "")
    return f"/blog/{slug}/" if slug and (blog / f"{slug}.json").exists() else ""


def upcoming_cards(items, now, limit=8):
    cards = []
    for u in items:
        at = datetime.fromisoformat(u["at"])
        if at < now:
            continue
        hh = at.hour % 12 or 12
        tm = f"{hh}{':%02d' % at.minute if at.minute else ''} {'PM' if at.hour >= 12 else 'AM'} IST"
        cls = " fest" if u.get("festival") else ""
        art = upcoming_article(u)
        read = f'<a class="read-a" href="{art}"><svg><use href="#i-book"/></svg>Read the story now</a>' if art else ""
        cards.append(f'''        <div class="up" data-at="{e(u["at"])}">
          <div class="date"><b>{at.day}</b><small>{MONTHS[at.month - 1]}</small></div>
          <div class="what"><div class="kind{cls}">{e(u["kind"])}</div><h3>{e(u["title"])}</h3><div class="time">{e(u["label"])} · {tm}</div>{read}</div>
        </div>''')
    return "\n".join(cards[:limit])


def page_videos(public):
    """{page url: (video, description)} for pages that show a public YouTube video (the click-to-play player loads
    YouTube only after a click, so the video sitemap tells Google which video is on which page)."""
    out = {}
    for f in sorted((ROOT / "data" / "series").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        v = public.get((d.get("full") or {}).get("id") or "")
        if v:
            out[f"/{d['slug']}/"] = (v, d.get("about_en") or d.get("title_en", ""))
    for f in sorted((ROOT / "data" / "blog").glob("*.json")):
        a = json.loads(f.read_text(encoding="utf-8"))
        v = public.get(a.get("video") or "")
        if v:
            out[f"/blog/{a['slug']}/"] = (v, a.get("description", ""))
    return out


def video_xml(item):
    if not item:
        return ""
    v, desc = item
    title = re.sub(r"\s*#\w+", "", v["title"]).strip()
    return ("<video:video>"
            f"<video:thumbnail_loc>https://i.ytimg.com/vi/{e(v['id'])}/hqdefault.jpg</video:thumbnail_loc>"
            f"<video:title>{e(title[:100])}</video:title>"
            f"<video:description>{e((desc or title)[:2000])}</video:description>"
            f"<video:player_loc>https://www.youtube.com/embed/{e(v['id'])}</video:player_loc>"
            f"<video:publication_date>{e(v['published'])}</video:publication_date>"
            "</video:video>")


def put(page, name, body):
    pat = re.compile(rf"(<!-- AUTO:{name} -->).*?(<!-- /AUTO:{name} -->)", re.S)
    if not pat.search(page):
        sys.exit(f"marker AUTO:{name} missing in index.html")
    return pat.sub(lambda m: m.group(1) + "\n" + body + "\n        " + m.group(2), page)


def no_conflicts():
    """Stop before writing anything when a merge left Git conflict markers in a page (they would go live)."""
    import subprocess
    bad = subprocess.run(["git", "grep", "-l", "-E", "^(<<<<<<< |>>>>>>> )", "--", "*.html", "*.css", "*.json", "*.py"],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
    if bad:
        sys.exit("Git conflict markers in: " + ", ".join(bad))


def main():
    no_conflicts()
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    vfile = ROOT / "data" / "videos.json"
    videos = {v["id"]: v for v in json.loads(vfile.read_text(encoding="utf-8"))}
    try:
        feed = read_feed()
    except Exception as ex:                       # keep the last good page when YouTube does not answer
        print("feed failed:", ex)
        feed = []
    for f in [] if feed else read_channel_pages():   # backup: only adds videos the site has not seen yet
        if f["id"] not in videos:
            videos[f["id"]] = f
            print("new (channel page)", f["kind"], f["id"], f["title"])
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
          <img src="assets/logo-128.webp" alt="" width="128" height="128" loading="lazy">
          <h3>Never miss a story</h3>
          <p>Subscribe on YouTube for every new story. A Short every evening, a longer video every week.</p>
          <span class="btn sm"><svg><use href="#i-yt"/></svg>Subscribe</span>
        </a>'''
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    def hero_cover(m):                            # the hero covers: newest picture, a 240 px copy for phones
        big = f"assets/s/360/covers/{m.group(1)}.webp"
        sm = small(f"assets/covers/{m.group(1)}.webp", 240)
        return (f'src="{ver(big)}" srcset="{ver(sm)} 240w, {ver(big)} 360w" '
                f'sizes="(max-width: 760px) 160px, 262px"')
    page = re.sub(r'src="assets/s/360/covers/([\w-]+)\.webp(\?v=\d+)?"( srcset="[^"]*" sizes="[^"]*")?', hero_cover, page)
    page = put(page, "docs", "\n".join(doc_card(v, i == 0) for i, v in enumerate(docs)) + "\n" + tile)
    show = site.get("show_views", False)        # view counts stay hidden until the channel is bigger
    page = put(page, "latest", "\n".join(short_card(v, show) for v in shorts[:5]))
    total = sum(v.get("views", 0) for v in allv)
    k = f"{total // 1000}K" if total >= 1000 else str(total)
    count = len(allv)
    n_art = len(list((ROOT / "data" / "blog").glob("*.json")))
    first = (f'<div class="stat"><b>{k}<em>+</em></b><span>views so far</span></div>' if show else
             f'<div class="stat"><b>{n_art}</b><span>stories to read</span></div>')
    page = re.sub(r'<span class="visits notranslate"[^>]*>', '<span class="visits notranslate" hidden'
                  + (' data-on' if show else '') + '>', page)
    page = put(page, "stats", f'''        {first}
        <div class="stat"><b>{count}</b><span>videos &amp; Shorts</span></div>
        <div class="stat"><b>{site.get("series_count", 3)}</b><span>story series</span></div>
        <div class="stat"><b>7<em> PM</em></b><span>new Short every evening</span></div>''')
    now = datetime.now(timezone.utc)
    page = put(page, "next", upcoming_cards(site.get("upcoming", []), now))
    import hubs                                   # section pages (videos, shorts, series, ...) + footer lists
    series_links, reads = hubs.footer_lists(sorted(
        (json.loads(f.read_text(encoding="utf-8")) for f in (ROOT / "data" / "series").glob("*.json")),
        key=lambda d: {"ajatashatru": 0, "ashoka": 1, "diwali": 2}.get(d["slug"], 9)))
    page = put(page, "fseries", series_links)
    page = put(page, "freads", reads)
    (ROOT / "index.html").write_text(no_dashes(page), encoding="utf-8", newline="\n")

    import pages                                  # series pages + timeline (same folder)
    import blog
    public = {v["id"]: v for v in allv}
    hub_urls = hubs.build(longs, shorts, upcoming_cards(site.get("upcoming", []), now, 40), doc_card, short_card, show,
                          (count, site.get("series_count", 3), n_art))
    urls = (["/"] + hub_urls + pages.build(public) + blog.build(public)
            + ["/privacy.html", "/terms.html"])
    cards = blog.home_cards(public)
    if cards:   # newest series stories + single stories on the home page
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        (ROOT / "index.html").write_text(no_dashes(put(home, "blog", cards)), encoding="utf-8", newline="\n")
    vids = page_videos(public)
    sm = "".join(f"  <url><loc>https://gyaanoxa.com{u}</loc><lastmod>{today}</lastmod>{video_xml(vids.get(u))}</url>\n"
                 for u in urls)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                      'xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n'
                                      + sm + "</urlset>\n", encoding="utf-8", newline="\n")
    print(f"ok: {len(longs)} videos, {len(shorts)} shorts, {total} views, feed {len(feed)}, pages {len(urls)}")


if __name__ == "__main__":
    main()
