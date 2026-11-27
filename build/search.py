"""Site search: search.json (every article, series, full video and Short) and the /search/ page that filters it in the
visitor's browser. No search service and no cookies: the index is a small static file rebuilt with the site.

Hindi, Hinglish and English find the same story: every entry also carries its words in one plain Latin spelling
(Devanagari written in Latin letters, spelling differences evened out: अशोक / ashok / Ashoka -> "ashok"), and the page
spells what the visitor types the same way.
"""
import json
import re

import blog
import pages
from pages import ROOT, e, page

TOPICS = [  # (name, words in the English title / slug / keywords that put an entry in it)
    ("Kings & empires", ("ashoka", "bindusara", "chandragupta", "kalinga", "maurya", "ajatashatru", "magadha",
                         "bimbisara", "chanakya", "kohinoor", "koh-i-noor", "aurangzeb")),
    ("Festivals", ("diwali", "dussehra", "chhath", "dhanteras", "govardhan", "bhai dooj", "ravan", "lakshmi puja",
                   "naraka", "festival")),
    ("Great Indians", ("birsa", "patel", "bhabha", "lakshmibai", "rani of jhansi", "jhansi", "freedom")),
    ("Mysteries", ("curse", "mystery", "kohinoor", "bhabha", "death")),
    ("Stories & science", ("panchatantra", "monkey", "crocodile", "algae", "phycology", "science")),
]

V = {"अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
     "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
     "ं": "n", "ँ": "n", "ः": "h", "्": "", "़": "", "ॉ": "o", "ॅ": "e"}
C = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
     "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
     "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
     "ष": "sh", "स": "s", "ह": "h", "ळ": "l", "क़": "k", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "rh",
     "फ़": "f"}


SIGNS = set("ािीुूृेैोौॉॅ़्")


def roman(s):
    """Devanagari in plain Latin letters (rough, only for matching): अशोक -> ashok, लक्ष्मी -> lakshmi. A consonant
    carries its hidden 'a' unless a vowel sign or virama follows or the word ends there (as Hindi is spoken)."""
    out = []
    for i, ch in enumerate(s):
        if ch in C:
            nxt = s[i + 1] if i + 1 < len(s) else ""
            out.append(C[ch] + ("a" if nxt and nxt not in SIGNS and (nxt in C or nxt in "ंँ") else ""))
        else:
            out.append(V.get(ch, ch))
    return "".join(out)


def skeleton(s):
    """Every word in one plain Latin spelling, the same for Hindi, Hinglish and English: अशोक / ashok / Ashoka ->
    'ashok', लक्ष्मी / laxmi / lakshmi -> 'laksmi'. The page's JavaScript (SKEL) does exactly the same."""
    words = re.sub(r"[^a-z0-9]+", " ", roman(s).lower()).split()
    out = []
    for w in words:
        for x, y in (("chh", "ch"), ("sh", "s"), ("ph", "f"), ("w", "v"), ("x", "ks"), ("q", "k"), ("z", "j"),
                     ("aa", "a"), ("ee", "i"), ("ii", "i"), ("oo", "u"), ("uu", "u")):
            w = w.replace(x, y)
        w = re.sub(r"(.)+", r"", w)
        w = w[:1] + w[1:].replace("a", "")      # Hindi often skips the 'a' sound: बिरसा = birsa, धनतेरस = dhanteras
        if w:
            out.append(w)
    return " ".join(dict.fromkeys(out))


def flat(s):
    """Lower case without nukta / chandrabindu differences, for plain substring matching."""
    return re.sub(r"\s+", " ", s.lower().replace("़", "").replace("ँ", "ं")).strip()


def topics(text):
    t = text.lower()
    return [name for name, words in TOPICS if any(w in t for w in words)]


def item(kind, title, desc, url, img, date, views, extra):
    title = re.sub(r"\s*#\S+", "", title).strip()       # YouTube titles end with #shorts and similar
    words = " ".join([title, desc, extra])
    return {"k": kind, "t": title, "d": desc, "u": url, "i": pages.ver(pages.small(img, 240)) if img else "",
            "dt": (date or "")[:10], "v": views or 0, "tp": topics(words), "f": flat(words), "s": skeleton(words)}


def index_items(public):
    arts = blog.load_all()
    series = blog.series_info()
    out = []
    for a in arts.values():
        s = series.get(a.get("series") or "")
        date = blog.story_date(a, public)
        if s and a.get("part"):
            date = next((p.get("at", "") for p in s.get("parts", []) if p.get("n") == a["part"]), "") or date
        elif s:
            date = (s.get("full") or {}).get("at", "") or date
        people = " ".join(p[0] for p in a.get("people", []) if p)
        extra = " ".join(a.get("keywords", [])) + " " + people + " " + a["slug"].replace("-", " ")
        kind = "article"
        label = (f"Part {a['part']} · " if a.get("part") else "") + blog.head_title(a["title"])
        out.append(item(kind, label, a.get("description", ""), pages.art_url(a["slug"]), blog.thumb(a, public)[0],
                        date, 0, extra))
    for sl, s in series.items():
        full = arts.get(f"{sl}-full-story")
        img = blog.thumb(full, public)[0] if full else ""
        card = ROOT / "assets" / "s" / "series" / f"{sl}-380.webp"
        if card.exists() and (not img or "og." in img):     # not out yet: the series card on the home page
            img = f"/assets/s/series/{sl}-380.webp"
        out.append(item("series", f'{s["title_hi"]} | {s["title_en"]}', s.get("about_en", ""), pages.series_url(sl), img,
                        blog.series_date(s), 0, sl + " " + s.get("about_hi", "")))
    for v in public.values():
        short = v.get("kind") == "short"
        own = ROOT / "assets" / "covers" / f"{v['id']}.webp"
        img = f"/assets/covers/{v['id']}.webp" if own.exists() else f"/assets/yt/{v['id']}.webp"
        url = f"https://www.youtube.com/shorts/{v['id']}" if short else f"https://www.youtube.com/watch?v={v['id']}"
        title = v.get("title", "")
        out.append(item("short" if short else "video", title, "", url, img, v.get("published", ""), v.get("views", 0),
                        ""))
    out.sort(key=lambda x: x["dt"], reverse=True)
    return out


SEARCH_JS = r"""
  // Search: filters search.json in the browser (Hindi, Hinglish and English via the same word outline as the index)
  (function () {
    var R = {"अ":"a","आ":"a","इ":"i","ई":"i","उ":"u","ऊ":"u","ऋ":"ri","ए":"e","ऐ":"ai","ओ":"o","औ":"au","ा":"a","ि":"i",
      "ी":"i","ु":"u","ू":"u","ृ":"ri","े":"e","ै":"ai","ो":"o","ौ":"au","ं":"n","ँ":"n","ः":"h","्":"","़":"","ॉ":"o","ॅ":"e",
      "क":"k","ख":"kh","ग":"g","घ":"gh","ङ":"n","च":"ch","छ":"chh","ज":"j","झ":"jh","ञ":"n","ट":"t","ठ":"th","ड":"d","ढ":"dh",
      "ण":"n","त":"t","थ":"th","द":"d","ध":"dh","न":"n","प":"p","फ":"ph","ब":"b","भ":"bh","म":"m","य":"y","र":"r","ल":"l",
      "व":"v","श":"sh","ष":"sh","स":"s","ह":"h","ळ":"l"};
    function SKEL(s) {
      var SIG = 'ािीुूृेैोौॉॅ़्', r = '';
      for (var i = 0; i < s.length; i++) {
        var ch = s[i], nx = s[i + 1] || '', isC = ch >= 'क' && ch <= 'ह';
        r += (R[ch] !== undefined ? R[ch] : ch) + (isC && nx && SIG.indexOf(nx) < 0 && ((nx >= 'क' && nx <= 'ह') || 'ंँ'.indexOf(nx) > -1) ? 'a' : '');
      }
      var P = [['chh','ch'],['sh','s'],['ph','f'],['w','v'],['x','ks'],['q','k'],['z','j'],['aa','a'],['ee','i'],['ii','i'],['oo','u'],['uu','u']];
      return r.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim().split(' ').map(function (w) {
        P.forEach(function (p) { w = w.split(p[0]).join(p[1]); });
        w = w.replace(/(.)\1+/g, '$1');
        w = w.slice(0, 1) + w.slice(1).split('a').join('');
        return w;
      }).filter(Boolean);
    }
    function flat(s) { return s.toLowerCase().replace(/़/g, '').replace(/ँ/g, 'ं').replace(/\s+/g, ' ').trim(); }
    var KIND = {article: 'Article', series: 'Series', video: 'Full video', short: 'Short'};
    var box = document.getElementById('q'), list = document.getElementById('results'), info = document.getElementById('count');
    var sortSel = document.getElementById('sort'), data = [], kind = 'all', topic = '';
    var p = new URLSearchParams(location.search);
    box.value = p.get('q') || ''; kind = p.get('type') || 'all'; topic = p.get('topic') || '';
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
    function score(it, q, words) {
      if (!q) return 1;
      var s = 0, t = flat(it.t);
      if (t.indexOf(q) > -1) s += 10;
      if (it.f.indexOf(q) > -1) s += 5;
      var sk = ' ' + it.s + ' ', hit = 0;
      words.forEach(function (w) {          // a short word must match a whole word, a longer one the start of one
        if (w.length > 1 && sk.indexOf(' ' + w + (w.length < 3 ? ' ' : '')) > -1) hit++; });
      if (words.length && hit === words.length) s += 3 * hit;
      return s;
    }
    function render() {
      var q = flat(box.value), words = SKEL(box.value), rows = [];
      data.forEach(function (it) {
        if (kind !== 'all' && it.k !== kind) return;
        if (topic && it.tp.indexOf(topic) < 0) return;
        var s = score(it, q, words); if (s > 0) rows.push([s, it]);
      });
      var by = sortSel.value;
      rows.sort(function (a, b) {
        if (by === 'views') return b[1].v - a[1].v || (b[1].dt > a[1].dt ? 1 : -1);
        if (by === 'best' && q) return b[0] - a[0] || (b[1].dt > a[1].dt ? 1 : -1);
        return b[1].dt > a[1].dt ? 1 : b[1].dt < a[1].dt ? -1 : 0;
      });
      document.querySelectorAll('[data-kind]').forEach(function (b) {
        var n = data.filter(function (it) { return (b.dataset.kind === 'all' || it.k === b.dataset.kind)
          && (!topic || it.tp.indexOf(topic) > -1) && score(it, q, words) > 0; }).length;
        b.querySelector('em').textContent = n; b.classList.toggle('on', b.dataset.kind === kind);
      });
      document.querySelectorAll('[data-topic]').forEach(function (b) { b.classList.toggle('on', b.dataset.topic === topic); });
      info.textContent = rows.length ? rows.length + (rows.length === 1 ? ' result' : ' results') : 'Nothing found. Try another word, in Hindi or English.';
      list.innerHTML = rows.slice(0, 120).map(function (r) {
        var it = r[1], ext = it.u.indexOf('http') === 0;
        return '<a class="sr sr-' + it.k + '" href="' + esc(it.u) + '"' + (ext ? ' target="_blank" rel="noopener"' : '') + '>'
          + (it.i ? '<img loading="lazy" src="' + esc(it.i) + '" alt="">' : '<span class="sr-noimg"></span>')
          + '<div><span class="sr-k">' + KIND[it.k] + (it.dt ? ' · ' + esc(it.dt.split('-').reverse().join('.')) : '') + '</span>'
          + '<h3>' + esc(it.t) + '</h3>' + (it.d ? '<p>' + esc(it.d) + '</p>' : '') + '</div></a>';
      }).join('');
      var u = new URLSearchParams();
      if (box.value) u.set('q', box.value); if (kind !== 'all') u.set('type', kind); if (topic) u.set('topic', topic);
      history.replaceState(null, '', location.pathname + (u.toString() ? '?' + u : ''));
    }
    box.addEventListener('input', function () { sortSel.value = box.value ? 'best' : 'new'; render(); });
    sortSel.addEventListener('change', render);
    document.querySelectorAll('[data-kind]').forEach(function (b) { b.addEventListener('click', function () { kind = b.dataset.kind; render(); }); });
    document.querySelectorAll('[data-topic]').forEach(function (b) { b.addEventListener('click', function () {
      topic = topic === b.dataset.topic ? '' : b.dataset.topic; render(); }); });
    if (box.value) sortSel.value = 'best';
    fetch('/search.json').then(function (r) { return r.json(); }).then(function (d) { data = d; render(); box.focus(); });
  })();
"""


def search_page(index, n):
    kinds = "".join(f'<button type="button" class="sf" data-kind="{k}">{e(lbl)} <em></em></button>'
                    for k, lbl in (("all", "All"), ("article", "Articles"), ("short", "Shorts"), ("video", "Full videos"),
                                   ("series", "Series")))
    tops = "".join(f'<button type="button" class="sf tp" data-topic="{e(t)}">{e(t)}</button>' for t, _ in TOPICS)
    body = f"""  <section class="sp-hero srch-hero">
    <div class="wrap">
      <p class="crumbs"><a href="/">Gyaanoxa</a> › Search</p>
      <h1>Search</h1>
      <p class="lead">Every story, Short, full video and series on Gyaanoxa ({n} in all). Type in Hindi, Hinglish or English: अशोक, ashok and Ashoka all work.</p>
      <form class="srch" role="search" onsubmit="return false">
        <svg aria-hidden="true"><use href="#i-search"/></svg>
        <input id="q" type="search" placeholder="अशोक, Diwali, Rani Lakshmibai..." aria-label="Search Gyaanoxa" autocomplete="off">
        <select id="sort" aria-label="Sort"><option value="new">Newest first</option><option value="best">Best match</option><option value="views">Most viewed</option></select>
      </form>
      <div class="sfilters" role="group" aria-label="Type">{kinds}</div>
      <div class="sfilters topics" role="group" aria-label="Topic">{tops}</div>
    </div>
  </section>
  <section class="srch-list"><div class="wrap"><p id="count" class="srch-count">Loading...</p><div id="results" class="sresults"></div></div></section>"""
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": "Search Gyaanoxa", "url": "https://gyaanoxa.com/search/"}
    return page("खोजें | Search Gyaanoxa", "Search every Gyaanoxa story, Short, video and series in Hindi or English.",
                "/search/", "https://gyaanoxa.com/assets/og.jpg", body, ld, index, SEARCH_JS,
                '  <meta name="robots" content="noindex, follow">\n')


def build(public):
    items = index_items(public)
    (ROOT / "search.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8",
                                      newline="\n")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    out = ROOT / "search" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(search_page(index, len(items)), encoding="utf-8", newline="\n")
    return ["/search/"]
