"""Inner pages in the same design as the home page (see portal.py): a compact banner, the same section headers and the
same cards (video_card, article_card, scard, icard). Called by hubs.build and blog.build."""
import blog
from pages import ROOT, SITE, e, page, series_url
from portal import NEXT_JS, duration, icard, icon, pic, split_title, step_links, video_card
from pages import srcset

FB = "https://www.facebook.com/gyaanoxa"
YT = "https://www.youtube.com/@Gyaanoxa"
IG = "https://www.instagram.com/gyaanoxa"


def wrap(body):
    return '<div class="portal">' + body + "</div>"


def banner(crumb, chip, h1, lead, stats=(), art="", extra=""):
    """Compact page banner: crumbs, chip, headline, lead, counter tiles; `art` is an optional picture on the right."""
    tiles = "".join('<span><i class="cb-i">' + icon(ic) + '</i><em><b>' + e(n) + "</b><small>" + e(t) + "</small></em></span>" for ic, n, t in stats)
    cb = '<div class="cb">' + tiles + "</div>" if tiles else ""
    right = '<aside class="ph-r pb-art">' + art + "</aside>" if art else ""
    return ('<section class="ph pb"><div class="pw ph-grid' + (" pb-two" if art else "") + '"><div class="ph-l">'
            '<p class="pb-crumbs"><a href="/">Gyaanoxa</a> ' + icon("arrow") + " " + e(crumb) + "</p>"
            '<span class="k-chip">' + icon("spark") + " " + e(chip) + "</span><h1>" + e(h1) + "</h1>"
            '<p class="ph-lead">' + e(lead) + "</p>" + extra + cb + "</div>" + right + "</div></section>")


def section(chip, title, sub, body, more=None, alt=False, sid=""):
    head = '<div><span class="k-chip">' + e(chip) + "</span><h2>" + e(title) + "</h2>" + ("<p>" + e(sub) + "</p>" if sub else "") + "</div>"
    if more:
        head += '<a class="sh-a" href="' + more[1] + '"' + ("" if more[1].startswith("/") else ' target="_blank" rel="noopener"') + ">" + e(more[0]) + " " + icon("arrow") + "</a>"
    return '<section' + (' id="' + sid + '"' if sid else "") + ' class="ps' + (" ps-alt" if alt else "") + '"><div class="pw"><div class="sh' + (" sh-row" if more else "") + '">' + head + "</div>" + body + "</div></section>"


def follow():
    def plat(cls, ic, name, sub, href, extra=""):
        return ('<a class="fp ' + cls + '" href="' + href + '" target="_blank" rel="noopener"' + extra + '><i><svg><use href="#' + ic + '"/></svg></i>'
                "<span><b>" + name + "</b><small>" + sub + "</small></span></a>")
    return ('<section class="ps"><div class="pw"><div class="fcta"><div class="fcta-l"><img class="fcta-logo" src="/assets/logo-128.webp" alt="" width="64" height="64" loading="lazy">'
            '<div><span class="ph-live"><i></i>New story every evening, 7 PM IST</span>'
            "<h2>Never miss a story</h2><p>On YouTube, Instagram and Facebook. Free to watch, no sign-up.</p></div></div>"
            '<div class="fcta-a">' + plat("fp-yt", "i-yt", "YouTube", "Subscribe", YT + "?sub_confirmation=1")
            + plat("fp-ig", "i-ig", "Instagram", "Follow", IG) + plat("fp-fb", "i-fb", "Facebook", "Follow", FB) + "</div></div></div></section>")


def crumbs_ld(name, url):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Gyaanoxa", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": SITE + url}]}


OG = SITE + "/assets/og.jpg"


def videos_page(longs, index):
    body = banner("Documentaries", "Full videos", "Documentaries", "The whole story in one sitting: Ashoka, Diwali, the Koh-i-Noor and more. Told as one clear story in simple Hindi.",
                  [("film", str(len(longs)), "Full-length videos"), ("book", str(len(blog.load_all())), "Articles to read"), ("clock", "6 PM", "New video, IST")])
    import links
    if longs:
        f = longs[0]
        hi, en = split_title(f["title"])
        art = links.article(f["id"])
        desc = next((a.get("description", "") for a in blog.load_all().values() if a.get("video") == f["id"]), "")
        yt = "https://www.youtube.com/watch?v=" + f["id"]
        dur = duration(f["id"])
        more = [("zap", "Shorts", "One story in a minute", "/shorts/#all-shorts"), ("layers", "Story series", "Part by part, then the full video", "/series/#series"),
                ("book", "Read the stories", "The long version with dates", "/blog/"), ("clock", "History timeline", "All stories in time order", "/timeline/"),
                ("play", "YouTube channel", "@Gyaanoxa", YT)]
        vside = ('<aside class="vside"><p class="vside-h">' + icon("compass") + " More ways to explore</p>" + "".join(
            '<a href="' + h + '"' + ("" if h.startswith("/") else ' target="_blank" rel="noopener"') + '><i class="vs-i">' + icon(ic) + "</i><span><b>" + t1 + "</b><small>" + t2 + "</small></span>" + icon("arrow") + "</a>"
            for ic, t1, t2, h in more) + "</aside>")
        body += ('<section id="latest" class="ps"><div class="pw"><div class="vrow"><div class="vf"><a class="vf-im" href="' + e(art or yt) + '"><img decoding="async" ' + srcset(pic(f), 480, "(max-width: 900px) 92vw, 460px", (640, 720)) + ' alt="" width="640" height="360">'
                 '<span class="pc-p">' + icon("play") + "</span>" + ('<span class="pc-dur">' + dur + "</span>" if dur else "") + "</a>"
                 '<div class="vf-b"><span class="vf-tag">' + icon("spark") + " Latest documentary</span><h2>" + e(hi) + "</h2>"
                 + ("<small>" + e(en) + "</small>" if en else "") + links.by(f.get("published", ""))
                 + ("<p>" + e(desc) + "</p>" if desc else "")
                 + '<div class="vf-a"><a class="pc-b pri" href="' + yt + '" target="_blank" rel="noopener">' + icon("play") + " Watch on YouTube</a>"
                 + ('<a class="pc-b" href="' + e(art) + '">' + icon("book") + " Read the story</a>" if art else "") + "</div></div></div>"
                 + vside + "</div></div></section>")
    body += section("Watch", "More documentaries", "Newest first. Each one opens its story page.",
                    '<div class="g4">' + "".join(video_card(v, False) for v in longs[1:]) + "</div>", ("On YouTube", YT + "/videos"), alt=True, sid="more-docs")
    body += follow()
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Documentaries", "/videos/"),
          {"@type": "ItemList", "name": "Gyaanoxa documentaries", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": "https://www.youtube.com/watch?v=" + v["id"]} for i, v in enumerate(longs)]}]}
    return page("इतिहास की डॉक्यूमेंट्री | Indian History Documentaries",
                "Full-length Hindi documentaries on Indian history from Gyaanoxa: Ashoka, Diwali's 5 days, the Koh-i-Noor, Aurangzeb's Diwali ban and more.",
                "/videos/", OG, wrap(body), ld, index)


SHORTS_JS = """
  (function () {
    var bar = document.getElementById('sfs'), grid = document.getElementById('allshorts'), cnt = document.getElementById('scount');
    if (!bar || !grid) return;
    bar.addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-s]'); if (!b) return;
      var k = b.getAttribute('data-s'), n = 0;
      bar.querySelectorAll('.sf').forEach(function (x) { x.classList.toggle('on', x === b); });
      grid.querySelectorAll('[data-s]').forEach(function (c) { var show = k === 'all' || c.getAttribute('data-s') === k; c.hidden = !show; if (show) n++; });
      cnt.textContent = n + (n === 1 ? ' Short' : ' Shorts');
    });
  })();
"""


def shorts_page(shorts, show, index):
    top = sorted(shorts, key=lambda v: -v.get("views", 0))[:10]
    body = banner("Shorts", "Shorts", "One story in a minute", "Every Gyaanoxa Short in one place. A new one goes live every evening at 7 PM IST on YouTube, Instagram and Facebook.",
                  [("zap", str(len(shorts)), "Shorts so far"), ("clock", "7 PM", "New Short, IST"), ("film", "1 min", "One story each")])
    body += section("Popular", "Most watched", "", '<div class="g5">' + "".join(video_card(v, show) for v in top) + "</div>", ("On YouTube", YT + "/shorts"), sid="popular")
    smap = {a["short"]: a["series"] for a in blog.load_all().values() if a.get("short") and a.get("series")}
    sinfo = blog.series_info()
    counts = {}
    for v in shorts:
        k = smap.get(v["id"], "single")
        counts[k] = counts.get(k, 0) + 1
    chips = '<button type="button" class="sf on" data-s="all">' + icon("zap") + 'All <em>' + str(len(shorts)) + "</em></button>"
    for k in sorted((x for x in counts if x != "single"), key=lambda x: -counts[x]):
        name = (sinfo.get(k) or {}).get("title_en", k)
        chips += '<button type="button" class="sf" data-s="' + e(k) + '">' + e(name) + " <em>" + str(counts[k]) + "</em></button>"
    if counts.get("single"):
        chips += '<button type="button" class="sf" data-s="single">Single Shorts <em>' + str(counts["single"]) + "</em></button>"

    def tagged(v):
        return video_card(v, show).replace('<div class="pc ', '<div data-s="' + e(smap.get(v["id"], "single")) + '" class="pc ', 1)
    body += section("All Shorts", "Newest first", "", '<div class="sfilters" id="sfs" role="group" aria-label="Series">' + chips + "</div>"
                    '<p class="srch-count" id="scount">' + str(len(shorts)) + " Shorts</p>"
                    '<div class="g5 g5-all" id="allshorts">' + "".join(tagged(v) for v in shorts) + "</div>", alt=True, sid="all-shorts")
    body += follow()
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Shorts", "/shorts/")]}
    return page("1 मिनट की इतिहास कहानियाँ | Indian History Shorts in Hindi",
                "Every Gyaanoxa Short: one-minute true stories from Indian history and festivals in Hindi, new every evening at 7 PM IST.",
                "/shorts/", OG, wrap(body), ld, index, SHORTS_JS)


def series_row(d):
    """A wide series card: picture, era and years, title, part steps, and buttons for the series page and the quiz."""
    full = d.get("full") or {}
    f = ROOT / "assets" / "s" / "series" / (d["slug"] + "-720.webp")
    src = "/assets/s/series/" + d["slug"] + "-720.webp" if f.exists() else "/assets/yt/" + str(full.get("id", "")) + ".webp"
    n = len(d.get("parts", []))
    steps = step_links(d)
    meta = " · ".join(x for x in (d.get("era", ""), d.get("years", "")) if x)
    intro = (d.get("intro_hi") or "").strip()
    if len(intro) > 130:
        intro = intro[:127].rsplit(" ", 1)[0] + "..."
    url = series_url(d["slug"])
    quiz = '<a class="pc-b" href="' + url + '#quiz">' + icon("help") + " Play the quiz</a>" if d.get("quiz") else ""
    return ('<article class="sx"><a class="sx-im" href="' + url + '"><img loading="lazy" decoding="async" ' + srcset(src, 380, "(max-width: 560px) 92vw, 380px", (720,)) + ' alt="" width="720" height="450">'
            '<span class="sc-tag">' + icon("layers") + " " + str(n) + " parts</span></a>"
            '<div class="sx-b">' + ('<small class="sx-m">' + e(meta) + "</small>" if meta else "") + '<h3><a href="' + url + '">' + e(d["title_hi"]) + "</a></h3>"
            '<p class="sx-en">' + e(d["title_en"]) + "</p>" + ("<p class=\"sx-p\">" + e(intro) + "</p>" if intro else "")
            + '<span class="sc-steps">' + steps + "</span>"
            '<div class="sx-a"><a class="pc-b pri" href="' + url + '">' + icon("book") + " Open series</a>" + quiz + "</div></div></article>")


def series_hub(index, all_series):
    body = banner("Series", "Series", "Stories told part by part",
                  "A big story comes out one short part each evening. After the last part, the whole thing comes out as one full video, with an article and a quiz on its own page.",
                  [("layers", str(len(all_series)), "Story series"), ("zap", str(sum(len(s["parts"]) for s in all_series)), "Short parts"),
                   ("help", str(sum(1 for s in all_series if s.get("quiz"))), "Quizzes to play")])
    body += section("Series", "Every series has its own page", "One short part every evening, then the whole story as one video.",
                    '<div class="sxg">' + "".join(series_row(d) for d in all_series) + "</div>", sid="series")
    qs = [d for d in all_series if d.get("quiz")]
    if qs:
        body += section("Quizzes", "Test what you remember", "Five questions after every series. Pick one to play.",
                        '<div class="ixg ixg-keep">' + "".join(icard("help", d["title_hi"], f'{len(d["quiz"])} questions, {d["title_en"]}', series_url(d["slug"]) + "#quiz") for d in qs) + "</div>",
                        alt=True, sid="quizzes")
    extra = icard("clock", "History timeline", "All stories on one timeline.", "/timeline/")
    body += section("More", "Also on Gyaanoxa", "", '<div class="ixg ixg-3">' + extra + icard("book", "Articles", "The long version of every story.", "/blog/")
                    + icard("calendar", "Coming next", "What goes live next, with dates.", "/coming-next/#schedule") + "</div>", sid="more")
    body += follow()
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Series", "/series/"),
          {"@type": "ItemList", "name": "Gyaanoxa series", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": SITE + series_url(s["slug"]), "name": s["title_en"]} for i, s in enumerate(all_series)]}]}
    return page("इतिहास की कहानियाँ भाग दर भाग | Indian History Series in Hindi",
                "Gyaanoxa's story series in Hindi: Ajatashatru, Ashoka, Diwali's 5 days and more, told one part each evening and then as one full video.",
                "/series/", OG, wrap(body), ld, index)


CN_JS = """
  (function () {
    var out = document.getElementById('cn-time'), box = document.getElementById('cn-next');
    if (!out) return;
    function tick() {
      var el = document.querySelector('.up'); if (!el) { if (box) box.hidden = true; return; }
      var ms = Date.parse(el.getAttribute('data-at')) - Date.now();
      if (isNaN(ms) || ms < 0) { out.textContent = 'Now'; return; }
      var m = Math.floor(ms / 60000), d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60), mm = m % 60;
      out.textContent = d ? d + 'd ' + h + 'h' : h ? h + 'h ' + mm + 'm' : mm + 'm';
      var t = el.querySelector('h3'); var tt = document.getElementById('cn-title'); if (tt && t) tt.textContent = t.textContent;
    }
    tick(); setInterval(tick, 30000);
  })();
"""


def next_page(cards, index):
    body = banner("Coming next", "Coming next", "What is coming next",
                  "What goes live next on YouTube, Instagram and Facebook. Shorts at 7 PM IST, full videos at 6 PM, festival stories at 1 PM a day before the festival.",
                  [("zap", "7 PM", "Shorts, IST"), ("film", "6 PM", "Full videos, IST"), ("flame", "1 PM", "Festival stories")])
    rows = [("zap", "Shorts", "Every evening", "7 PM IST"), ("film", "Full videos", "Every week", "6 PM IST"), ("flame", "Festival stories", "A day before", "1 PM IST")]
    side = ('<aside class="cn-side"><div class="cn-next" id="cn-next"><span class="ph-live"><i></i>Next release in</span><b id="cn-time">...</b><small id="cn-title"></small></div>'
            '<div class="cn-plan"><p class="vside-h">' + icon("clock") + " The weekly rhythm</p>"
            + "".join('<div class="cn-row"><i class="vs-i">' + icon(ic) + "</i><span><b>" + t1 + "</b><small>" + t2 + "</small></span><em>" + t3 + "</em></div>" for ic, t1, t2, t3 in rows)
            + '<a class="cn-yt" href="' + YT + '?sub_confirmation=1" target="_blank" rel="noopener">' + icon("play") + " Subscribe so you do not miss one</a></div></aside>")
    body += section("Schedule", "Upcoming releases", "In time order. A release disappears from the list after it goes live.",
                    '<div class="cn-grid"><div><div class="upcoming rail">' + cards + "</div>"
                    '<p class="none" hidden>Nothing is scheduled right now. The next story will show up here soon.</p>'
                    '<p class="note">Festival and special-day topics are planned and may change.</p></div>' + side + "</div>", sid="schedule")
    body += follow()
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Coming next", "/coming-next/")]}
    return page("आने वाले वीडियो और Shorts | Gyaanoxa Upcoming",
                "The Gyaanoxa release schedule: upcoming Hindi Shorts, full videos and festival stories, with dates and times in IST.",
                "/coming-next/", OG, wrap(body), ld, index, NEXT_JS + CN_JS)


FAQ = [
    ("What is Gyaanoxa?", "Gyaanoxa (ज्ञानोक्सा) is a Hindi history channel. It tells the parts of Indian history that school "
     "books often skip: kings and wars, the old stories behind festivals, scientists and a few mysteries."),
    ("When do new stories come out?", "A new Short goes live every evening at 7 PM IST. A big story first comes out part by part "
     "as Shorts, and the full video follows at 6 PM after the last part. Festival stories come out at 1 PM a day before the festival."),
    ("Where does the information come from?", "From history books, inscriptions and encyclopaedias, mostly Wikipedia and the "
     "sources it cites. Every video description names its source. Legends are told as legends, for example \"the old books say\"."),
    ("Whose pictures are in the videos?", "Old paintings and photos come from places like Wikimedia Commons, and each artist and "
     "licence is listed in the video description. Some scenes are drawn only to explain the story, and they are not real photos."),
    ("Where can I watch?", "On YouTube (@Gyaanoxa), Instagram (@gyaanoxa) and Facebook (facebook.com/gyaanoxa). The long version "
     "of every story is on this website's Blog."),
    ("I found a mistake. What should I do?", "Write to gyaanoxa@gmail.com with the source. A mistake reported with a source is "
     "fixed in the article and in the next video."),
    ("Can I suggest a topic?", "Yes. Many stories on the channel started as a viewer's question. Send the name of the king, "
     "battle, festival or mystery, and where you read about it."),
]

STEPS = [
    ("search", "1. Pick the story", "Topics come from viewers' questions, festival dates and the stories that fit the timeline next."),
    ("book", "2. Read the sources", "History books, inscriptions and encyclopaedias. Every story is told as one clear account."),
    ("scroll", "3. Write in simple Hindi", "One clear story for a one minute Short, and a longer version for the full video and the article."),
    ("shield", "4. Pictures with credit", "Old paintings and photos are credited by name and licence. Drawn scenes only explain what words cannot."),
    ("play", "5. Publish everywhere", "YouTube, Instagram and Facebook at 7 PM IST, then the long article goes up on this website."),
    ("mail", "6. Listen and fix", "Comments and emails decide the next topics, and every correction with a source is applied."),
]


def about_page(index, n_videos, n_series, n_articles):
    from portal import TOPICS
    steps = "".join('<div class="stp"><span class="stp-n">' + str(k) + "</span><i class=\"wy-i\">" + icon(ic) + "</i><b>" + e(t) + "</b><p>" + e(d) + "</p></div>"
                    for k, (ic, t, d) in enumerate(STEPS, 1))
    faq = "".join('<details class="faq-q"><summary>' + e(q) + "</summary><p>" + e(a) + "</p></details>" for q, a in FAQ)
    body = banner("About", "About", "About Gyaanoxa",
                  "A Hindi channel about the parts of Indian history that textbooks skip: kings and wars, festivals, scientists and a few old mysteries. Told in the Hindi we speak at home, with the sources named.",
                  [("film", str(n_videos), "Videos & Shorts"), ("layers", str(n_series), "Story series"), ("book", str(n_articles), "Stories to read"), ("clock", "7 PM", "New Short, IST")],
                  art='<img class="pb-logo" src="/assets/stacked.webp" alt="Gyaanoxa, भारत के अनसुने सच" width="600" height="520">')
    promise = ["Facts from named sources, and legends clearly marked as legends", "One clear story, told in simple Hindi",
               "No misleading titles: the title says what the video shows", "A new Short every evening and a full video after every series",
               "Credit for every picture's artist and licence"]
    body += ('<section id="story" class="ps"><div class="pw"><div class="abg"><div class="ab-story"><span class="k-chip">' + icon("users") + " Our story</span><h2>Why Gyaanoxa exists</h2>"
             "<p class=\"ab-big\">Most of us learned history as a list of dates. The real stories, like a prince who locked up his own father or an emperor who carved his regret in stone, were left out.</p>"
             "<p>Gyaanoxa tells those stories the way they were told at home: simply, in Hindi, one story at a time.</p>"
             "<p>The name comes from ज्ञान (knowledge). Every story stays close to its sources, so you can enjoy it and still trust it.</p></div>"
             '<div class="ab-prom"><span class="k-chip">' + icon("shield") + " Our promise</span><h2>What you can expect</h2><ul>"
             + "".join("<li>" + icon("check") + "<span>" + x + "</span></li>" for x in promise) + "</ul></div></div></div></section>")
    body += section("How we work", "How a story is made", "Six steps, from a viewer's question to a fixed correction.", '<div class="g3 stg">' + steps + "</div>", alt=True, sid="how")
    chips = "".join('<a href="/search/?q=' + e(x.replace(" ", "+")) + '">' + e(x) + "</a>" for x in TOPICS)
    body += section("Topics", "What we cover", "Ancient India, festivals, mysteries and modern India. Tap a name to see every story about it.",
                    '<div class="chips">' + chips + '</div><p class="ab-more"><a class="sh-a" href="/timeline/">See every story on the timeline ' + icon("arrow") + "</a></p>", sid="topics")
    body += section("Where to find us", "Where to watch", "", '<div class="ixg ixg-4">' + icard("play", "YouTube", "@Gyaanoxa, Shorts and full videos.", YT) + icard("zap", "Instagram", "@gyaanoxa, Reels every evening.", IG)
                    + icard("users", "Facebook", "facebook.com/gyaanoxa, Reels and posters.", FB) + icard("book", "Blog", "The long version of every story.", "/blog/") + "</div>", alt=True, sid="watch")
    body += section("FAQ", "Frequently asked questions", "", '<div class="faq-list faq-2">' + faq + "</div>", sid="faq")
    body += follow()
    ld = {"@context": "https://schema.org", "@graph": [
        crumbs_ld("About", "/about/"),
        {"@type": "AboutPage", "name": "About Gyaanoxa", "url": SITE + "/about/", "inLanguage": "hi"},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}]}
    return page("Gyaanoxa के बारे में | Indian History in Simple Hindi",
                "About Gyaanoxa: a Hindi channel of true stories from Indian history and festivals. How a story is made, where to watch, and answers to common questions.",
                "/about/", OG, wrap(body), ld, index)


COPY_JS = """
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var done = function () { var s = b.querySelector('span'); var old = s.textContent; s.textContent = 'Copied'; b.classList.add('ok'); setTimeout(function () { s.textContent = old; b.classList.remove('ok'); }, 1800); };
      if (navigator.clipboard) { navigator.clipboard.writeText(b.getAttribute('data-copy')).then(done); }
    });
  });
"""


def contact_page(index):
    mail = "gyaanoxa@gmail.com"
    body = banner("Contact", "Contact", "Contact Gyaanoxa", "Got a topic idea, spotted a mistake, or want to work together? Write to us. We read every message.",
                  [("mail", "1", "Email, the best way"), ("users", "3", "Social pages"), ("check", "4", "Ways to write to us")],
                  art='<img class="pb-logo pb-round" src="/assets/logo.webp" alt="Gyaanoxa logo" width="256" height="256">')
    pts = [("search", "Story idea", "Story%20idea", "A king, a battle, a festival or a mystery you want to hear about. Tell us where you read about it."),
           ("check", "Correction", "Correction", "Found a wrong date or name? Send the source. Fixes go into the next video and the article."),
           ("book", "Pictures and credits", "Picture%20credit", "If a picture in a video is yours and the credit is missing or wrong, write and we will fix it."),
           ("users", "Working together", "Working%20together", "Schools, museums, writers and other channels: we are happy to talk about history projects.")]
    tiles = "".join('<a class="ctile" href="mailto:' + mail + "?subject=" + sj + '"><i class="wy-i">' + icon(ic) + "</i><span><b>" + t + "</b><small>" + d + '</small></span><em class="ctile-go">' + icon("arrow") + "</em></a>"
                    for ic, t, sj, d in pts)
    body += ('<section id="write" class="ps"><div class="pw"><div class="cgrid"><div class="cmail"><span class="k-chip">' + icon("mail") + " Email</span>"
             '<h2>' + mail + '</h2><p>Email is the best way to reach us. A short subject line helps, like "Story idea" or "Correction".</p>'
             '<div class="cmail-a"><a class="btn" href="mailto:' + mail + '">' + icon("mail") + ' Write an email</a>'
             '<button class="btn ghost" type="button" data-copy="' + mail + '">' + icon("check") + "<span>Copy email</span></button></div>"
             '<p class="cmail-n">' + icon("shield") + " We read every message. A correction with a source is applied to the article and the next video.</p></div>"
             '<div class="cwhat"><p class="cwhat-h">' + icon("spark") + " What would you like to write about?</p>" + tiles + "</div></div></div></section>")
    body += section("Social", "Message us here too", "", '<div class="ixg ixg-3">' + icard("play", "YouTube", "Comment on any video.", YT) + icard("zap", "Instagram", "DM @gyaanoxa.", IG)
                    + icard("users", "Facebook", "Message the Gyaanoxa Page.", FB) + "</div>", alt=True, sid="social")
    body += follow()
    ld = {"@context": "https://schema.org", "@graph": [
        crumbs_ld("Contact", "/contact/"),
        {"@type": "ContactPage", "name": "Contact Gyaanoxa", "url": SITE + "/contact/",
         "mainEntity": {"@type": "Organization", "name": "Gyaanoxa", "email": mail, "url": SITE + "/", "sameAs": [YT, IG, FB]}}]}
    return page("संपर्क करें, कहानी सुझाएँ | Contact Gyaanoxa",
                "Contact Gyaanoxa: suggest a story from Indian history, send a correction or talk about working together. Email gyaanoxa@gmail.com.",
                "/contact/", OG, wrap(body), ld, index, COPY_JS)
