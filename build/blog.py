"""Blog: /blog/ (all articles, series-wise) and /blog/<slug>/ from data/blog/<slug>.json (written by write_articles.py).

Uses the same page shell as the series pages (pages.page). A video shows as a click-to-play player once it is public;
before that the article shows its release date.
"""
import json
import re
from pathlib import Path

import pages
from pages import SITE, e, page, when

ROOT = Path(__file__).resolve().parent.parent
SERIES_ORDER = {"ajatashatru": 0, "ashoka": 1, "diwali": 2}


READ_JS = """
  (function () {
    var bar = document.querySelector('.read-bar'), art = document.querySelector('.art');
    if (!bar || !art) return;
    var links = [].slice.call(document.querySelectorAll('.toc a'));
    function upd() {
      var r = art.getBoundingClientRect(), h = r.height - innerHeight, cur = null;
      bar.style.transform = 'scaleX(' + Math.min(1, Math.max(0, -r.top / (h > 0 ? h : 1))) + ')';
      links.forEach(function (l) { var t = document.querySelector(l.getAttribute('href')); if (t && t.getBoundingClientRect().top < 140) cur = l; });
      links.forEach(function (l) { l.classList.toggle('on', l === cur); });
    }
    addEventListener('scroll', upd, {passive: true}); upd();
  })();
"""


def load_all():
    arts = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "blog").glob("*.json"))]
    return {a["slug"]: a for a in arts}


def head_title(t):
    return re.sub(r"\s*#\w+", "", t).split(" | ")[0].strip()


def words(a):
    txt = " ".join([a.get("intro", ""), a.get("takeaway", "")] + [p for s in a["sections"] for p in s["paras"]])
    return len(txt.split())


def series_info():
    out = {}
    for f in (ROOT / "data" / "series").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        out[d["slug"]] = d
    return out


def thumb(a, public):
    if a.get("part") and a.get("video") and (ROOT / "assets" / "covers" / f"{a['video']}.webp").exists():
        return f"/assets/covers/{a['video']}.webp", "tall"
    if a.get("video") and (ROOT / "assets" / "yt" / f"{a['video']}.webp").exists():
        return f"/assets/yt/{a['video']}.webp", "wide"
    if a.get("short") and (ROOT / "assets" / "covers" / f"{a['short']}.webp").exists():
        return f"/assets/covers/{a['short']}.webp", "tall"
    if (ROOT / "assets" / "parts" / f"{a['slug']}.webp").exists():   # the part's own opening picture (from the studio)
        return f"/assets/parts/{a['slug']}.webp", "tall"
    if a.get("series"):        # a series story whose video is not public yet: its Part 1 cover
        sf = ROOT / "data" / "series" / f"{a['series']}.json"
        if sf.exists():
            for p in json.loads(sf.read_text(encoding="utf-8"))["parts"]:
                if p.get("short") and (ROOT / "assets" / "covers" / f"{p['short']}.webp").exists():
                    return f"/assets/covers/{p['short']}.webp", "tall"
    art = ROOT / "assets" / f"{a.get('series')}-art.webp"
    return (f"/assets/{a['series']}-art.webp", "tall") if a.get("series") and art.exists() else ("/assets/og.jpg", "wide")


def article_page(a, arts, public, series, index):
    slug = a["slug"]
    s = series.get(a.get("series") or "")
    vid = a.get("video")
    live = vid in public
    img, shape = thumb(a, public)
    if live and a.get("part"):
        player = (f'<div class="player tall"><button class="yt-facade" type="button" data-id="{e(vid)}" aria-label="{e(head_title(a["title"]))}">'
                  f'<img src="{e(img)}" alt="" width="540" height="960"><span class="big-play"><svg><use href="#i-play"/></svg></span></button></div>')
    elif live:
        player = pages.facade(vid, head_title(a["title"]), img)
    else:
        at = ""
        if s and a.get("part"):
            at = next((p.get("at") for p in s["parts"] if p["n"] == a["part"]), "")
        elif s:
            at = s["full"].get("at", "")
        player = (f'<div class="player soon-box"><img src="{e(img)}" alt="" width="540" height="960">'
                  f'<div><b>वीडियो — जल्द</b><span>{e(when(at)) or "Coming soon"}</span></div></div>') if at or s else ""

    crumbs = '<a href="/">Gyaanoxa</a> › <a href="/blog/">Blog</a>'
    badge = ""
    if s:
        crumbs += f' › <a href="/{e(s["slug"])}/">{e(s["title_en"])}</a>'
        badge = f"भाग {a['part']}/{a['of']}" if a.get("part") else "पूरी कहानी"
    secs = "".join(f'<h2 id="s{i}">{e(x["h2"])}</h2>' + "".join(f"<p>{e(p)}</p>" for p in x["paras"])
                   for i, x in enumerate(a["sections"], 1))
    dyk = a.get("did_you_know") or []
    if dyk:                    # one "did you know" box in the middle of the article
        mid = len(a["sections"]) // 2 + 1
        box = '<div class="dyk"><b>क्या आप जानते हैं?</b>' + "".join(f"<p>{e(t)}</p>" for t in dyk) + "</div>"
        secs = secs.replace(f'<h2 id="s{mid}">', box + f'<h2 id="s{mid}">', 1) if mid > 1 else secs + box
    dates = "".join(f"<li><b>{e(d)}</b><span>{e(t)}</span></li>" for d, t in a.get("key_dates", []))
    faq = "".join(f"<details><summary>{e(q['q'])}</summary><p>{e(q['a'])}</p></details>" for q in a.get("faq", []))
    hl = "".join(f"<li>{e(t)}</li>" for t in a.get("highlights", []))
    toc = "".join(f'<li><a href="#s{i}">{e(x["h2"])}</a></li>' for i, x in enumerate(a["sections"], 1))
    toc = f'<nav class="side-box toc"><p class="eyebrow">इस लेख में</p><ol>{toc}</ol></nav>' if toc else ""
    people = "".join(f"<li><b>{e(n)}</b><span>{e(r)}</span></li>" for n, r in a.get("people", []))
    people = f'<div class="side-box people"><p class="eyebrow">कहानी के किरदार</p><ul>{people}</ul></div>' if people else ""

    nav = pnav = ""
    related = []
    if s:
        base = s["slug"]
        items = [(f"{base}-full-story", "पूरी कहानी")] + [(f"{base}-part-{p['n']}", f"भाग {p['n']}: {p['topic']}") for p in s["parts"]]
        nav = "".join(f'<li{" class=on" if k == slug else ""}><a href="/blog/{e(k)}/">{e(t)}</a></li>'
                      for k, t in items if k in arts)
        nav = f'<aside class="side-box series-nav"><p class="eyebrow">इस सीरीज़ के लेख</p><ol>{nav}</ol><a class="more" href="/{e(base)}/">Series page · Quiz</a></aside>'
        keys = [k for k, _ in items if k in arts]
        at = keys.index(slug) if slug in keys else 0
        related = [arts[k] for k in keys[at + 1:] + keys[:at]][:3]
        if a.get("part"):
            prev_k, next_k = f"{base}-part-{a['part'] - 1}", f"{base}-part-{a['part'] + 1}"
            pn = ""
            if prev_k in arts:
                pn += f'<a class="pn" href="/blog/{e(prev_k)}/"><small>← पिछला भाग</small><b>{e(head_title(arts[prev_k]["title"]))}</b></a>'
            if next_k in arts:
                pn += f'<a class="pn next" href="/blog/{e(next_k)}/"><small>अगला भाग →</small><b>{e(head_title(arts[next_k]["title"]))}</b></a>'
            pnav = f'<div class="prevnext">{pn}</div>' if pn else ""
    if not related:
        others = [x for x in arts.values() if x["slug"] != slug and (x.get("part") or 0) == 0]
        related = sorted(others, key=lambda x: (x.get("series") == a.get("series"), x["slug"]), reverse=True)[:3]
    rel = "".join(card(x, public) for x in related)

    yt = (f'<a class="btn" href="https://www.youtube.com/{"shorts/" if a.get("part") else "watch?v="}{e(vid)}" target="_blank" rel="noopener">'
          f'<svg><use href="#i-yt"/></svg>YouTube पर देखें</a>') if live else \
        '<a class="btn" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener"><svg><use href="#i-yt"/></svg>Subscribe करें</a>'
    src = a.get("source") or {}
    mins = max(2, round(words(a) / 180))
    tags = "".join(f'<span class="tag-chip">#{e(k)}</span>' for k in a.get("keywords", []))
    en = a["title"].split(" | ")[1] if " | " in a["title"] else ""
    tall = "tall" in player or "soon-box" in player
    body = f"""  <div class="read-bar" aria-hidden="true"></div>
  <section class="art-hero">
    <div class="wrap art-top{' wide' if not tall else ''}">
      <div class="art-head">
        <p class="crumbs">{crumbs}</p>
        <div class="art-chips">{f'<span class="chip">{e(badge)}</span>' if badge else ''}<span class="chip ghost">{mins} मिनट पढ़ें</span>{f'<span class="chip ghost notranslate">{e(en)}</span>' if en else ''}</div>
        <h1>{e(head_title(a["title"]))}</h1>
        <p class="art-lead">{e(a.get("description", ""))}</p>
        {f'<div class="hl"><p class="eyebrow">इस लेख में आप जानेंगे</p><ul>{hl}</ul></div>' if hl else ''}
      </div>
      <div class="art-media">{player}</div>
    </div>
  </section>
  <section class="art-body">
    <div class="wrap art-grid">
      <article class="art">
        <p class="art-intro">{e(a.get("intro", ""))}</p>
        {secs}
        {f'<div class="kd"><h2>मुख्य तारीखें</h2><ol class="vt">{dates}</ol></div>' if dates else ''}
        {f'<h2>अक्सर पूछे जाने वाले सवाल</h2><div class="faq">{faq}</div>' if faq else ''}
        <div class="takeaway"><b>आख़िर में</b><p>{e(a.get("takeaway", ""))}</p></div>
        <p class="src">Source: <a href="{e(src.get("url", ""))}" target="_blank" rel="noopener">{e(src.get("title", ""))}</a> (Wikipedia) and the texts it cites, as researched for our video. Legends are told as legends.</p>
        {f'<div class="tags"><span>Tags</span>{tags}</div>' if tags else ''}
        <div class="actions">{yt}<a class="btn ghost" href="/blog/">सभी लेख</a></div>
        {pnav}
      </article>
      <div class="art-side">{toc}{nav}{people}</div>
    </div>
  </section>
  {f'<section class="more-reads"><div class="wrap"><div class="head"><div><p class="eyebrow">Keep reading</p><h2>आगे पढ़ें</h2></div><a class="more" href="/blog/">सभी लेख</a></div><div class="agrid">{rel}</div></div></section>' if rel else ''}"""
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": head_title(a["title"])[:110], "description": a.get("description", ""),
         "inLanguage": "hi", "datePublished": a.get("written", ""), "keywords": ", ".join(a.get("keywords", [])),
         "image": SITE + img, "url": f"{SITE}/blog/{slug}/",
         "dateModified": a.get("written", ""), "mainEntityOfPage": f"{SITE}/blog/{slug}/", "wordCount": words(a),
         "articleSection": s["title_en"] if s else "Indian History",
         "about": [{"@type": "Person", "name": n} for n, _ in a.get("people", [])][:6] or None,
         "author": {"@type": "Organization", "name": "Gyaanoxa", "url": SITE},
         "publisher": {"@type": "Organization", "name": "Gyaanoxa", "logo": {"@type": "ImageObject", "url": SITE + "/assets/icon-512.png"}}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                                            for q in a.get("faq", [])]}]}
    trail = [("Gyaanoxa", "/"), ("Blog", "/blog/")] + ([(s["title_en"], f"/{s['slug']}/")] if s else []) +         [(head_title(a["title"]), f"/blog/{slug}/")]
    ld["@graph"].append({"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": SITE + u} for i, (n, u) in enumerate(trail, 1)]})
    if not ld["@graph"][0]["about"]:
        del ld["@graph"][0]["about"]
    if live:
        v = public[vid]
        ld["@graph"].append({"@type": "VideoObject", "name": head_title(v["title"]), "description": a.get("description", ""),
                             "thumbnailUrl": [f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"], "uploadDate": v["published"],
                             "embedUrl": f"https://www.youtube-nocookie.com/embed/{vid}", "inLanguage": "hi"})
    d0 = a.get("written", "")
    head = (f'  <meta name="keywords" content="{e(", ".join(a.get("keywords", [])))}">\n'
            f'  <meta property="article:published_time" content="{e(d0)}">\n'
            f'  <meta property="article:modified_time" content="{e(d0)}">\n'
            f'  <meta property="article:section" content="{e(s["title_en"] if s else "Indian History")}">\n'
            + "".join(f'  <meta property="article:tag" content="{e(k)}">\n' for k in a.get("keywords", [])))
    return page(f"{a['title']} — Gyaanoxa", a.get("description", ""), f"/blog/{slug}/", SITE + img, body, ld, index, READ_JS, head, "article")


def card(a, public):
    img, shape = thumb(a, public)
    label = (f"भाग {a['part']}/{a['of']}" if a.get("part") else "पूरी कहानी") if a.get("series") else "लेख"
    return (f'<a class="acard {shape}" href="/blog/{e(a["slug"])}/"><div class="ac-img"><img loading="lazy" src="{e(img)}" alt=""></div>'
            f'<div class="ac-body"><span class="ac-k">{e(label)} · {max(2, round(words(a) / 180))} मिनट</span>'
            f'<h3>{e(head_title(a["title"]))}</h3><p>{e(a.get("description", ""))}</p></div></a>')


def prow(a, public):
    img, _ = thumb(a, public)
    return (f'<li><a class="prow" href="/blog/{e(a["slug"])}/"><img loading="lazy" src="{e(img)}" alt="" width="540" height="960">'
            f'<div><span class="ac-k">भाग {a["part"]} · {max(2, round(words(a) / 180))} मिनट</span>'
            f'<h3>{e(head_title(a["title"]))}</h3></div></a></li>')


def feature(a, public, s):
    img, _ = thumb(a, public)
    return (f'<a class="bfeat-card" href="/blog/{e(a["slug"])}/"><img loading="lazy" src="{e(img)}" alt="">'
            f'<div class="bf-body"><span class="chip">पूरी कहानी · {max(2, round(words(a) / 180))} मिनट</span>'
            f'<h3>{e(head_title(a["title"]))}</h3><p>{e(a.get("description", ""))}</p>'
            f'<span class="bf-go">पूरा लेख पढ़ें →</span></div></a>')


def index_page(arts, public, series, index):
    groups = []
    for sl in sorted(series, key=lambda k: SERIES_ORDER.get(k, 9)):
        s = series[sl]
        full = arts.get(f"{sl}-full-story")
        parts = [arts[k] for k in [f"{sl}-part-{p['n']}" for p in s["parts"]] if k in arts]
        if not (full or parts):
            continue
        lst = f'<ol class="plist{" many" if len(parts) > 5 else ""}">{"".join(prow(a, public) for a in parts)}</ol>'
        groups.append(f'<div class="bgroup" id="{e(sl)}"><div class="head"><div><p class="eyebrow">Series · {len(s["parts"])} parts</p>'
                      f'<h2>{e(s["title_hi"])}</h2></div><a class="more" href="/{e(sl)}/">Series page · Quiz</a></div>'
                      f'<div class="bfeat">{feature(full, public, s) if full else ""}{lst}</div></div>')
    singles = [a for a in arts.values() if not a.get("series")]
    if singles:
        groups.append('<div class="bgroup" id="stories"><div class="head"><div><p class="eyebrow">Stories</p><h2>और कहानियाँ</h2></div></div>'
                      f'<div class="agrid singles">{"".join(card(a, public) for a in singles)}</div></div>')
    total = sum(max(2, round(words(a) / 180)) for a in arts.values())
    jump = "".join(f'<a href="#{e(sl)}">{e(series[sl]["title_hi"].split(":")[0])}</a>'
                   for sl in sorted(series, key=lambda k: SERIES_ORDER.get(k, 9))) + '<a href="#stories">और कहानियाँ</a>'
    body = f"""  <section class="sp-hero blog-hero">
    <div class="wrap">
      <p class="crumbs"><a href="/">Gyaanoxa</a> › Blog</p>
      <h1>पढ़िए पूरी कहानी</h1>
      <p class="lead">हर वीडियो की कहानी, विस्तार से — वही तथ्य, वही स्रोत, साथ में मुख्य तारीखें, किरदार और सवाल-जवाब। सीरीज़ भाग-दर-भाग।</p>
      <div class="bstats"><span><b>{len(arts)}</b> लेख</span><span><b>{len(series)}</b> सीरीज़</span><span><b>{total}</b> मिनट पढ़ने को</span></div>
      <nav class="bjump">{jump}</nav>
    </div>
  </section>
  <section class="blog-list"><div class="wrap">{"".join(groups)}</div></section>"""
    ld = {"@context": "https://schema.org", "@type": "Blog", "name": "Gyaanoxa Blog", "url": f"{SITE}/blog/", "inLanguage": "hi"}
    return page("Blog — पढ़िए पूरी कहानी | Gyaanoxa", "Gyaanoxa के हर वीडियो की कहानी विस्तार से: अशोक, अजातशत्रु, दिवाली, कोहिनूर और भारत के इतिहास के अनसुने सच।",
                "/blog/", f"{SITE}/assets/og.jpg", body, ld, index)


def home_cards(public):
    """Up to 6 cards for the home page: each series' full story first, then single stories (relative links)."""
    arts = load_all()
    order = [f"{s}-full-story" for s in sorted(SERIES_ORDER, key=SERIES_ORDER.get)] + sorted(k for k, a in arts.items() if not a.get("series"))
    picks = [arts[k] for k in order if k in arts][:6]
    return "\n".join("        " + card(a, public) for a in picks)


def build(public):
    arts = load_all()
    if not arts:
        return []
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    series = series_info()
    urls = []
    for a in arts.values():
        out = ROOT / "blog" / a["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(article_page(a, arts, public, series, index), encoding="utf-8", newline="\n")
        urls.append(f"/blog/{a['slug']}/")
    (ROOT / "blog" / "index.html").write_text(index_page(arts, public, series, index), encoding="utf-8", newline="\n")
    return ["/blog/"] + urls
