"""Blog: /blog/ (all articles, series-wise) and /blog/<slug>/ from data/blog/<slug>.json (written by write_articles.py).

Uses the same page shell as the series pages (pages.page). A video shows as a click-to-play player once it is public;
before that the article shows its release date.
"""
import json
import re
from pathlib import Path

import links
import pages
from pages import SITE, art_path, art_url, e, page, redirect_page, series_url, when

ROOT = Path(__file__).resolve().parent.parent
SERIES_ORDER = {"ajatashatru": 0, "ashoka": 1, "diwali": 2}


READ_JS = """
  (function () {
    var bar = document.querySelector('.read-bar'), art = document.querySelector('.art');
    if (!bar || !art) return;
    var root = document.documentElement, grid = document.querySelector('.art-grid');
    var left = document.getElementById('rt-left'), mins = left ? parseInt(left.getAttribute('data-mins'), 10) || 1 : 1;
    var links = [].slice.call(document.querySelectorAll('.toc a, .toc-m a'));
    var SIZES = [16, 17.5, 19, 20.5, 22], fs = 1;
    function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
    function put(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
    var saved = parseInt(get('gx-fs'), 10); if (saved >= 0 && saved < SIZES.length) fs = saved;
    function size() {
      root.style.setProperty('--art-fs', SIZES[fs] + 'px');
      [].forEach.call(document.querySelectorAll('[data-fs]'), function (b) {
        var d = parseInt(b.getAttribute('data-fs'), 10); b.disabled = (d < 0 && fs === 0) || (d > 0 && fs === SIZES.length - 1);
      });
    }
    [].forEach.call(document.querySelectorAll('[data-fs]'), function (b) {
      b.addEventListener('click', function () { fs = Math.max(0, Math.min(SIZES.length - 1, fs + parseInt(b.getAttribute('data-fs'), 10))); put('gx-fs', fs); size(); upd(); });
    });
    size();
    var focus = document.getElementById('rt-focus');
    function setFocus(on) { if (grid) grid.classList.toggle('focus', on); if (focus) { focus.setAttribute('aria-pressed', on ? 'true' : 'false'); focus.classList.toggle('on', on); } }
    if (get('gx-focus') === '1') setFocus(true);
    if (focus) focus.addEventListener('click', function () { var on = !(grid && grid.classList.contains('focus')); setFocus(on); put('gx-focus', on ? '1' : '0'); });
    var paper = document.getElementById('rt-paper');
    function setPaper(on) { art.classList.toggle('paper', on); if (paper) { paper.setAttribute('aria-pressed', on ? 'true' : 'false'); paper.classList.toggle('on', on); } }
    if (get('gx-paper') === '1') setPaper(true);
    if (paper) paper.addEventListener('click', function () { var on = !art.classList.contains('paper'); setPaper(on); put('gx-paper', on ? '1' : '0'); });
    var wa = document.getElementById('rt-wa');
    if (wa) wa.href = 'https://wa.me/?text=' + encodeURIComponent(document.title.split(' | ')[0] + ' ' + location.href.split('#')[0]);
    var cp = document.getElementById('rt-copy');
    if (cp) cp.addEventListener('click', function () {
      var url = location.href.split('#')[0], old = cp.textContent;
      var done = function () { cp.textContent = 'Copied'; cp.classList.add('on'); setTimeout(function () { cp.textContent = old; cp.classList.remove('on'); }, 1800); };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(done);
    });
    var rail = document.querySelector('.read-rail'), fill = rail && rail.querySelector('.rr-fill'), pct = rail && rail.querySelector('.rr-pct'), ticks = [];
    if (rail) {
      [].slice.call(art.querySelectorAll('h2[id]')).forEach(function (hd) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'rr-t';
        b.title = hd.textContent.replace('#', '').trim(); b.setAttribute('aria-label', 'Go to: ' + b.title);
        b.addEventListener('click', function () { hd.scrollIntoView({behavior: 'smooth', block: 'start'}); });
        rail.appendChild(b); ticks.push([b, hd]);
      });
    }
    function upd() {
      var r = art.getBoundingClientRect(), h = r.height - innerHeight, cur = null;
      var p = Math.min(1, Math.max(0, -r.top / (h > 0 ? h : 1)));
      bar.style.transform = 'scaleX(' + p + ')';
      if (rail) {
        rail.classList.toggle('show', r.top < innerHeight * 0.6 && r.bottom > innerHeight * 0.3);
        if (fill) fill.style.height = (p * 100) + '%';
        if (pct) pct.textContent = Math.round(p * 100) + '%';
        var act = null;
        ticks.forEach(function (x) {
          var top = x[1].getBoundingClientRect().top;
          x[0].style.top = Math.min(100, Math.max(0, (top - r.top) / r.height * 100)) + '%';
          if (top < 140) act = x[0];
        });
        ticks.forEach(function (x) { x[0].classList.toggle('on', x[0] === act); });
      }
      if (left) { var m = Math.ceil(mins * (1 - p)); left.textContent = p < 0.02 ? mins + ' min read' : p > 0.985 ? 'Finished' : m + ' min left'; }
      links.forEach(function (l) { var t = document.querySelector(l.getAttribute('href')); if (t && t.getBoundingClientRect().top < 140) cur = l.getAttribute('href'); });
      links.forEach(function (l) { l.classList.toggle('on', l.getAttribute('href') === cur); });
    }
    var posKey = 'gx-pos:' + location.pathname, lastSave = 0;
    function save(p) {
      var now = Date.now(); if (now - lastSave < 700) return; lastSave = now;
      if (p > 0.97) { try { localStorage.removeItem(posKey); } catch (e) {} } else if (p > 0.04) put(posKey, p.toFixed(3));
    }
    function place(p) { var r = art.getBoundingClientRect(), h = r.height - innerHeight; return scrollY + r.top + p * (h > 0 ? h : 0); }
    var back = parseFloat(get(posKey));
    if (back > 0.06 && back < 0.94 && !location.hash && scrollY < 240) {
      var box = document.createElement('div'); box.className = 'resume';
      box.innerHTML = '<span>Continue where you left off? <b>' + Math.round(back * 100) + '%</b> read</span><button type="button" data-go>Continue</button><button type="button" data-no aria-label="Start over">Start over</button>';
      document.body.appendChild(box);
      var hide = function () { box.classList.remove('show'); setTimeout(function () { box.remove(); }, 300); };
      box.querySelector('[data-go]').addEventListener('click', function () { scrollTo({top: place(back), behavior: 'smooth'}); hide(); });
      box.querySelector('[data-no]').addEventListener('click', function () { try { localStorage.removeItem(posKey); } catch (e) {} hide(); });
      setTimeout(function () { box.classList.add('show'); }, 500); setTimeout(hide, 14000);
    }
    var _upd = upd;
    upd = function () { _upd(); var r = art.getBoundingClientRect(), h = r.height - innerHeight; if (h > 0) save(Math.min(1, Math.max(0, -r.top / h))); };
    addEventListener('scroll', upd, {passive: true}); addEventListener('resize', upd); upd();
  })();
"""


def load_raw():
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "blog").glob("*.json"))]


def load_all():
    """Every article that has its own page (an article with "redirect_to" is merged into another one)."""
    return {a["slug"]: a for a in load_raw() if not a.get("redirect_to")}


AUTOLINKS = ROOT / "data" / "autolinks.json"
DEV = "\u0900-\u097F"


def autolinker(arts, self_slug, limit=5):
    """Returns f(text) that links the first mention of known names (data/autolinks.json) to their story, in text that is already
    escaped. Each story is linked once per article, never to the article itself, at most `limit` links in all."""
    try:
        rows = json.loads(AUTOLINKS.read_text(encoding="utf-8"))["links"]
    except (OSError, ValueError, KeyError):
        rows = []
    to = {}
    for r in rows:
        if r["slug"] in arts and r["slug"] != self_slug:
            for term in r["terms"]:
                to[term] = r["slug"]
    if not to:
        return lambda x: x
    pat = re.compile("(?<![" + DEV + "])(" + "|".join(re.escape(k) for k in sorted(to, key=len, reverse=True)) + ")(?![" + DEV + "])")
    used = set()

    def one(m):
        slug = to[m.group(1)]
        if slug in used or len(used) >= limit:
            return m.group(0)
        used.add(slug)
        return '<a class="x-link" href="' + art_url(slug) + '">' + m.group(1) + "</a>"
    return lambda x: pat.sub(one, x)


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
    if (ROOT / "assets" / "parts" / f"{a['slug']}.webp").exists():   # the part's own opening picture
        return f"/assets/parts/{a['slug']}.webp", "tall"
    if a.get("series"):        # a series story whose video is not public yet: its Part 1 cover
        sf = ROOT / "data" / "series" / f"{a['series']}.json"
        if sf.exists():
            for p in json.loads(sf.read_text(encoding="utf-8"))["parts"]:
                if p.get("short") and (ROOT / "assets" / "covers" / f"{p['short']}.webp").exists():
                    return f"/assets/covers/{p['short']}.webp", "tall"
    art = ROOT / "assets" / f"{a.get('series')}-art.webp"
    return (f"/assets/{a['series']}-art.webp", "tall") if a.get("series") and art.exists() else ("/assets/og.jpg", "wide")


def upcoming_at(slug):
    """When a single story's video goes live, from site.json "upcoming" ("article" given, or the label's first word
    starts the slug, e.g. "Chhath Puja" -> chhath-puja-ki-kahani). Past times are ignored."""
    from datetime import datetime, timezone
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for u in site.get("upcoming", []):
        name = u.get("label", "").split("·")[0].strip().lower().split(" ")[0]
        if (u.get("article") == slug or (name and slug.startswith(name + "-"))) and "Part" not in u.get("label", ""):
            try:
                if datetime.fromisoformat(u["at"]) > now:
                    return u["at"]
            except (KeyError, ValueError):
                pass
    return ""


def article_page(a, arts, public, series, index):
    slug = a["slug"]
    s = series.get(a.get("series") or "")
    vid = a.get("video") or a.get("short")              # Short-only stories show their Short
    short = bool(a.get("part")) or vid == a.get("short")
    live = vid in public
    img, shape = thumb(a, public)
    if live and short:
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
        else:                   # a single story: its release time from "Coming next" (data/site.json upcoming)
            at = upcoming_at(slug)
        if at or s:
            player = (f'<div class="player soon-box"><img src="{e(img)}" alt="" width="540" height="960">'
                      f'<div><b>Video coming soon</b><span>{e(when(at)) or "Coming soon"}</span></div></div>')
        else:                   # no video planned: the story's own picture, never an empty space
            player = (f'<div class="player {"tall" if shape == "tall" else ""} still"><img src="{e(img)}" alt="'
                      f'{e(head_title(a["title"]))}" width="{540 if shape == "tall" else 960}" '
                      f'height="{960 if shape == "tall" else 540}"></div>')

    crumbs = '<a href="/">Gyaanoxa</a> › <a href="/blog/">Blog</a>'
    badge = ""
    if s:
        crumbs += f' › <a href="{series_url(s["slug"])}">{e(s["title_en"])}</a>'
        badge = f"Part {a['part']} of {a['of']}" if a.get("part") else "Full story"
    link = autolinker(arts, slug)
    intro_html = link(e(a.get("intro", "")))
    secs = "".join(f'<h2 id="s{i}">{e(x["h2"])}<a class="h-a" href="#s{i}" aria-label="Link to this section">#</a></h2>' + "".join(f"<p>{link(e(p))}</p>" for p in x["paras"])
                   for i, x in enumerate(a["sections"], 1))
    dyk = a.get("did_you_know") or []
    if dyk:                    # one "did you know" box in the middle of the article
        mid = len(a["sections"]) // 2 + 1
        box = '<div class="dyk"><b>Did you know?</b>' + "".join(f"<p>{e(t)}</p>" for t in dyk) + "</div>"
        secs = secs.replace(f'<h2 id="s{mid}">', box + f'<h2 id="s{mid}">', 1) if mid > 1 else secs + box
    dates = "".join(f"<li><b>{e(d)}</b><span>{e(t)}</span></li>" for d, t in a.get("key_dates", []))
    faq = "".join(f"<details><summary>{e(q['q'])}</summary><p>{e(q['a'])}</p></details>" for q in a.get("faq", []))
    hl = "".join(f"<li>{e(t)}</li>" for t in a.get("highlights", []))
    toc = "".join(f'<li><a href="#s{i}">{e(x["h2"])}</a></li>' for i, x in enumerate(a["sections"], 1))
    toc = f'<details class="side-box toc" open><summary><span>In this article</span><em>{len(a["sections"])}</em></summary><ol>{toc}</ol></details>' if toc else ""
    people = "".join(f"<li><b>{e(n)}</b><span>{e(r)}</span></li>" for n, r in a.get("people", []))
    people = f'<details class="side-box people" open><summary><span>People in this story</span><em>{len(a.get("people", []))}</em></summary><ul>{people}</ul></details>' if people else ""

    nav = pnav = ""
    related = []
    if s:
        base = s["slug"]
        items = [(f"{base}-full-story", "Full story")] + [(f"{base}-part-{p['n']}", f"Part {p['n']}: {p['topic']}") for p in s["parts"]]
        nav = "".join(f'<li{" class=on" if k == slug else ""}><a href="{art_url(k)}">{e(t)}</a></li>'
                      for k, t in items if k in arts)
        nav = f'<details class="side-box series-nav" open><summary><span>Articles in this series</span><em>{len(items)}</em></summary><ol>{nav}</ol><a class="more" href="{series_url(base)}">Series page and quiz</a></details>'
        keys = [k for k, _ in items if k in arts]
        at = keys.index(slug) if slug in keys else 0
        related = [arts[k] for k in keys[at + 1:] + keys[:at]][:4]
        if a.get("part"):
            prev_k, next_k = f"{base}-part-{a['part'] - 1}", f"{base}-part-{a['part'] + 1}"
            pn = ""
            if prev_k in arts:
                pn += f'<a class="pn" href="{art_url(prev_k)}"><small>← Previous part</small><b>{e(head_title(arts[prev_k]["title"]))}</b></a>'
            if next_k in arts:
                pn += f'<a class="pn next" href="{art_url(next_k)}"><small>Next part →</small><b>{e(head_title(arts[next_k]["title"]))}</b></a>'
            pnav = f'<div class="prevnext">{pn}</div>' if pn else ""
    if not related:
        others = [x for x in arts.values() if x["slug"] != slug and (x.get("part") or 0) == 0]
        related = sorted(others, key=lambda x: (x.get("series") == a.get("series"), x["slug"]), reverse=True)[:4]
    rel = "".join(card(x, public) for x in related)
    import inner
    from portal import article_card
    more_reads = inner.section("Keep reading", "More stories", "", '<div class="g4">' + "".join(article_card(x, public) for x in related) + "</div>",
                               ("All articles", "/blog/"), alt=True) if related else ""

    yt = links.buttons(vid, short) if live else \
        '<a class="btn" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener"><svg><use href="#i-yt"/></svg>Subscribe</a>'
    src = a.get("source") or {}
    mins = max(2, round(words(a) / 180))
    tags = "".join(f'<span class="tag-chip">#{e(k)}</span>' for k in a.get("keywords", []))
    en = a["title"].split(" | ")[1] if " | " in a["title"] else ""
    import urllib.parse as _up
    from portal import icon as _icon
    _title = head_title(a["title"])
    _mail = ("mailto:gyaanoxa@gmail.com?subject=" + _up.quote("Correction: " + _title) + "&body="
             + _up.quote("Article: " + SITE + art_url(slug) + chr(10) + chr(10) + "What is wrong:" + chr(10) + chr(10) + "The source:" + chr(10)))
    fix = ('<div class="fix"><i class="fix-i">' + _icon("shield") + "</i><div><b>Found a mistake?</b><p>Send us what is wrong and the source. A correction with a source is fixed in this article and in the next video.</p></div>"
           '<a class="btn ghost" href="' + _mail + '">' + _icon("mail") + " Report a mistake</a></div>")
    nx, nlabel = None, "Keep reading"
    if s and a.get("part"):
        nk = f"{s['slug']}-part-{a['part'] + 1}"
        fk = f"{s['slug']}-full-story"
        if nk in arts:
            nx, nlabel = arts[nk], f"Next up · Part {a['part'] + 1} of {a['of']}"
        elif fk in arts:
            nx, nlabel = arts[fk], "Next up · The full story"
    elif s:
        fp = f"{s['slug']}-part-1"
        if fp in arts:
            nx, nlabel = arts[fp], "Start from Part 1"
    if nx is None and related:
        nx = related[0]
    nextup = ""
    if nx is not None:
        _img, _ = thumb(nx, public)
        nextup = ('<a class="nextup" href="' + art_url(nx["slug"]) + '"><span class="nu-im"><img loading="lazy" decoding="async" ' + pages.srcset(_img, 480, "(max-width: 700px) 92vw, 300px", (640,))
                  + ' alt=""></span><span class="nu-b"><small>' + e(nlabel) + "</small><b>" + e(head_title(nx["title"])) + "</b><p>" + e((nx.get("description") or "")[:170])
                  + '</p><span class="nu-go">Read next ' + _icon("arrow") + "</span></span></a>")
    tall = "tall" in player or "soon-box" in player
    rtools = ('<div class="rtools" role="toolbar" aria-label="Reading tools"><span class="rt-left" id="rt-left" data-mins="' + str(mins) + '">' + str(mins) + " min read</span>"
              '<span class="rt-sp"></span><button type="button" class="rt-b" data-fs="-1" aria-label="Smaller text"><b>A</b><small>-</small></button>'
              '<button type="button" class="rt-b" data-fs="1" aria-label="Larger text"><b>A</b><small>+</small></button>'
              '<button type="button" class="rt-b" id="rt-focus" aria-pressed="false" title="Hide the side boxes">Focus</button>'
              '<button type="button" class="rt-b" id="rt-paper" aria-pressed="false" title="Warm paper colour for reading">Paper</button>'
              '<a class="rt-b rt-wa" id="rt-wa" target="_blank" rel="noopener" href="https://wa.me/">WhatsApp</a>'
              '<button type="button" class="rt-b" id="rt-copy">Copy link</button></div>')
    toc_m = ('<nav class="toc-m" aria-label="Jump to a section">' + "".join(f'<a href="#s{i}">{e(x["h2"])}</a>' for i, x in enumerate(a["sections"], 1)) + "</nav>") if len(a["sections"]) > 1 else ""
    body = f"""  <div class="read-bar" aria-hidden="true"></div>
  <div class="read-rail" aria-label="Reading progress"><span class="rr-pct">0%</span><i class="rr-fill"></i></div>
  <section class="art-hero">
    <div class="wrap art-top{' wide' if not tall else ''}">
      <div class="art-head">
        <p class="crumbs">{crumbs}</p>
        <div class="art-chips">{f'<span class="chip">{e(badge)}</span>' if badge else ''}<span class="chip ghost">{mins} min read</span>{f'<span class="chip ghost notranslate">{e(en)}</span>' if en else ''}</div>
        <h1>{e(head_title(a["title"]))}</h1>
        {links.byline(a)}
        <p class="art-lead">{e(a.get("description", ""))}</p>
        {f'<div class="hl"><p class="eyebrow">What you will learn</p><ul>{hl}</ul></div>' if hl else ''}
      </div>
      <div class="art-media">{player}{f'<div class="art-watch"><span>Watch on</span>{links.icons(vid, short)}</div>' if live else ''}</div>
    </div>
  </section>
  <section class="art-body">
    <div class="wrap art-grid">
      <article class="art">
        {rtools}{toc_m}
        <p class="art-intro">{intro_html}</p>
        {secs}
        {f'<div class="kd"><h2>Key dates</h2><ol class="vt">{dates}</ol></div>' if dates else ''}
        {f'<h2>Questions people ask</h2><div class="faq">{faq}</div>' if faq else ''}
        <div class="takeaway"><b>In short</b><p>{e(a.get("takeaway", ""))}</p></div>
        <p class="src">Source: <a href="{e(src.get("url", ""))}" target="_blank" rel="noopener">{e(src.get("title", ""))}</a> (Wikipedia) and the books it cites.</p>
        {f'<div class="tags"><span>Tags</span>{tags}</div>' if tags else ''}
        <div class="actions">{yt}<a class="btn ghost" href="/blog/">All articles</a></div>
        {pnav}
        {fix}
        {nextup}
      </article>
      <div class="art-side">{toc}{nav}{people}</div>
    </div>
  </section>
  {f'<div class="portal">{more_reads}</div>' if rel else ''}"""
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": head_title(a["title"])[:110], "description": a.get("description", ""),
         "inLanguage": "hi", "datePublished": a.get("written", ""), "keywords": ", ".join(a.get("keywords", [])),
         "image": SITE + img, "url": f"{SITE}{art_url(slug)}",
         "dateModified": a.get("written", ""), "mainEntityOfPage": f"{SITE}{art_url(slug)}", "wordCount": words(a),
         "articleSection": s["title_en"] if s else "Indian History",
         "about": [{"@type": "Person", "name": n} for n, _ in a.get("people", [])][:6] or None,
         "author": {"@type": "Organization", "name": "Gyaanoxa", "url": SITE},
         "publisher": {"@type": "Organization", "name": "Gyaanoxa", "logo": {"@type": "ImageObject", "url": SITE + "/assets/icon-512.png"}}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                                            for q in a.get("faq", [])]}]}
    trail = [("Gyaanoxa", "/"), ("Blog", "/blog/")] + ([(s["title_en"], f"/{s['slug']}/")] if s else []) +         [(head_title(a["title"]), art_url(slug))]
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
    return page(a.get("seo_title") or f"{a['title']} | Gyaanoxa", a.get("seo_desc") or a.get("description", ""), art_url(slug),
                SITE + img, body, ld, index, READ_JS, head, "article")


def card(a, public):
    img, shape = thumb(a, public)
    label = (f"Part {a['part']} of {a['of']}" if a.get("part") else "Full story") if a.get("series") else "Article"
    return (f'<a class="acard {shape}" href="{art_url(a["slug"])}"><div class="ac-img"><img loading="lazy" '
            f'{pages.srcset(img, 360, "(max-width: 760px) 40vw, 360px")} alt=""></div>'
            f'<div class="ac-body"><span class="ac-k">{e(label)} · {max(2, round(words(a) / 180))} min read</span>'
            f'<h3>{e(head_title(a["title"]))}</h3><p>{e(a.get("description", ""))}</p>{links.by(a.get("updated") or a.get("written") or "")}</div></a>')


def prow(a, public):
    img, _ = thumb(a, public)
    return (f'<li><a class="prow" href="{art_url(a["slug"])}"><img loading="lazy" src="{pages.ver(pages.small(img, 160))}" alt="" width="540" height="960">'
            f'<div><span class="ac-k">Part {a["part"]} · {max(2, round(words(a) / 180))} min read</span>'
            f'<h3>{e(head_title(a["title"]))}</h3></div></a></li>')


def feature(a, public, s):
    img, _ = thumb(a, public)
    return (f'<a class="bfeat-card" href="{art_url(a["slug"])}"><img loading="lazy" src="{e(img)}" alt="">'
            f'<div class="bf-body"><span class="chip">Full story · {max(2, round(words(a) / 180))} min read</span>'
            f'<h3>{e(head_title(a["title"]))}</h3><p>{e(a.get("description", ""))}</p>'
            f'<span class="bf-go">Read the full story →</span></div></a>')


def series_date(s):
    """When a series started (its Part 1), for newest-first lists."""
    return min((p.get("at") or "" for p in s.get("parts", [])), default="") or (s.get("full") or {}).get("at", "")


def story_date(a, public):
    """When a single story came out (or comes out): its video's YouTube date, else its release time, else written."""
    for vid in (a.get("short"), a.get("video")):
        if vid and vid in public and public[vid].get("published"):
            return public[vid]["published"]
    return upcoming_at(a["slug"])[:10] or a.get("written", "")


def newest_series(series):
    return sorted(series, key=lambda k: series_date(series[k]), reverse=True)


def index_page(arts, public, series, index):
    import inner
    from portal import article_card
    sections = ""
    jump = []
    for n, sl in enumerate(newest_series(series)):
        s = series[sl]
        full = arts.get(f"{sl}-full-story")
        parts = [arts[k] for k in [f"{sl}-part-{p['n']}" for p in s["parts"]] if k in arts]
        if not (full or parts):
            continue
        cards = ([full] if full else []) + parts
        jump.append('<a href="#' + e(sl) + '">' + e(s["title_hi"].split(":")[0]) + "</a>")
        sections += inner.section("Series · " + str(len(s["parts"])) + " parts", s["title_hi"], "The full story and every part, in order.", '<div class="g4">' + "".join(article_card(a, public) for a in cards) + "</div>",
                                  ("Series page and quiz", series_url(sl)), alt=n % 2 == 1).replace('<section class="ps', '<section id="' + e(sl) + '" class="ps', 1)
    singles = sorted((a for a in arts.values() if not a.get("series")), key=lambda a: story_date(a, public), reverse=True)
    if singles:
        sections += inner.section("Stories", "Single stories", "", '<div class="g4">' + "".join(article_card(a, public) for a in singles) + "</div>",
                                  alt=bool(sections.count("<section") % 2)).replace('<section class="ps', '<section id="stories" class="ps', 1)
    total = sum(max(2, round(words(a) / 180)) for a in arts.values())
    from portal import icon
    search = ('<form class="bsearch" action="/search/" method="get" role="search">' + icon("search") + '<input type="search" name="q" placeholder="Search any story, king or festival" aria-label="Search stories">'
              '<button class="btn" type="submit">Search</button></form>')
    body = inner.banner("Blog", "Blog", "The Gyaanoxa Blog",
                        "The long version of every video: the same facts and sources, with dates, the people in the story and the questions readers ask. Series articles are grouped part by part.",
                        [("book", str(len(arts)), "Articles"), ("layers", str(len(series)), "Series"), ("clock", str(total), "Minutes of reading")], extra=search)
    if singles:
        jump.append('<a href="#stories">Single stories</a>')
    bar = '<nav class="jumpbar" aria-label="Series"><div class="wrap">' + "".join(jump) + "</div></nav>" if jump else ""
    body = inner.wrap(body + bar + sections + inner.follow())
    ld = {"@context": "https://schema.org", "@type": "Blog", "name": "Gyaanoxa Blog", "url": f"{SITE}/blog/", "inLanguage": "hi"}
    return page("इतिहास की कहानियाँ पढ़ें | Indian History Blog in Hindi", "Gyaanoxa के हर वीडियो की कहानी विस्तार से। अशोक, अजातशत्रु, दिवाली, कोहिनूर और भारत के इतिहास के अनसुने सच।",
                "/blog/", f"{SITE}/assets/og.jpg", body, ld, index)


def home_cards(public):
    """Up to 6 cards for the home page: each series' full story first, then single stories (relative links)."""
    arts = load_all()
    order = [f"{s}-full-story" for s in sorted(SERIES_ORDER, key=SERIES_ORDER.get)] + sorted(k for k, a in arts.items() if not a.get("series"))
    picks = [arts[k] for k in order if k in arts][:8]
    return "\n".join("        " + card(a, public) for a in picks)


def build(public):
    arts = load_all()
    if not arts:
        return []
    index = (ROOT / "build" / "shell.html").read_text(encoding="utf-8")
    series = series_info()
    urls = []
    for a in arts.values():
        out = ROOT / "blog" / art_path(a["slug"]) / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(article_page(a, arts, public, series, index), encoding="utf-8", newline="\n")
        urls.append(art_url(a["slug"]))
        olds = ([a["slug"]] if art_path(a["slug"]) != a["slug"] else []) + list(a.get("aliases", []))
        for o in olds:                              # every earlier address (already in video descriptions) redirects
            if o != art_path(a["slug"]):
                old = ROOT / "blog" / o / "index.html"
                old.parent.mkdir(parents=True, exist_ok=True)
                old.write_text(redirect_page(art_url(a["slug"])), encoding="utf-8", newline="\n")
    for a in load_raw():                            # merged articles: their addresses lead to the article they joined
        if a.get("redirect_to") and a["redirect_to"] in arts:
            for o in {a["slug"], a.get("path") or a["slug"]} | set(a.get("aliases", [])):
                old = ROOT / "blog" / o / "index.html"
                old.parent.mkdir(parents=True, exist_ok=True)
                old.write_text(redirect_page(art_url(a["redirect_to"])), encoding="utf-8", newline="\n")
    (ROOT / "blog" / "index.html").write_text(index_page(arts, public, series, index), encoding="utf-8", newline="\n")
    return ["/blog/"] + urls
