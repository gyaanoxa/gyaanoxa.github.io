"""Where a video can be watched and read: YouTube (the default), Instagram and Facebook, and its article.

data/social.json maps a YouTube id to the same video's Instagram / Facebook posts:
    {"<youtube id>": {"ig": "https://www.instagram.com/reel/...", "fb": "https://www.facebook.com/reel/..."}}
Without an entry the icon opens the channel's Reels page on that platform.
"""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YT = "https://www.youtube.com/@Gyaanoxa"
IG_REELS = "https://www.instagram.com/gyaanoxa/reels/"
FB_REELS = "https://www.facebook.com/gyaanoxa/reels/"
FB_VIDEOS = "https://www.facebook.com/gyaanoxa/videos/"


def esc(s):
    import html
    return html.escape(str(s or ""), quote=True)


@lru_cache(maxsize=1)
def social():
    f = ROOT / "data" / "social.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


@lru_cache(maxsize=1)
def articles_by_video():
    """{youtube id: article slug} from the articles' video / short fields and the series' full videos."""
    out = {}
    for f in sorted((ROOT / "data" / "blog").glob("*.json")):
        a = json.loads(f.read_text(encoding="utf-8"))
        for k in ("short", "video"):
            if a.get(k):
                out.setdefault(a[k], a["slug"])
    for f in (ROOT / "data" / "series").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        fid = (d.get("full") or {}).get("id")
        if fid and (ROOT / "data" / "blog" / f"{d['slug']}-full-story.json").exists():
            out[fid] = f"{d['slug']}-full-story"
    return out


def article(vid):
    slug = articles_by_video().get(vid or "")
    return f"/blog/{slug}/" if slug else ""


def yt_url(vid, short):
    return f"https://www.youtube.com/shorts/{vid}" if short else f"https://www.youtube.com/watch?v={vid}"


def urls(vid, short):
    """(youtube, instagram, facebook) for one video. Long videos are not on Instagram."""
    s = social().get(vid or "", {})
    ig = s.get("ig") or (IG_REELS if short else "")
    fb = s.get("fb") or (FB_REELS if short else "")       # full videos are only on YouTube
    return yt_url(vid, short), ig, fb


def icons(vid, short, cls="plat"):
    """Three small platform buttons: each opens this video on that platform."""
    yt, ig, fb = urls(vid, short)
    out = [f'<a class="pi yt" href="{esc(yt)}" target="_blank" rel="noopener" aria-label="Watch on YouTube" title="YouTube">'
           f'<svg><use href="#i-yt"/></svg></a>']
    if fb:
        out.append(f'<a class="pi fb" href="{esc(fb)}" target="_blank" rel="noopener" aria-label="Watch on Facebook" title="Facebook">'
                   f'<svg><use href="#i-fb"/></svg></a>')
    if ig:
        out.append(f'<a class="pi ig" href="{esc(ig)}" target="_blank" rel="noopener" aria-label="Watch on Instagram" title="Instagram">'
                   f'<svg><use href="#i-ig"/></svg></a>')
    return f'<span class="{cls}">{"".join(out)}</span>'


def read_link(vid, label="Read article"):
    url = article(vid)
    return f'<a class="read-a" href="{url}"><svg><use href="#i-book"/></svg>{esc(label)}</a>' if url else ""


def buttons(vid, short):
    """Big buttons for an article / series page: YouTube first, then Facebook and Instagram."""
    yt, ig, fb = urls(vid, short)
    out = f'<a class="btn" href="{esc(yt)}" target="_blank" rel="noopener"><svg><use href="#i-yt"/></svg>Watch on YouTube</a>'
    if fb:
        out += f'<a class="btn ghost" href="{esc(fb)}" target="_blank" rel="noopener"><svg><use href="#i-fb"/></svg>Facebook</a>'
    if ig:
        out += f'<a class="btn ghost" href="{esc(ig)}" target="_blank" rel="noopener"><svg><use href="#i-ig"/></svg>Instagram</a>'
    return out


@lru_cache(maxsize=1)
def _descs():
    """{youtube id: one or two sentences about it}: the article's description, else the series part's hook."""
    out = {}
    for f in (ROOT / "data" / "series").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d.get("parts", []):
            if p.get("short") and p.get("hook"):
                out[p["short"]] = p["hook"]
        fid = (d.get("full") or {}).get("id")
        if fid and d.get("intro_hi"):
            out[fid] = d["intro_hi"]
    for f in sorted((ROOT / "data" / "blog").glob("*.json")):
        a = json.loads(f.read_text(encoding="utf-8"))
        for k in ("short", "video"):
            if a.get(k) and a.get("description"):
                out[a[k]] = a["description"]
    return out


def desc(vid, limit=160):
    t = " ".join(_descs().get(vid or "", "").split())
    return t if len(t) <= limit else t[:limit].rsplit(" ", 1)[0] + "…"


def highlights(vid, n=3):
    """The first points of the video's article ("What you will learn"), for the big featured card."""
    slug = articles_by_video().get(vid or "")
    if not slug:
        return []
    a = json.loads((ROOT / "data" / "blog" / f"{slug}.json").read_text(encoding="utf-8"))
    return a.get("highlights", [])[:n]
