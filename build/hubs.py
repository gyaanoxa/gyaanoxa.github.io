"""Section pages: /videos/, /shorts/, /series/, /coming-next/, /about/, /contact/ (each section of the home page has
its own page, so visits can be counted per page), the footer's Series + Latest stories lists and /feed.xml.

Called by build.py after index.html is refreshed; the header and footer are copied from index.html (pages.page).
"""
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime

from pages import SITE, ROOT, art_url, e, page

FB = "https://www.facebook.com/gyaanoxa"
YT = "https://www.youtube.com/@Gyaanoxa"
IG = "https://www.instagram.com/gyaanoxa"


def absolute(body):
    """Card HTML from build.py uses 'assets/...' (home page); section pages live in sub-folders."""
    return re.sub(r'(["\s,])assets/', r'\1/assets/', body)


def hero(crumb, eyebrow, h1, lead, extra="", side=""):
    """Page header; `side` (a logo picture) sits on the right on wide screens."""
    text = f"""<p class="crumbs"><a href="/">Gyaanoxa</a> › {e(crumb)}</p>
      <p class="eyebrow">{e(eyebrow)}</p>
      <h1>{e(h1)}</h1>
      <p class="lead">{e(lead)}</p>{extra}"""
    if side:
        return f"""  <section class="sp-hero">
    <div class="wrap hero-side">
      <div>{text}</div>
      <div class="hs-art">{side}</div>
    </div>
  </section>
"""
    return f"""  <section class="sp-hero">
    <div class="wrap">
      {text}
    </div>
  </section>
"""


def crumbs_ld(name, url):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Gyaanoxa", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": SITE + url}]}


FOLLOW = f"""
  <section>
    <div class="wrap">
      <div class="cta">
        <h2>Never miss a story</h2>
        <p class="sub">A new story every evening at 7 PM IST on YouTube, Instagram and Facebook.</p>
        <div class="actions">
          <a class="btn" href="{YT}?sub_confirmation=1" target="_blank" rel="noopener"><svg><use href="#i-yt"/></svg>Subscribe</a>
          <a class="btn ghost" href="{IG}" target="_blank" rel="noopener"><svg><use href="#i-ig"/></svg>Instagram</a>
          <a class="btn ghost" href="{FB}" target="_blank" rel="noopener"><svg><use href="#i-fb"/></svg>Facebook</a>
        </div>
      </div>
    </div>
  </section>"""


def videos_page(longs, doc_card, index):
    cards = "\n".join(doc_card(v, i == 0) for i, v in enumerate(longs))
    body = hero("Documentaries", "Full videos", "Documentaries", "The whole story in one sitting: Ashoka, Diwali, the Koh-i-Noor and more. "
                "Where the old books disagree, you hear both sides.") + f"""
  <section>
    <div class="wrap">
      <div class="head"><div><p class="eyebrow">{len(longs)} videos</p><h2>Every full-length video</h2>
      <p class="sub">Newest first. Each one opens on YouTube.</p></div>
      <a class="more" href="{YT}/videos" target="_blank" rel="noopener">On YouTube</a></div>
      <div class="docs">
{absolute(cards)}
      </div>
    </div>
  </section>{FOLLOW}"""
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Documentaries", "/videos/"),
          {"@type": "ItemList", "name": "Gyaanoxa documentaries", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": f"https://www.youtube.com/watch?v={v['id']}"}
              for i, v in enumerate(longs)]}]}
    return page("Documentaries | Indian History in Hindi | Gyaanoxa",
                "Full-length Hindi documentaries on Indian history from Gyaanoxa: Ashoka, Diwali's 5 days, the Koh-i-Noor, "
                "Aurangzeb's Diwali ban and more.", "/videos/", f"{SITE}/assets/og.jpg", body, ld, index)


def shorts_page(shorts, short_card, show, index):
    latest = "\n".join(short_card(v, show) for v in shorts)
    top = "\n".join(short_card(v, show) for v in sorted(shorts, key=lambda v: -v["views"])[:12])
    body = hero("Shorts", "Shorts", "One story in a minute", "Every Gyaanoxa Short in one place. A new one goes live every evening at 7 PM IST "
                "on YouTube, Instagram and Facebook.") + f"""
  <section>
    <div class="wrap">
      <div class="head"><div><p class="eyebrow">Popular</p><h2>Most watched</h2></div>
      <a class="more" href="{YT}/shorts" target="_blank" rel="noopener">On YouTube</a></div>
      <div class="shorts grid">
{absolute(top)}
      </div>
    </div>
  </section>
  <section>
    <div class="wrap">
      <div class="head"><div><p class="eyebrow">All Shorts · {len(shorts)}</p><h2>Newest first</h2></div></div>
      <div class="shorts grid">
{absolute(latest)}
      </div>
    </div>
  </section>{FOLLOW}"""
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Shorts", "/shorts/")]}
    return page("Shorts | 1 Minute History Stories in Hindi | Gyaanoxa",
                "Every Gyaanoxa Short: one-minute true stories from Indian history and festivals in Hindi, new every evening at 7 PM IST.",
                "/shorts/", f"{SITE}/assets/og.jpg", body, ld, index)


def series_page(index, all_series):
    home = index[index.index('<div class="series reveal">'):]
    cards = home[:home.index("</section>")]
    cards = cards[:cards.rindex("</div>")]                       # drop the .wrap closing tag
    cards = absolute(cards.replace("series reveal", "series"))
    rows = "".join(f'<a class="other" href="/{e(s["slug"])}/"><b>{e(s["title_hi"])}</b><span>{e(s["title_en"])} · '
                   f'{len(s["parts"])} parts + full video</span></a>' for s in all_series)
    body = hero("Series", "Series", "Stories told part by part", "A big story comes out one short part each evening. After the last part, "
                "the whole thing comes out as one full video, with an article and a quiz on its own page.") + f"""
  <section>
    <div class="wrap">
      {cards}
    </div>
  </section>
  <section>
    <div class="wrap">
      <p class="eyebrow">All series</p><h2>Every series has its own page</h2>
      <div class="others">{rows}<a class="other" href="/timeline/"><b>History timeline</b><span>All stories on one timeline</span></a></div>
    </div>
  </section>{FOLLOW}"""
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Series", "/series/"),
          {"@type": "ItemList", "name": "Gyaanoxa series", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": f"{SITE}/{s['slug']}/", "name": s["title_en"]}
              for i, s in enumerate(all_series)]}]}
    return page("Series | Indian History Stories Part by Part | Gyaanoxa",
                "Gyaanoxa's story series in Hindi: Ajatashatru, Ashoka, Diwali's 5 days and more, told one part each evening "
                "and then as one full video.", "/series/", f"{SITE}/assets/og.jpg", body, ld, index)


NEXT_JS = """
  (function () {
    var now = Date.now(), first = true, shown = 0;
    document.querySelectorAll('.up').forEach(function (el) {
      var t = Date.parse(el.getAttribute('data-at'));
      if (isNaN(t) || t < now) { el.remove(); return; }
      if (first) { el.classList.add('next'); first = false; }
      shown++;
    });
    if (!shown) { var n = document.querySelector('.none'); if (n) n.hidden = false; }
  })();
"""


def next_page(cards, index):
    body = hero("Coming next", "Coming next", "What is coming next", "What goes live next on YouTube, Instagram and Facebook. Shorts at "
                "7 PM IST, full videos at 6 PM, festival stories at 1 PM a day before the festival.") + f"""
  <section>
    <div class="wrap">
      <div class="upcoming">
{cards}
      </div>
      <p class="none" hidden>Nothing is scheduled right now. The next story will show up here soon.</p>
      <p class="note">Festival and special-day topics are planned and may change.</p>
    </div>
  </section>{FOLLOW}"""
    ld = {"@context": "https://schema.org", "@graph": [crumbs_ld("Coming next", "/coming-next/")]}
    return page("Coming next | Upcoming Videos and Shorts | Gyaanoxa",
                "The Gyaanoxa release schedule: upcoming Hindi Shorts, full videos and festival stories, with dates and times in IST.",
                "/coming-next/", f"{SITE}/assets/og.jpg", body, ld, index, NEXT_JS)


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
    ("1. Pick the story", "Topics come from viewers' questions, festival dates and the stories that fit the timeline next."),
    ("2. Read the sources", "History books, inscriptions and encyclopaedias. Where two old texts disagree, both versions are noted."),
    ("3. Write in simple Hindi", "One clear story for a one minute Short, and a longer version for the full video and the article."),
    ("4. Pictures with credit", "Old paintings and photos are credited by name and licence. Drawn scenes only explain what words cannot."),
    ("5. Publish everywhere", "YouTube, Instagram and Facebook at 7 PM IST, then the long article goes up on this website."),
    ("6. Listen and fix", "Comments and emails decide the next topics, and every correction with a source is applied."),
]


def about_page(index, n_videos, n_series, n_articles):
    faq = "".join(f'<details class="faq-q"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in FAQ)
    steps = "".join(f'<div class="point"><h3>{e(t)}</h3><p>{e(d)}</p></div>' for t, d in STEPS)
    body = hero("About", "About", "About Gyaanoxa", "A Hindi channel about the parts of Indian history that textbooks skip: kings and wars, "
                "festivals, scientists and a few old mysteries. Told in the Hindi we speak at home, with the sources named.",
                side='<img class="hs-stacked" src="/assets/stacked.webp" alt="Gyaanoxa, भारत के अनसुने सच" width="600" height="520">') + f"""
  <section>
    <div class="wrap two">
      <div>
        <p class="eyebrow">Our story</p><h2>Why Gyaanoxa exists</h2>
        <p class="sub">Most of us learned history as a list of dates. The real stories, like a prince who locked up his own father
        or an emperor who carved his regret in stone, were left out. Gyaanoxa tells those stories the way they were told at home:
        simply, in Hindi, one story at a time.</p>
        <p class="sub">The name comes from ज्ञान (knowledge). Every story stays close to its sources, so you can enjoy it and still
        trust it.</p>
      </div>
      <div>
        <p class="eyebrow">Our promise</p><h2>What you can expect</h2>
        <ul class="sp-facts">
          <li>Facts from named sources, and legends clearly marked as legends</li>
          <li>Both sides when old books disagree</li>
          <li>No misleading titles: the title says what the video shows</li>
          <li>A new Short every evening and a full video after every series</li>
          <li>Credit for every picture's artist and licence</li>
        </ul>
      </div>
    </div>
  </section>
  <section>
    <div class="wrap">
      <div class="stats-row">
        <div class="stat"><b>{n_videos}</b><span>videos &amp; Shorts</span></div>
        <div class="stat"><b>{n_series}</b><span>story series</span></div>
        <div class="stat"><b>{n_articles}</b><span>stories to read</span></div>
        <div class="stat"><b>7<em> PM</em></b><span>new Short every evening</span></div>
      </div>
    </div>
  </section>
  <section>
    <div class="wrap">
      <p class="eyebrow">How we work</p><h2>How a story is made</h2>
      <div class="points steps">{steps}</div>
    </div>
  </section>
  <section>
    <div class="wrap two">
      <div>
        <p class="eyebrow">Topics</p><h2>What we cover</h2>
        <ul class="sp-facts">
          <li>Ancient India: Magadha, the Mauryas, Ashoka, Ajatashatru, Chandragupta</li>
          <li>Festivals and the stories behind them: Diwali, Chhath, Dussehra</li>
          <li>Mysteries and famous objects, like the Koh-i-Noor</li>
          <li>Modern India: Sardar Patel, Homi Bhabha and the people who built the country</li>
        </ul>
        <p class="src">See every story in time order on the <a href="/timeline/">history timeline</a>.</p>
      </div>
      <div>
        <p class="eyebrow">Where to find us</p><h2>Where to watch</h2>
        <div class="others one">
          <a class="other" href="{YT}" target="_blank" rel="noopener"><b>YouTube</b><span>@Gyaanoxa · Shorts and full videos</span></a>
          <a class="other" href="{IG}" target="_blank" rel="noopener"><b>Instagram</b><span>@gyaanoxa · Reels every evening</span></a>
          <a class="other" href="{FB}" target="_blank" rel="noopener"><b>Facebook</b><span>facebook.com/gyaanoxa · Reels and posters</span></a>
          <a class="other" href="/blog/"><b>Blog</b><span>The long version of every story</span></a>
        </div>
      </div>
    </div>
  </section>
  <section>
    <div class="wrap">
      <p class="eyebrow">FAQ</p><h2>Frequently asked questions</h2>
      <div class="faq-list">{faq}</div>
    </div>
  </section>{FOLLOW}"""
    ld = {"@context": "https://schema.org", "@graph": [
        crumbs_ld("About", "/about/"),
        {"@type": "AboutPage", "name": "About Gyaanoxa", "url": f"{SITE}/about/", "inLanguage": "hi"},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                                            for q, a in FAQ]}]}
    return page("About Gyaanoxa | Indian History in Simple Hindi",
                "About Gyaanoxa: a Hindi channel of true stories from Indian history, festivals and mysteries, with sources named. "
                "How a story is made, where to watch, and answers to common questions.", "/about/", f"{SITE}/assets/og.jpg",
                body, ld, index)


def contact_page(index):
    body = hero("Contact", "Contact", "Contact Gyaanoxa", "Got a topic idea, spotted a mistake, or want to work together? Write to us. "
                "We read every message.", side='<img class="hs-round" src="/assets/logo.webp" alt="Gyaanoxa logo" width="256" height="256">') + f"""
  <section>
    <div class="wrap">
      <div class="cta">
        <h2>gyaanoxa@gmail.com</h2>
        <p class="sub">Email is the best way to reach us. A short subject line helps, like "Story idea" or "Correction".</p>
        <div class="actions">
          <a class="btn" href="mailto:gyaanoxa@gmail.com"><svg><use href="#i-mail"/></svg>Write an email</a>
          <a class="btn ghost" href="mailto:gyaanoxa@gmail.com?subject=Story%20idea"><svg><use href="#i-spark"/></svg>Suggest a story</a>
        </div>
      </div>
    </div>
  </section>
  <section>
    <div class="wrap">
      <p class="eyebrow">What to write about</p><h2>What you can write to us about</h2>
      <div class="points">
        <div class="point"><h3>Story ideas</h3><p>A king, a battle, a festival or a mystery you want to hear about. Tell us where you read about it.</p></div>
        <div class="point"><h3>Corrections</h3><p>Found a wrong date or name? Send the source. Fixes go into the next video and the article.</p></div>
        <div class="point"><h3>Pictures and credits</h3><p>If a picture in a video is yours and the credit is missing or wrong, write and we will fix it.</p></div>
        <div class="point"><h3>Working together</h3><p>Schools, museums, writers and other channels: we are happy to talk about history projects.</p></div>
      </div>
    </div>
  </section>
  <section>
    <div class="wrap">
      <p class="eyebrow">Social</p><h2>Message us here too</h2>
      <div class="others">
        <a class="other" href="{YT}" target="_blank" rel="noopener"><b>YouTube</b><span>Comment on any video</span></a>
        <a class="other" href="{IG}" target="_blank" rel="noopener"><b>Instagram</b><span>DM @gyaanoxa</span></a>
        <a class="other" href="{FB}" target="_blank" rel="noopener"><b>Facebook</b><span>Message the Gyaanoxa Page</span></a>
      </div>
    </div>
  </section>"""
    ld = {"@context": "https://schema.org", "@graph": [
        crumbs_ld("Contact", "/contact/"),
        {"@type": "ContactPage", "name": "Contact Gyaanoxa", "url": f"{SITE}/contact/",
         "mainEntity": {"@type": "Organization", "name": "Gyaanoxa", "email": "gyaanoxa@gmail.com", "url": SITE + "/",
                        "sameAs": [YT, IG, FB]}}]}
    return page("Contact Gyaanoxa | Suggest a Story", "Contact Gyaanoxa: suggest a story from Indian history, send a correction "
                "or talk about working together. Email gyaanoxa@gmail.com.", "/contact/", f"{SITE}/assets/og.jpg", body, ld, index)


def articles():
    out = [json.loads(f.read_text(encoding="utf-8")) for f in (ROOT / "data" / "blog").glob("*.json")]
    return sorted(out, key=lambda a: (a.get("written") or "", a["slug"]), reverse=True)


def clean(t):
    return re.sub(r"\s*#\w+", "", t or "").split(" | ")[0].strip()


def footer_lists(all_series):
    series = "\n".join(f'      <a href="/{e(s["slug"])}/">{e(s["title_en"])}</a>' for s in all_series)
    series += '\n      <a href="/series/">All series →</a>'
    reads = "\n".join(f'      <a href="{art_url(a["slug"])}">{e(clean(a["title"]))}</a>' for a in articles()[:5])
    reads += '\n      <a href="/blog/">All articles →</a>'
    return series, reads


def feed():
    items = []
    for a in articles()[:30]:
        try:
            when = datetime.fromisoformat((a.get("written") or "")[:10]).replace(tzinfo=timezone.utc)
        except ValueError:
            when = datetime.now(timezone.utc)
        url = f"{SITE}{art_url(a['slug'])}"
        items.append(f"<item><title>{e(clean(a['title']))}</title><link>{url}</link><guid>{url}</guid>"
                     f"<pubDate>{format_datetime(when)}</pubDate><description>{e(a.get('description', ''))}</description></item>")
    (ROOT / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Gyaanoxa: भारत के अनसुने सच</title>'
        f'<link>{SITE}/</link><description>True stories from Indian history in simple Hindi.</description><language>hi</language>'
        + "".join(items) + "</channel></rss>\n", encoding="utf-8", newline="\n")


def build(longs, shorts, upcoming, doc_card, short_card, show, counts):
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    all_series = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "series").glob("*.json"))]
    order = {"ajatashatru": 0, "ashoka": 1, "diwali": 2}
    all_series.sort(key=lambda s: order.get(s["slug"], 9))
    pages = {"videos": videos_page(longs, doc_card, index), "shorts": shorts_page(shorts, short_card, show, index),
             "series": series_page(index, all_series), "coming-next": next_page(upcoming, index),
             "about": about_page(index, *counts), "contact": contact_page(index)}
    for name, html_ in pages.items():
        out = ROOT / name / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(html_, encoding="utf-8", newline="\n")
    feed()
    return [f"/{n}/" for n in pages]
