"""Series pages (/<slug>/) and the history timeline (/timeline/) from data/series/*.json and data/timeline.json.

Called by build.py after the videos are refreshed, so a part shows "Watch" as soon as its Short is public.
The header, footer and icons are copied from index.html, with links made absolute (pages live in sub-folders).
"""
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://gyaanoxa.com"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def e(s):
    return html.escape(str(s or ""), quote=True)


def absolute(s):
    s = s.replace('href="./#', 'href="/#').replace('href="#', 'href="/#').replace('href="./"', 'href="/"')
    s = re.sub(r'(src|href)="(assets/|privacy\.html|terms\.html|data-deletion\.html|lang\.js|style\.css|favicon\.ico|site\.webmanifest)',
               r'\1="/\2', s)
    return s.replace('<use href="/#', '<use href="#')


def shell(index):
    svg = index[index.index('<svg width="0"'):index.index("</svg>\n\n<header") + 6]
    header = absolute(index[index.index('<header class="top">'):index.index("</header>") + 9])
    footer = absolute(index[index.index("<footer>"):index.index("</footer>") + 9])
    head_links = absolute(index[index.index('  <link rel="icon"'):index.index('  <script type="application/ld+json">')])
    return svg, header, footer, head_links


def page(title, desc, url, image, body, ld, index, extra_js=""):
    svg, header, footer, head_links = shell(index)
    return f"""<!doctype html>
<html lang="hi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="theme-color" content="#13205C">
  <link rel="canonical" href="{SITE}{url}">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:image" content="{e(image)}">
  <meta property="og:url" content="{SITE}{url}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary_large_image">
{head_links}  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>

{svg}

{header}

<main class="sp">
{body}
</main>

{footer}

<script>
  document.querySelectorAll('.reveal').forEach(function (e) {{ e.classList.add('in'); }});
  // Video facade: the YouTube player loads only after a click (faster page, no YouTube cookies before that)
  document.querySelectorAll('.yt-facade').forEach(function (b) {{
    b.addEventListener('click', function () {{
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + b.dataset.id + '?autoplay=1&rel=0' + (b.dataset.t ? '&start=' + b.dataset.t : '');
      f.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen';
      f.allowFullscreen = true; f.title = b.getAttribute('aria-label') || 'Video';
      b.replaceWith(f);
    }});
  }});
  document.querySelectorAll('.chap[data-t]').forEach(function (a) {{
    a.addEventListener('click', function (ev) {{
      var b = document.querySelector('.yt-facade'); if (!b) return;
      ev.preventDefault(); b.dataset.t = a.dataset.t; b.click();
      document.querySelector('.player').scrollIntoView({{behavior: 'smooth', block: 'center'}});
    }});
  }});
{extra_js}
</script>
<script src="/lang.js" defer></script>
<script data-goatcounter="https://gyaanoxa.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


QUIZ_JS = """
  // Quiz: pick an answer, see right / wrong and why; score at the end
  document.querySelectorAll('.quiz').forEach(function (q) {
    var done = 0, right = 0, total = q.querySelectorAll('.qq').length;
    q.querySelectorAll('.qq').forEach(function (item) {
      var a = +item.dataset.a;
      item.querySelectorAll('.opt').forEach(function (b, i) {
        b.addEventListener('click', function () {
          if (item.classList.contains('answered')) return;
          item.classList.add('answered'); done++;
          if (i === a) { right++; b.classList.add('ok'); } else { b.classList.add('no'); item.querySelectorAll('.opt')[a].classList.add('ok'); }
          if (done === total) {
            var s = q.querySelector('.score');
            s.textContent = right + ' / ' + total + (right === total ? ' — शानदार! 🎉' : right >= total - 1 ? ' — बहुत बढ़िया!' : ' — वीडियो देखकर फिर कोशिश करें');
            s.hidden = false;
          }
        });
      });
    });
  });
"""


def when(at):
    try:
        t = datetime.fromisoformat(at)
    except Exception:
        return ""
    hh = t.hour % 12 or 12
    return f"{t.day} {MONTHS[t.month - 1]}, {hh} {'PM' if t.hour >= 12 else 'AM'} IST"


def facade(vid, title, img):
    return (f'<div class="player"><button class="yt-facade" type="button" data-id="{e(vid)}" aria-label="{e(title)}">'
            f'<img src="{e(img)}" alt="" width="960" height="540"><span class="big-play"><svg><use href="#i-play"/></svg></span>'
            f'</button></div>')


def series_page(d, public, index, all_series):
    slug = d["slug"]
    full = d["full"]
    full_live = full.get("id") in public
    ftitle = public[full["id"]]["title"] if full_live else full["title"]
    hi_t = re.sub(r"\s*#\w+", "", ftitle).split(" | ")[0]
    first_cover = next((f"/assets/covers/{p['short']}.webp" for p in d["parts"] if p.get("short")), "/assets/stacked.webp")
    image = f"{SITE}/assets/yt/{full['id']}.webp" if full_live and (ROOT / "assets" / "yt" / f"{full['id']}.webp").exists() else f"{SITE}/assets/og.jpg"

    if full_live:
        img = f"/assets/yt/{full['id']}.webp"
        player = facade(full["id"], hi_t, img)
        watch = f'<a class="btn" href="https://www.youtube.com/watch?v={e(full["id"])}" target="_blank" rel="noopener"><svg><use href="#i-yt"/></svg>पूरी कहानी YouTube पर</a>'
    else:
        player = (f'<div class="player soon-box"><img src="{e(first_cover)}" alt="" width="540" height="960">'
                  f'<div><b>पूरी कहानी — जल्द</b><span>{e(when(full.get("at"))) or "Coming soon"}</span></div></div>')
        watch = '<a class="btn" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener"><svg><use href="#i-yt"/></svg>Subscribe करें</a>'

    chaps = ""
    if full_live and full.get("chapters"):
        chaps = '<ol class="chapters">' + "".join(
            f'<li><a class="chap" data-t="{t}" href="https://www.youtube.com/watch?v={e(full["id"])}&t={t}s" target="_blank" rel="noopener">'
            f'<span class="ts">{t // 60}:{t % 60:02d}</span>{e(n)}</a></li>' for t, n in full["chapters"]) + "</ol>"

    cards = []
    for p in d["parts"]:
        live = p.get("short") in public
        cov = f"/assets/covers/{p['short']}.webp" if p.get("short") and (ROOT / "assets" / "covers" / f"{p['short']}.webp").exists() else ""
        inner = (f'<div class="pc-img">{f"<img loading=lazy src={cov} alt=\"\" width=540 height=960>" if cov else "<span class=pc-n>" + str(p["n"]) + "</span>"}'
                 f'{"<span class=play><svg><use href=#i-play /></svg></span>" if live else ""}</div>'
                 f'<div class="pc-body"><div class="pc-k">भाग {p["n"]}/{len(d["parts"])}</div><h3>{e(p["topic"])}</h3>'
                 f'<p>{e(p["hook"])}</p>'
                 f'<span class="pc-s{" live" if live else ""}">{"▶ Short देखें" if live else "🕒 " + e(when(p.get("at")) or "जल्द")}</span></div>')
        cards.append(f'<a class="pcard" href="https://www.youtube.com/shorts/{e(p["short"])}" target="_blank" rel="noopener">{inner}</a>'
                     if live else f'<div class="pcard">{inner}</div>')

    tl = "".join(f'<li><b>{e(a)}</b><span>{e(b)}</span></li>' for a, b in d.get("timeline", []))
    facts = "".join(f"<li>{e(f)}</li>" for f in d.get("facts", []))
    quiz = "".join(
        f'<div class="qq" data-a="{q["a"]}"><p class="qt">{i}. {e(q["q"])}</p><div class="opts">'
        + "".join(f'<button class="opt" type="button">{e(o)}</button>' for o in q["o"])
        + f'</div><p class="why">{e(q["why"])}</p></div>' for i, q in enumerate(d.get("quiz", []), 1))
    others = "".join(
        f'<a class="other" href="/{e(o["slug"])}/"><b>{e(o["title_hi"])}</b><span>{e(o["title_en"])}</span></a>'
        for o in all_series if o["slug"] != slug)

    body = f"""  <section class="sp-hero">
    <div class="wrap sp-grid">
      <div>
        <p class="crumbs"><a href="/">Gyaanoxa</a> › <a href="/#series">Series</a> › {e(d["title_en"])}</p>
        <p class="eyebrow">{e(d.get("era", ""))} · {e(d.get("years", ""))}</p>
        <h1>{e(d["title_hi"])}</h1>
        <p class="sp-en">{e(d["title_en"])} · {len(d["parts"])} parts + full video</p>
        <p class="lead">{e(d.get("intro_hi", ""))}</p>
        <div class="actions">{watch}<a class="btn ghost" href="#quiz">Quiz खेलें</a></div>
        <p class="place">📍 {e(d.get("place", ""))}</p>
      </div>
      <div>{player}{chaps}</div>
    </div>
  </section>

  <section>
    <div class="wrap">
      <div class="head"><div><p class="eyebrow">Episodes</p><h2>कहानी, भाग-दर-भाग</h2>
      <p class="sub">One part every evening at 7 PM IST — then the whole story in one video.</p></div></div>
      <div class="parts">
{chr(10).join(cards)}
      </div>
    </div>
  </section>

  <section>
    <div class="wrap two">
      <div>
        <p class="eyebrow">Key dates</p><h2>मुख्य घटनाएँ</h2>
        <ol class="vt">{tl}</ol>
      </div>
      <div>
        <p class="eyebrow">What the sources say</p><h2>Facts &amp; sources</h2>
        <ul class="facts">{facts}</ul>
        <p class="src">Source: <a href="{e(d["source"]["url"])}" target="_blank" rel="noopener">{e(d["source"]["title"])}</a> (Wikipedia) and the texts it cites. Legends are told as legends.</p>
      </div>
    </div>
  </section>

  <section id="quiz">
    <div class="wrap">
      <div class="quiz">
        <p class="eyebrow">Quiz</p><h2>कितना याद रहा?</h2>
        <p class="sub">5 सवाल — हर जवाब इसी कहानी से।</p>
        {quiz}
        <p class="score" hidden></p>
      </div>
    </div>
  </section>

  <section>
    <div class="wrap">
      <p class="eyebrow">More series</p><h2>और कहानियाँ</h2>
      <div class="others">{others}<a class="other" href="/timeline/"><b>इतिहास की टाइमलाइन</b><span>All stories on one timeline</span></a></div>
    </div>
  </section>"""

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Gyaanoxa", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": d["title_en"], "item": f"{SITE}/{slug}/"}]},
        {"@type": "CreativeWorkSeries", "name": d["title_hi"], "alternateName": d["title_en"], "inLanguage": "hi",
         "url": f"{SITE}/{slug}/", "publisher": {"@type": "Organization", "name": "Gyaanoxa", "url": SITE}}]}
    if full_live:
        v = public[full["id"]]
        ld["@graph"].append({"@type": "VideoObject", "name": re.sub(r"\s*#\w+", "", v["title"]), "description": d.get("about_en") or d["title_en"],
                             "thumbnailUrl": [f"https://i.ytimg.com/vi/{full['id']}/maxresdefault.jpg"], "uploadDate": v["published"],
                             "embedUrl": f"https://www.youtube-nocookie.com/embed/{full['id']}", "contentUrl": f"https://www.youtube.com/watch?v={full['id']}",
                             "inLanguage": "hi"})
    desc = (d.get("about_en") or d["title_en"])[:300]
    return page(f"{d['title_hi']} | {d['title_en']} — Gyaanoxa", desc, f"/{slug}/", image, body, ld, index, QUIZ_JS)


def timeline_page(tl, public, index):
    def target(ev):
        l = ev["link"]
        if l.startswith("/"):
            return f'{l}/', "Series", ""
        if l in public:
            k = ev.get("kind", "video")
            return (f"https://www.youtube.com/shorts/{l}" if k == "short" else f"https://www.youtube.com/watch?v={l}"), ("Short" if k == "short" else "Video"), ' target="_blank" rel="noopener"'
        return "", "", ""
    blocks = []
    for era in tl["eras"]:
        evs = [x for x in tl["events"] if era["from"] <= x["year"] < era["to"]]
        if not evs:
            continue
        items = []
        for x in sorted(evs, key=lambda v: v["year"]):
            href, kind, tgt = target(x)
            t = f'<b>{e(x["label"])}</b><h3>{e(x["title"])}</h3><span>{e(x["en"])}</span>'
            items.append(f'<li><a href="{e(href)}"{tgt}>{t}<em>{e(kind)} →</em></a></li>' if href else f"<li><div>{t}</div></li>")
        blocks.append(f'<div class="era"><h2>{e(era["name"])} <small>{e(era["en"])}</small></h2><ol class="tl">{"".join(items)}</ol></div>')
    fest = []
    for x in tl.get("festivals", []):
        href, kind, tgt = target(x)
        if href:
            fest.append(f'<a class="other" href="{e(href)}"{tgt}><b>{e(x["title"])}</b><span>{e(x["en"])}</span></a>')
    body = f"""  <section class="sp-hero">
    <div class="wrap">
      <p class="crumbs"><a href="/">Gyaanoxa</a> › Timeline</p>
      <p class="eyebrow">Indian history timeline</p>
      <h1>इतिहास की टाइमलाइन</h1>
      <p class="lead">Gyaanoxa की हर कहानी, सही समय पर — मगध के राजाओं से आज़ाद भारत तक। हर नई वीडियो के साथ यह टाइमलाइन बढ़ती है।</p>
    </div>
  </section>
  <section>
    <div class="wrap">{"".join(blocks)}</div>
  </section>
  <section>
    <div class="wrap"><p class="eyebrow">Festivals</p><h2>त्योहारों की कहानियाँ</h2><div class="others">{"".join(fest)}</div></div>
  </section>"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Indian history timeline — Gyaanoxa",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": x["en"]} for i, x in enumerate(sorted(tl["events"], key=lambda v: v["year"]))]}
    return page("इतिहास की टाइमलाइन | Indian History Timeline — Gyaanoxa",
                "Gyaanoxa's stories of Indian history on one timeline: Magadha, the Mauryas, Ashoka, the Koh-i-Noor, Sardar Patel and more.",
                "/timeline/", f"{SITE}/assets/og.jpg", body, ld, index)


def build(public):
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    series = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "series").glob("*.json"))]
    order = {"ajatashatru": 0, "ashoka": 1, "diwali": 2}
    series.sort(key=lambda s: order.get(s["slug"], 9))
    urls = []
    for d in series:
        out = ROOT / d["slug"] / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(series_page(d, public, index, series), encoding="utf-8", newline="\n")
        urls.append(f"/{d['slug']}/")
    tl = json.loads((ROOT / "data" / "timeline.json").read_text(encoding="utf-8"))
    (ROOT / "timeline").mkdir(exist_ok=True)
    (ROOT / "timeline" / "index.html").write_text(timeline_page(tl, public, index), encoding="utf-8", newline="\n")
    urls.append("/timeline/")
    return urls
