"""The new home page (preview at /preview/): a full-width featured banner, then dense rows of cards that scroll sideways.
Built only from the site's own data (videos, articles, series, timeline, upcoming releases)."""
import json
import re
from datetime import datetime

import blog
import links
from pages import ROOT, SITE, e, page, series_url, art_url


def split_title(t):
    t = re.sub(r"\s*#\w+", "", t).strip()
    hi, _, en = t.partition(" | ")
    return hi.strip(), en.strip()


def own_pic(v):
    p = ROOT / "assets" / "covers" / f"{v['id']}.webp"
    return f"/assets/covers/{v['id']}.webp" if p.exists() else f"/assets/yt/{v['id']}.webp"


def fmt_views(n):
    return f"{n / 1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)


def target(v):
    a = links.article(v["id"])
    return (a, "") if a else (("https://www.youtube.com/shorts/" if v["kind"] == "short" else "https://www.youtube.com/watch?v=") + v["id"],
                              ' target="_blank" rel="noopener"')


def wide(v):
    hi, en = split_title(v["title"])
    href, tgt = target(v)
    return (f'<a class="k-w" href="{e(href)}"{tgt}><span class="im"><img loading="lazy" src="{e(own_pic(v))}" alt="" width="640" height="360"></span>'
            f'<b>{e(hi)}</b><small>{e(en or "Full video")}</small></a>')


def tall(v, views=True):
    hi, en = split_title(v["title"])
    hi = re.sub(r"^भाग\s*\d+\s*:\s*", "", hi)
    href, tgt = target(v)
    chip = f'<i class="vw">{fmt_views(v.get("views", 0))} views</i>' if views and v.get("views") else ""
    return (f'<a class="k-t" href="{e(href)}"{tgt}><span class="im"><img loading="lazy" src="{e(own_pic(v))}" alt="" width="360" height="640">{chip}</span>'
            f'<b>{e(hi)}</b></a>')


def article_card(a, public):
    src, _ = blog.thumb(a, public)
    kind = "Full story" if not a.get("part") or a.get("part") == 0 else f'Part {a["part"]}'
    mins = max(1, round(blog.words(a) / 180))
    return (f'<a class="k-w" href="{art_url(a["slug"])}"><span class="im"><img loading="lazy" src="{e(src)}" alt="" width="640" height="360">'
            f'<i class="vw">{mins} min read</i></span><b>{e(blog.head_title(a["title"]))}</b><small>{e(kind)}</small></a>')


def series_card(d, public):
    full = d.get("full") or {}
    img = ROOT / "assets" / "s" / "series" / f'{d["slug"]}-720.webp'
    src = f'/assets/s/series/{d["slug"]}-720.webp' if img.exists() else f'/assets/yt/{full.get("id", "")}.webp'
    parts = len(d.get("parts", []))
    return (f'<a class="k-s" href="{series_url(d["slug"])}"><img loading="lazy" src="{e(src)}" alt="" width="720" height="450">'
            f'<i class="vw">{parts} parts + full video</i><span class="tx"><b>{e(d["title_hi"])}</b><small>{e(d["title_en"])}</small></span></a>')


def rail(title, more_href, more_text, cards, cls=""):
    more = '<a href="' + more_href + '">' + e(more_text) + "</a>" if more_href else ""
    return ('<section class="rw ' + cls + '"><div class="rw-h"><h2>' + e(title) + "</h2>"
            '<div class="rw-a">' + more +
            '<button type="button" class="rl" aria-label="Scroll left">&#8249;</button>'
            '<button type="button" class="rr" aria-label="Scroll right">&#8250;</button></div></div>'
            '<div class="rail">' + cards + "</div></section>")


JS = """
  document.querySelectorAll('.rw').forEach(function (rw) {
    var r = rw.querySelector('.rail');
    rw.querySelector('.rl').addEventListener('click', function () { r.scrollBy({left: -r.clientWidth * 0.85, behavior: 'smooth'}); });
    rw.querySelector('.rr').addEventListener('click', function () { r.scrollBy({left: r.clientWidth * 0.85, behavior: 'smooth'}); });
  });
"""


def build(longs, shorts, allv, site, now, show):
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    public = {v["id"]: v for v in allv}
    arts = blog.load_all()
    feat = next((v for v in longs if v["id"] == site.get("featured")), None) or (longs[0] if longs else None)
    # ---- billboard ----
    bb = ""
    if feat:
        hi, en = split_title(feat["title"])
        href, tgt = target(feat)
        yt = f'https://www.youtube.com/watch?v={feat["id"]}'
        d = links.desc(feat["id"], 190)
        ups = [u for u in site.get("upcoming", []) if u.get("at", "") > now.astimezone().isoformat()][:3]
        nxt = ""
        tag = re.compile(r"\s*#\w+")
        for u in ups:
            try:
                dt = datetime.fromisoformat(u["at"])
                day = str(dt.day) + " " + dt.strftime("%b") + ", " + dt.strftime("%I %p").lstrip("0")
            except ValueError:
                day = ""
            nxt += "<span><em>" + e(day) + "</em><b>" + e(tag.sub("", u.get("title", ""))) + "</b><small>" + e(u.get("label", "")) + "</small></span>"
        read = '<a class="btn ghost" href="' + e(href) + '">Read the article</a>' if href.startswith("/") else ""
        about = "<p>" + e(d) + "</p>" if d else ""
        nxt_html = '<div class="bb-next"><p>Coming next</p>' + nxt + "</div>" if nxt else ""
        bb = ('<section class="bb"><img src="' + e(own_pic(feat)) + '" alt="" fetchpriority="high"><div class="bb-in">'
              '<span class="chip-k">Featured documentary</span><h1>' + e(hi) + '</h1><p class="en">' + e(en) + "</p>" + about +
              '<div class="acts"><a class="btn" href="' + yt + '" target="_blank" rel="noopener">&#9654; Watch the full story</a>' + read +
              "</div></div>" + nxt_html + "</section>")
    # ---- rows ----
    series = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "series").glob("*.json"))]
    order = {"dharti": 0, "bindusara": 1, "ajatashatru": 2, "ashoka": 3, "diwali": 4}
    series.sort(key=lambda s: order.get(s["slug"], 9))
    def has_pic(a):
        return "og." not in blog.thumb(a, public)[0]
    newest_arts = sorted(arts.values(), key=lambda a: (has_pic(a), a.get("written") or "", a["slug"]), reverse=True)[:20]
    tl = json.loads((ROOT / "data" / "timeline.json").read_text(encoding="utf-8"))
    eras = ""
    for ev in sorted(tl["events"], key=lambda x: x["year"]):
        l = ev.get("link", "")
        if l.startswith("/") and (ROOT / "data" / "series" / (l.strip("/") + ".json")).exists():
            h = series_url(l.strip("/"))
        elif l in public:
            h = ("https://www.youtube.com/shorts/" if ev.get("kind") == "short" else "https://www.youtube.com/watch?v=") + l
        else:
            h = "/timeline/"
        eras += (f'<a class="k-e" href="{e(h)}"><em>{e(ev["label"])}</em><b>{e(ev["title"])}</b><small>{e(ev["en"])}</small></a>')
    quiz = ""
    for d in series:
        n = len(d.get("quiz", []))
        if n:
            quiz += f'<a class="k-q" href="{series_url(d["slug"])}#quiz"><i>{n}</i><b>{e(d["title_hi"])}</b><small>{e(d["title_en"])}</small></a>'
    popular = sorted(shorts, key=lambda v: v.get("views", 0), reverse=True)[:14]
    rows = [
        rail("Documentaries", "/videos/", "All videos", "".join(wide(v) for v in longs)),
        rail("Story series, part by part", "/series/", "All series", "".join(series_card(d, public) for d in series), "r-series"),
        rail("Latest Shorts", "/shorts/", "All Shorts", "".join(tall(v, show) for v in shorts[:16]), "r-tall"),
        rail("Most watched", "/shorts/", "All Shorts", "".join(tall(v, show) for v in popular), "r-tall"),
        rail("Read the stories", "/blog/", "All articles", "".join(article_card(a, public) for a in newest_arts)),
        rail("Indian history, in order", "/timeline/", "Full timeline", eras, "r-era"),
        rail("Test yourself", "", "", quiz, "r-quiz"),
    ]
    sub = ('<section class="sub-strip"><div><b>Never miss a story</b><span>A new Short every evening at 7 PM IST, a longer video every week.</span></div>'
           '<a class="btn" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener">Subscribe on YouTube</a></section>')
    body = f'<div class="h2">{bb}{"".join(rows)}{sub}</div>'
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "Gyaanoxa", "url": SITE + "/preview/"}
    head = ('  <meta name="robots" content="noindex, nofollow">\n  <link rel="stylesheet" href="/home2.css">\n')
    out = ROOT / "preview"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(page("Gyaanoxa preview: new home page | Gyaanoxa", "A preview of the new Gyaanoxa home page.", "/preview/",
                                         SITE + "/assets/og.jpg", body, ld, index, JS, head), encoding="utf-8", newline="\n")
    return []
