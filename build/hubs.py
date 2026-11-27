"""Section pages: /videos/, /shorts/, /series/, /coming-next/, /about/, /contact/ (each section of the home page has
its own page, so visits can be counted per page), the footer's Series + Latest stories lists and /feed.xml.

Called by build.py after index.html is refreshed; the header and footer are copied from index.html (pages.page).
"""
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime

import pages
from pages import SITE, ROOT, art_url, e

FB = "https://www.facebook.com/gyaanoxa"
YT = "https://www.youtube.com/@Gyaanoxa"
IG = "https://www.instagram.com/gyaanoxa"


def absolute(body):
    """Card HTML from build.py uses 'assets/...' (home page); section pages live in sub-folders."""
    return re.sub(r'(["\s,])assets/', r'\1/assets/', body)


def crumbs_ld(name, url):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Gyaanoxa", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": SITE + url}]}


def articles():
    out = [json.loads(f.read_text(encoding="utf-8")) for f in (ROOT / "data" / "blog").glob("*.json")]
    return sorted(out, key=lambda a: (a.get("written") or "", a["slug"]), reverse=True)


def clean(t):
    return re.sub(r"\s*#\w+", "", t or "").split(" | ")[0].strip()


def footer_lists(all_series):
    series = "\n".join(f'      <a href="{pages.series_url(s["slug"])}">{e(s["title_en"])}</a>' for s in all_series)
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
    index = (ROOT / "build" / "shell.html").read_text(encoding="utf-8")
    all_series = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "series").glob("*.json"))]
    order = {"bindusara": 0, "ajatashatru": 1, "ashoka": 2, "diwali": 3}
    all_series.sort(key=lambda s: order.get(s["slug"], 9))
    import inner                                  # the same design as the home page
    pages = {"videos": inner.videos_page(longs, index), "shorts": inner.shorts_page(shorts, show, index),
             "series": inner.series_hub(index, all_series), "coming-next": inner.next_page(upcoming, index),
             "about": inner.about_page(index, *counts), "contact": inner.contact_page(index)}
    for name, html_ in pages.items():
        out = ROOT / name / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(html_, encoding="utf-8", newline="\n")
    feed()
    return [f"/{n}/" for n in pages]
