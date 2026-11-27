"""The new home page, laid out like a structured portal: welcome section with a right-hand panel, icon cards, counters, schedule cards,
latest videos / articles grids, topics, a contact block. Built only from the site's own data. Written to /preview/ first."""
import json
import re
from datetime import datetime

import blog
import links
from pages import ROOT, SITE, e, page, series_url, art_url, srcset

IC = {
    "play": '<polygon points="6 4 20 12 6 20 6 4"/>',
    "film": '<rect x="2" y="3" width="20" height="18" rx="3"/><path d="M7 3v18M17 3v18M2 9h5M2 15h5M17 9h5M17 15h5"/>',
    "zap": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>',
    "layers": '<path d="m12 2 10 5-10 5L2 7l10-5z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/>',
    "book": '<path d="M2 4h7a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H2z"/><path d="M22 4h-7a3 3 0 0 0-3 3v14a2 2 0 0 1 2-2h8z"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "compass": '<circle cx="12" cy="12" r="10"/><path d="m16 8-2 6-6 2 2-6z"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    "crown": '<path d="m2 6 4 12h12l4-12-6 5-4-7-4 7-6-5z"/><path d="M6 21h12"/>',
    "landmark": '<path d="M3 22h18M6 18v-7M10 18v-7M14 18v-7M18 18v-7M12 2 20 7H4z"/>',
    "scroll": '<path d="M8 21h12a2 2 0 0 0 2-2v-1H10v1a2 2 0 1 1-4 0V5a2 2 0 0 0-2-2 2 2 0 0 0-2 2v2h4"/><path d="M19 17V5a2 2 0 0 0-2-2H4"/>',
    "flame": '<path d="M12 22a7 7 0 0 0 7-7c0-3-2-5-3.5-7-1-1.3-1.5-3-1.5-5-2 1.5-4 4-4.5 6.5C8 11 7 12 6.5 13.5 5.6 16 7 22 12 22z"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.4 8.4 8 9 4.6-.6 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "youtube": '<rect x="2" y="5" width="20" height="14" rx="4"/><path d="m10 9 5 3-5 3z"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8"/>',
    "facebook": '<path d="M18 2h-3a4 4 0 0 0-4 4v3H8v4h3v9h4v-9h3l1-4h-4V6a1 1 0 0 1 1-1h3z"/>',
    "spark": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
}


def icon(name, cls="ic-svg"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{IC[name]}</svg>'


def split_title(t):
    t = re.sub(r"\s*#\w+", "", t).strip()
    hi, _, en = t.partition(" | ")
    return hi.strip(), en.strip()


def pic(v):
    p = ROOT / "assets" / "covers" / f"{v['id']}.webp"
    return f"/assets/covers/{v['id']}.webp" if p.exists() else f"/assets/yt/{v['id']}.webp"


def fmt(n):
    return f"{n / 1000:.1f}K".replace(".0K", "K") if n >= 1000 else str(n)


_VM = {}


def duration(vid):
    """'12:30' for a video, from the cache in data/vmeta.json (empty when unknown)."""
    if not _VM:
        try:
            _VM.update(json.loads((ROOT / "data" / "vmeta.json").read_text(encoding="utf-8")))
        except (OSError, ValueError):
            _VM["_"] = {}
    sec = (_VM.get(vid) or {}).get("d")
    return f"{sec // 60}:{sec % 60:02d}" if sec else ""


def video_card(v, show):
    hi, en = split_title(v["title"])
    hi = re.sub(r"^भाग\s*\d+\s*:\s*", "", hi)
    art = links.article(v["id"])
    yt = ("https://www.youtube.com/shorts/" if v["kind"] == "short" else "https://www.youtube.com/watch?v=") + v["id"]
    ratio = "pc-tall" if v["kind"] == "short" else "pc-wide"
    views = '<i class="pc-v">' + fmt(v.get("views", 0)) + " views</i>" if show and v.get("views") else ""
    read = '<a class="pc-b" href="' + e(art) + '">' + icon("book") + ' Read</a>' if art else ""
    return ('<div class="pc ' + ratio + '"><a class="pc-im" href="' + e(art or yt) + '"' + ("" if art else ' target="_blank" rel="noopener"') + '>'
            '<img loading="lazy" decoding="async" ' + (srcset(pic(v), 240, "(max-width: 640px) 46vw, 210px", (360, 480)) if v["kind"] == "short" else srcset(pic(v), 360, "(max-width: 640px) 92vw, (max-width: 1100px) 45vw, 290px", (480, 640))) + ' alt="" width="640" height="360">' + views + '<span class="pc-kind">' + ("Short" if v["kind"] == "short" else "Full video") + '</span>' + ('<span class="pc-dur">' + duration(v["id"]) + "</span>" if v["kind"] != "short" and duration(v["id"]) else "") + '<span class="pc-p">' + icon("play") + '</span></a>'
            '<div class="pc-t"><a href="' + e(art or yt) + '"' + ("" if art else ' target="_blank" rel="noopener"') + '><b>' + e(hi) + '</b></a>'
            '<small>' + e(en or ("Short" if v["kind"] == "short" else "Full video")) + '</small>' + links.by(v.get("published", "")) +
            '<div class="pc-a"><a class="pc-b pri" href="' + yt + '" target="_blank" rel="noopener">' + icon("play") + ' Watch</a>' + read + '</div></div></div>')


def article_card(a, public):
    src, _ = blog.thumb(a, public)
    kind = "Full story" if not a.get("part") else "Part " + str(a["part"])
    mins = max(1, round(blog.words(a) / 180))
    desc = a.get("description", "")
    return ('<a class="ac" href="' + art_url(a["slug"]) + '"><span class="ac-im"><img loading="lazy" decoding="async" ' + srcset(src, 360, "(max-width: 640px) 92vw, (max-width: 1100px) 45vw, 290px", (480, 640)) + ' alt="" width="640" height="360">'
            '<span class="ac-k"><em>' + e(kind) + "</em><em>" + icon("clock") + " " + str(mins) + " min</em></span></span>"
            '<span class="ac-main"><span class="ac-b"><b>' + e(blog.head_title(a["title"])) + "</b><p>" + e(desc[:110]) + "</p></span>"
            '<span class="ac-f">' + links.by(a.get("updated") or a.get("written") or "") + '<span class="ac-go">' + icon("arrow") + "</span></span></span></a>")


def step_links(d):
    """The part numbers of a series as links: part N goes to that part's article, "Full" to the full story (else the series page)."""
    slug = d["slug"]
    url = series_url(slug)
    bdir = ROOT / "data" / "blog"
    out = ""
    for k in range(len(d.get("parts", []))):
        key = f"{slug}-part-{k + 1}"
        href = art_url(key) if (bdir / f"{key}.json").exists() else url + "#episodes"
        out += '<a href="' + href + '" title="Part ' + str(k + 1) + '">' + str(k + 1) + "</a>"
    full = f"{slug}-full-story"
    out += '<a class="sc-full" href="' + (art_url(full) if (bdir / f"{full}.json").exists() else url) + '" title="Full story">' + icon("play") + " Full</a>"
    return out


def scard(d):
    full = d.get("full") or {}
    f = ROOT / "assets" / "s" / "series" / (d["slug"] + "-720.webp")
    src = "/assets/s/series/" + d["slug"] + "-720.webp" if f.exists() else "/assets/yt/" + str(full.get("id", "")) + ".webp"
    n = len(d.get("parts", []))
    url = series_url(d["slug"])
    return ('<div class="sc"><a class="sc-im" href="' + url + '"><img loading="lazy" decoding="async" ' + srcset(src, 380, "(max-width: 640px) 92vw, (max-width: 1300px) 45vw, 380px", (720,)) + ' alt="" width="720" height="450">'
            '<span class="sc-tag">' + icon("layers") + " " + str(n) + " parts</span></a>"
            '<div class="sc-b"><b><a class="sc-t" href="' + url + '">' + e(d["title_hi"]) + "</a></b><small>" + e(d["title_en"]) + "</small>"
            '<span class="sc-steps">' + step_links(d) + "</span>"
            '<span class="sc-f">' + links.by(span(d), False) + '<span class="ac-go">' + icon("arrow") + "</span></span></div></div>")


def span(d):
    """First and last release day of a series (its parts and the full video)."""
    days = [str(x.get("at", ""))[:10] for x in d.get("parts", []) if x.get("at")]
    full = (d.get("full") or {}).get("at")
    if full:
        days.append(str(full)[:10])
    days = sorted(x for x in days if x)
    return (days[0], days[-1]) if days else ""


def icard(ic, title, text, href, badge=""):
    return ('<a class="ix" href="' + href + '"><span class="ix-i">' + icon(ic) + "</span><b>" + e(title) + "</b><p>" + e(text) + "</p>"
            + ('<em>' + e(badge) + "</em>" if badge else "") + '<span class="ix-go">' + icon("arrow") + "</span></a>")


COUNT_JS = """
  (function () {
    var els = document.querySelectorAll('.cnt');
    function run(el) {
      var to = +el.dataset.to, t0 = null;
      function step(t) { if (!t0) t0 = t; var p = Math.min(1, (t - t0) / 1100); el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(step); }
      requestAnimationFrame(step);
    }
    if (!('IntersectionObserver' in window)) { els.forEach(function (e) { e.textContent = e.dataset.to; }); return; }
    var io = new IntersectionObserver(function (en) { en.forEach(function (x) { if (x.isIntersecting) { run(x.target); io.unobserve(x.target); } }); }, {threshold: .4});
    els.forEach(function (e) { io.observe(e); });
  })();
"""

NEXT_JS = """
  (function () {
    var now = Date.now(), first = true;
    document.querySelectorAll('.up').forEach(function (el) {
      var t = Date.parse(el.getAttribute('data-at'));
      if (isNaN(t) || t < now) { el.remove(); return; }
      if (first) { el.classList.add('next'); first = false; }
    });
  })();
"""

HN_JS = """
  (function () {
    var rows = document.querySelectorAll('.hn[data-at]'), pill = document.getElementById('hp-in');
    function tick() {
      var first = null, now = Date.now();
      rows.forEach(function (r) { var ms = Date.parse(r.getAttribute('data-at')) - now; if (isNaN(ms) || ms < 0) { r.hidden = true; } else if (!first) { first = ms; } });
      if (!pill) return;
      if (first === null) { pill.hidden = true; return; }
      var m = Math.floor(first / 60000), d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60), mm = m % 60;
      pill.textContent = 'Next in ' + (d ? d + 'd ' + h + 'h' : h ? h + 'h ' + mm + 'm' : mm + 'm'); pill.hidden = false;
    }
    tick(); setInterval(tick, 30000);
  })();
  (function () {
    function badge() {
      var el = document.querySelector('.portal .upcoming .up.next'); if (!el) return;
      var pill = el.querySelector('.up-in'); if (!pill) { pill = document.createElement('span'); pill.className = 'up-in'; el.querySelector('.kind').appendChild(pill); }
      var ms = Date.parse(el.getAttribute('data-at')) - Date.now(); if (isNaN(ms) || ms < 0) { pill.remove(); return; }
      var m = Math.floor(ms / 60000), d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60), mm = m % 60;
      pill.textContent = 'in ' + (d ? d + 'd ' + h + 'h' : h ? h + 'h ' + mm + 'm' : mm + 'm');
    }
    setTimeout(badge, 0); setInterval(badge, 30000);
  })();
"""

TOPICS = ["Ashoka", "Kalinga War", "Mauryan Empire", "Chanakya", "Bindusara", "Ajatashatru", "Chandragupta Maurya", "Birsa Munda", "Guru Nanak",
          "Guru Tegh Bahadur", "Rani Lakshmibai", "Rajendra Prasad", "Sardar Patel", "Homi Bhabha", "Koh-i-Noor", "Diwali", "Chhath Puja",
          "Dussehra", "26/11 Mumbai attacks", "Padmanabhaswamy"]


def build(longs, shorts, allv, site, now, show, upcoming_cards, upcoming_article=None):
    index = (ROOT / "build" / "shell.html").read_text(encoding="utf-8")
    public = {v["id"]: v for v in allv}
    arts = blog.load_all()
    series = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "series").glob("*.json"))]
    order = {"dharti": 0, "bindusara": 1, "ajatashatru": 2, "ashoka": 3, "diwali": 4}
    series.sort(key=lambda s: order.get(s["slug"], 9))
    feat = next((v for v in longs if v["id"] == site.get("featured")), None) or (longs[0] if longs else None)
    n_art, n_vid, n_ser = len(arts), len(longs) + len(shorts), len(series)
    n_quiz = sum(len(s.get("quiz", [])) for s in series)
    iso_now = now.astimezone().isoformat()

    cb = ('<div class="cb">'
          '<span><i class="cb-i">' + icon("book") + '</i><em><b class="cnt" data-to="' + str(n_art) + '">0</b><small>Stories to read</small></em></span>'
          '<span><i class="cb-i">' + icon("film") + '</i><em><b class="cnt" data-to="' + str(n_vid) + '">0</b><small>Videos &amp; Shorts</small></em></span>'
          '<span><i class="cb-i">' + icon("layers") + '</i><em><b class="cnt" data-to="' + str(n_ser) + '">0</b><small>Story series</small></em></span>'
          '<span><i class="cb-i">' + icon("help") + '</i><em><b class="cnt" data-to="' + str(n_quiz) + '">0</b><small>Quiz questions</small></em></span></div>')

    # ---- hero: welcome + right-hand panel ----
    panel = ""
    if feat:
        hi, en = split_title(feat["title"])
        art = links.article(feat["id"])
        panel += ('<div class="hp hp-feat"><a class="hp-im" href="' + e(art or "https://www.youtube.com/watch?v=" + feat["id"]) + '"><img loading="lazy" decoding="async" ' + srcset(pic(feat), 240, "(max-width: 640px) 40vw, 170px", (360, 480)) +
                  '" alt="" width="640" height="360"><span class="pc-p">' + icon("play") + '</span>' + ('<span class="pc-dur">' + duration(feat["id"]) + "</span>" if duration(feat["id"]) else "") + '</a><div><em>Featured documentary</em><b>' + e(hi) + "</b><small>" + e(en) +
                  '</small>' + links.by(feat.get("published", "")) + '<div class="hp-act"><a class="pc-b pri" href="https://www.youtube.com/watch?v=' + feat["id"] + '" target="_blank" rel="noopener">' + icon("play") + ' Watch now</a>'
                  + ('<a class="pc-b" href="' + e(art) + '">' + icon("book") + " Read</a>" if art else "") + "</div></div></div>")
    ups = [u for u in site.get("upcoming", []) if u.get("at", "") > iso_now][:3]
    rows = ""
    for u in ups:
        try:
            dt = datetime.fromisoformat(u["at"])
            day, mon, tm = str(dt.day), dt.strftime("%b"), dt.strftime("%I %p").lstrip("0")
        except ValueError:
            day, mon, tm = "", "", ""
        href = (upcoming_article(u) if upcoming_article else "") or "/coming-next/"
        rows += ('<a class="hn' + (" hn-first" if not rows else "") + '" href="' + href + '" data-at="' + e(u["at"]) + '"><span class="hn-d"><b>' + day + "</b><small>" + mon + "</small></span><div><b>" +
                 e(re.sub(r"\s*#\w+", "", u.get("title", ""))) + "</b><small>" + e(u.get("label", "")) + '</small></div><span class="hn-t">' + (tm + " IST" if tm else "") + "</span></a>")
    if rows:
        panel += '<div class="hp hp-next"><p class="hp-h">' + icon("calendar") + 'Coming next<span class="hp-in" id="hp-in" hidden></span><a href="/coming-next/#schedule">Full schedule</a></p>' + rows + "</div>"
    qk = [("/shorts/", "zap", "Shorts"), ("/series/", "layers", "Series"), ("/timeline/", "clock", "Timeline"), ("/series/#quizzes", "help", "Quiz")]
    panel += ('<div class="hp hp-q"><p class="hp-h">' + icon("compass") + 'Quick links</p><div class="hq">' +
              "".join('<a href="' + h + '"><i class="hq-i">' + icon(ic) + "</i><b>" + t + "</b></a>" for h, ic, t in qk) + "</div></div>")
    follow = ('<div class="ph-follow"><span>' + icon("spark") + " Follow Gyaanoxa</span>"
              '<a class="hf hf-yt" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener" aria-label="YouTube">' + icon("youtube") + "</a>"
              '<a class="hf hf-ig" href="https://www.instagram.com/gyaanoxa" target="_blank" rel="noopener" aria-label="Instagram">' + icon("instagram") + "</a>"
              '<a class="hf hf-fb" href="https://www.facebook.com/gyaanoxa" target="_blank" rel="noopener" aria-label="Facebook">' + icon("facebook") + "</a></div>")
    hero = ('<section class="ph"><div class="pw ph-grid"><div class="ph-l"><div class="ph-tags"><span class="k-chip">' + icon("spark") + ' Welcome to Gyaanoxa</span>'
            '<span class="ph-live"><i></i>New Short every evening, 7 PM IST</span></div>'
            "<h1>भारत के <span>अनसुने सच</span></h1>"
            '<p class="ph-lead">True stories from Indian history that most of us never heard in school. Kings, wars, festivals and old mysteries, told as one clear story in simple Hindi.</p>'
            '<ul class="ph-ul"><li>' + icon("check") + "Facts from named sources</li><li>" + icon("check") + "One clear story, told in everyday Hindi</li><li>" + icon("check") +
            "Free to watch on YouTube, Instagram and Facebook</li></ul>"
            '<div class="ph-cta"><a class="btn" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener">' + icon("play") + ' Subscribe on YouTube</a>'
            '<a class="btn ghost" href="/blog/">Explore the stories</a></div>'
            + cb + follow + '</div>'
            '<aside class="ph-r">' + panel + "</aside></div></section>")

    # ---- three feature cards ----
    tri = [("/about/#story", "users", "About us", "Who we are", "A Hindi channel about the parts of Indian history that textbooks skip: kings and wars, festivals, scientists and a few old mysteries.", ["Simple Hindi", "Sources named"]),
           ("/series/#series", "landmark", "What we cover", "Stories, part by part", "Big stories come out one short part each evening, then as one full video with an article and a quiz.", ["A Short each evening", "Full video", "Quiz"]),
           ("/about/#how", "shield", "How we work", "Facts first", "Every story stays close to its sources, with credit for every picture, and is told as one clear account.", ["One clear story", "Picture credits"])]
    trio = ('<section class="ps"><div class="pw"><div class="trio">' + "".join(
        '<a class="tc" href="' + h + '"><span class="tc-n">0' + str(k) + '</span><div class="tc-head"><span class="tc-i">' + icon(ic) + "</span><small>" + lbl + "</small></div>"
        "<h3>" + ti + "</h3><p>" + tx + '</p><span class="tc-tags">' + "".join("<i>" + x + "</i>" for x in tg) + "</span>"
        '<span class="tc-foot"><span>Discover more</span><span class="tc-go">' + icon("arrow") + "</span></span></a>"
        for k, (h, ic, lbl, ti, tx, tg) in enumerate(tri, 1)) + "</div></div></section>")

    # ---- icon cards ----
    cards = "".join([
        icard("film", "Documentaries", "Full-length stories in one sitting.", "/videos/", str(len(longs)) + " videos"),
        icard("zap", "Shorts", "One story in a minute, every evening.", "/shorts/", str(len(shorts)) + " Shorts"),
        icard("layers", "Series", "Big stories told part by part.", "/series/", str(n_ser) + " series"),
        icard("book", "Articles", "The long version with dates and people.", "/blog/", str(n_art) + " articles"),
        icard("clock", "Timeline", "Indian history in order, moment by moment.", "/timeline/"),
        icard("help", "Quizzes", "Five questions after every series.", "/series/#quizzes", str(n_quiz) + " questions"),
        icard("calendar", "Coming next", "What goes live next, with dates.", "/coming-next/#schedule"),
        icard("search", "Search", "Find any story, Short or video.", "/search/"),
        icard("users", "About", "Who makes Gyaanoxa and how.", "/about/"),
        icard("mail", "Suggest a story", "Send a topic or report a mistake.", "/contact/#write"),
    ])
    explore = ('<section id="explore" class="ps ps-alt"><div class="pw"><div class="sh"><span class="k-chip">Explore</span><h2>Everything on Gyaanoxa</h2>'
               "<p>Pick where you want to start. Every part of the channel has its own page.</p></div><div class=\"ixg\">" + cards + "</div></div></section>")

    # ---- coming next (the same section as the old design) ----
    nextsec = ('<section id="next" class="ps"><div class="pw"><div class="sh sh-row"><div><span class="k-chip">Coming next</span><h2>New this week</h2>'
               "<p>What goes live next on YouTube, Instagram and Facebook.</p></div>"
               '<a class="sh-a" href="/coming-next/#schedule">Full schedule ' + icon("arrow") + '</a></div>'
               '<div class="upcoming">' + upcoming_cards(site.get("upcoming", []), now) + "</div>"
               '<p class="note">Festival and special-day topics are planned and may change.</p></div></section>')

    # ---- latest videos + shorts ----
    vids = ('<section id="documentaries" class="ps"><div class="pw"><div class="sh sh-row"><div><span class="k-chip">Watch</span><h2>Latest documentaries</h2><p>The whole story in one sitting.</p></div>'
            '<a class="sh-a" href="/videos/#more-docs">View all ' + icon("arrow") + '</a></div><div class="g4">' + "".join(video_card(v, show) for v in longs[:4]) + "</div></div></section>")
    shs = ('<section id="shorts" class="ps ps-alt"><div class="pw"><div class="sh sh-row"><div><span class="k-chip">Shorts</span><h2>One story in a minute</h2><p>A new Short every evening at 7 PM IST.</p></div>'
           '<a class="sh-a" href="/shorts/#all-shorts">View all ' + icon("arrow") + '</a></div><div class="g5">' + "".join(video_card(v, show) for v in shorts[:10]) + "</div></div></section>")

    # ---- series ----
    ser = ('<section id="series" class="ps"><div class="pw"><div class="sh sh-row"><div><span class="k-chip">Series</span><h2>Stories told part by part</h2>'
           "<p>One short part every evening, then the whole story as one video.</p></div><a class=\"sh-a\" href=\"/series/#series\">All series " + icon("arrow") + '</a></div>'
           '<div class="g3' + (" g-five" if len(series) == 5 else "") + '">' + "".join(scard(d) for d in series) + "</div></div></section>")

    # ---- why + schedule ----
    wy = [("shield", "Close to the sources", "Every story stays with its sources, told in simple Hindi."),
          ("layers", "One clear story", "Never a pile of versions. One account, told well."),
          ("film", "Three ways in", "A one-minute Short, a full video and a long article for every story.")]
    why = ('<section id="why" class="ps ps-alt"><div class="pw"><div class="why"><div class="why-v"><div class="why-o"><img src="/assets/logo.webp" alt="Gyaanoxa" width="256" height="256" loading="lazy">'
           '<span class="fl fl1">' + icon("film") + ' Hindi stories</span><span class="fl fl2">' + icon("shield") + ' Facts first</span><span class="fl fl3">' + icon("clock") + ' Every evening</span></div>'
           '<div class="why-s"><span><b>' + str(n_art) + '+</b><small>Stories</small></span><span><b>' + str(len(shorts)) + '</b><small>Shorts</small></span>'
           '<span><b>' + str(n_ser) + '</b><small>Series</small></span></div></div><div class="why-t">'
           '<span class="k-chip">' + icon("spark") + ' Why Gyaanoxa</span><h2>History the way it was told at home</h2>'
           "<p>Most of us learned history as a list of dates. Gyaanoxa tells the stories behind them: the prince who locked up his own father, the emperor who carved his regret in stone, the festival that lasts five days for a reason.</p>"
           '<div class="why-g">' + "".join('<div class="wy"><i class="wy-i">' + icon(ic) + "</i><b>" + t + "</b><p>" + x + "</p></div>" for ic, t, x in wy) + "</div>"
           '<div class="why-a"><a class="btn" href="/about/#story">Discover more ' + icon("arrow") + '</a><a class="btn ghost" href="https://www.youtube.com/@Gyaanoxa?sub_confirmation=1" target="_blank" rel="noopener">' + icon("play") + ' Subscribe</a>'
           '<span class="why-tr">' + icon("check") + " Free to watch, no sign-up</span></div></div></div></div></section>")
    plans = [("zap", "Shorts", "Every evening", "7 PM IST", ["A one-minute story", "On YouTube, Instagram and Facebook", "Hindi voice with captions on screen", "A long article for every Short"], "Watch Shorts", "/shorts/#all-shorts", True, "One story, one minute, every single evening."),
             ("film", "Full videos", "Every week", "6 PM IST", ["A full documentary, one sitting", "Chapters, an article and a quiz", "The finale of every story series"], "Watch documentaries", "/videos/#more-docs", False, "The whole story in one sitting, with chapters."),
             ("flame", "Festival stories", "A day before", "1 PM IST", ["Diwali, Chhath, Dussehra and more", "Told as one clear story", "Planned dates, they may change"], "See what is next", "/coming-next/#schedule", False, "A special story the day before the festival.")]
    def dial(tm):
        t, _, zone = tm.rpartition(" ")
        return '<span class="sk-dial"><b>' + e(t) + "</b><small>" + e(zone) + "</small></span>"
    pc = "".join('<article class="sk' + (" sk-hot" if hot else "") + '">'
                 + ('<em class="sk-flag">' + icon("spark") + " Most watched format</em>" if hot else "")
                 + '<div class="sk-top"><span class="ix-i">' + icon(ic) + '</span><span class="sk-cad">' + icon("clock") + " " + e(when) + "</span></div>"
                 + '<div class="sk-mid">' + dial(tm) + "<div><h3>" + e(t) + "</h3><p>" + e(blurb) + "</p></div></div>"
                 + "<ul>" + "".join("<li>" + icon("check") + e(x) + "</li>" for x in items) + "</ul>"
                 + '<a class="btn' + ("" if hot else " ghost") + '" href="' + href + '">' + e(cta) + " " + icon("arrow") + "</a></article>"
                 for ic, t, when, tm, items, cta, href, hot, blurb in plans)
    sched = ('<section id="schedule" class="ps"><div class="pw"><div class="sh"><span class="k-chip">Schedule</span><h2>When new stories go live</h2>'
             "<p>A steady rhythm, so you always know when the next story is coming.</p></div><div class=\"skg\">" + pc + "</div>"
             '<p class="note">Times are India time (IST). Festival and special-day dates are planned and may change.</p></div></section>')

    # ---- latest articles ----
    def has_pic(a):
        return "og." not in blog.thumb(a, public)[0]
    newest = sorted(arts.values(), key=lambda a: (has_pic(a), a.get("written") or "", a["slug"]), reverse=True)[:4]
    art = ('<section id="stories" class="ps ps-alt"><div class="pw"><div class="sh sh-row"><div><span class="k-chip">Read</span><h2>Latest stories to read</h2><p>The long version of every video, with dates and the people in the story.</p></div>'
           '<a class="sh-a" href="/blog/">View all ' + icon("arrow") + '</a></div><div class="g4">' + "".join(article_card(a, public) for a in newest) + "</div></div></section>")

    # ---- topics ----
    chips = "".join('<a href="/search/?q=' + e(t.replace(" ", "+")) + '">' + e(t) + "</a>" for t in TOPICS)
    topics = ('<section id="topics" class="ps"><div class="pw"><div class="sh"><span class="k-chip">Topics</span><h2>Topics we cover</h2>'
              "<p>Tap a name to see every story about it.</p></div><div class=\"chips\">" + chips + "</div></div></section>")

    # ---- contact ----
    contact = ('<section id="contact" class="ps ps-alt"><div class="pw"><div class="ct"><div class="ct-l"><span class="k-chip">Contact</span><h2>Suggest a story, or tell us what we got wrong</h2>'
               "<p>Got a topic idea, spotted a mistake, or want to work together? Write to us. We read every message.</p><ul>"
               "<li>" + icon("check") + "Suggest a story from Indian history</li><li>" + icon("check") + "Report a mistake or a wrong date</li><li>" + icon("check") + "Work with Gyaanoxa</li></ul></div>"
               '<div class="ct-r"><span class="ix-i">' + icon("mail") + "</span><h3>Write to us</h3><p>gyaanoxa@gmail.com</p>"
               '<a class="btn" href="mailto:gyaanoxa@gmail.com?subject=Story%20suggestion">Send an email ' + icon("arrow") + '</a><a class="btn ghost" href="/contact/#write">Contact page</a></div></div></div></section>')

    body = '<div class="portal">' + hero + trio + explore + nextsec + vids + shs + ser + why + sched + art + topics + contact + "</div>"
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', index, re.S)
    ld = json.loads(m.group(1)) if m else {"@context": "https://schema.org", "@type": "WebSite", "name": "Gyaanoxa", "url": SITE + "/"}
    (ROOT / "index.html").write_text(page("Indian History in Hindi: भारत के अनसुने सच | Gyaanoxa",
                                         "Indian history in simple Hindi: emperors, wars and untold stories, with a new Short every day at 7 PM IST on YouTube, Instagram and Facebook.",
                                         "/", SITE + "/assets/og.jpg", body, ld, index, COUNT_JS + NEXT_JS + HN_JS), encoding="utf-8", newline=chr(10))
    return []
