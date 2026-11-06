"""Writes the blog articles with Claude from the studio's own scripts (facts only from each video's script/summary).

Run on the owner's PC:  python build/write_articles.py [--redo] [slug ...]   (no slug = every article not written yet;
--redo writes them again even if they exist - the old file stays when Claude fails)

The studio runs it by itself after writing a script:  write_articles.py --project <project folder> --publish
- new projects get a slug in data/projects.json (series: first word of the English series title; single video: the
  English keyword of its title), and <project>/website.json gets the article's link at once (used in descriptions)
- a series is written when its full video's script exists (the parts use its facts); export_series runs first
- --publish rebuilds the site and pushes it (commit as Gyaanoxa)
Output: data/blog/<slug>.json, rendered to /blog/<slug>/ by build/blog.py.
"""
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUDIO = Path(r"D:\gyaanoxa-studio")
OUT = STUDIO / "output"
sys.path.insert(0, str(STUDIO))
import core  # noqa: E402

SER = {"ashoka": "20261030-0121-series-ashoka-from-fierce-king-to-righteous",
       "diwali": "20261103-1436-series-5-days-of-diwali-5-legends",
       "ajatashatru": "20261105-1429-series-ajatashatru-magadha-s-rebel-son"}
REG = ROOT / "data" / "projects.json"     # projects added by the studio: {"series": {slug: folder}, "singles": {slug: folder}}
SITE = "https://gyaanoxa.com"
SINGLES = [
    ("kalinga-war", "20261023-0328-ashoka"),
    ("kohinoor-curse", "20261102-2228-koh-i-noor"),
    ("aurangzeb-diwali-ban", "20261023-1047-diwali"),
    ("dussehra-ravan-worship", "20261023-1111-vijayadashami"),
    ("chandragupta-maurya-origin", "20261029-1944-chandragupta-maurya"),
    ("sardar-patel-ekta-diwas", "20261030-1506-vallabhbhai-patel"),
    ("homi-bhabha-death", "20261030-1453-homi-j-bhabha"),
]


def registry():
    try:
        return json.loads(REG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"series": {}, "singles": {}}


def all_series():
    return {**SER, **registry()["series"]}


def all_singles():
    return SINGLES + [(k, v) for k, v in registry()["singles"].items() if k not in dict(SINGLES)]


def jobs():
    out = []
    for s, folder in all_series().items():
        d = OUT / folder
        n = len(json.loads((d / "series.json").read_text(encoding="utf-8"))["plan"]["episodes"])
        out.append({"slug": f"{s}-full-story", "dir": d / "full", "series": s, "part": 0, "of": n, "kind": "long"})
        for i in range(1, n + 1):
            out.append({"slug": f"{s}-part-{i}", "dir": d / f"part{i}", "series": s, "part": i, "of": n, "kind": "reel"})
    for slug, folder in all_singles():
        out.append({"slug": slug, "dir": OUT / folder, "series": "", "part": 0, "of": 0, "kind": "long"})
    return out


STYLE = """WRITE LIKE A HUMAN WRITER, NOT LIKE AN AI
- Sound like a good Hindi magazine writer or a friend who loves history: plain, warm, specific. Mix short and
  long sentences. Let paragraphs start in different ways.
- NEVER use these filler habits: "सोचिए" / "ज़रा सोचिए" / "कल्पना कीजिए", "आइए जानते हैं", "दिलचस्प बात यह है",
  "सवाल यह है कि", "एक बात साफ है", "यह कहानी हमें सिखाती/याद दिलाती है", "यह सिर्फ ... नहीं, बल्कि ...",
  "कहानी यहीं खत्म नहीं होती", "असल में" at the start of sentences, "यहीं से" openers.
- Use "यानी" at most twice in the whole article. No colons in headings; headings are short and plain
  (like a newspaper), not "X: Y" and not questions every time.
- No moral lessons or big summaries at the end of paragraphs. End on a concrete detail instead.
- No rhetorical questions to the reader more than twice in the whole article.
- No em dashes; use commas or full stops (।).
"""

PROMPT = """You write a blog article in natural, simple spoken HINDI (Devanagari) for the website of Gyaanoxa, a Hindi
channel about little-known truths of Indian history. The article goes with one of our videos.

STRICT RULES
- Use ONLY the facts in the SOURCE MATERIAL below (the video's research summary and narration). Do not add any fact,
  name, number or date that is not there. If the material is thin, write a shorter article - never invent.
- Legends and disputed claims must be framed as claims ("ग्रंथ कहते हैं", "किंवदंती के अनुसार", "इतिहासकार मानते हैं").
- Your own words (no copying sentences from Wikipedia). Warm, clear, storytelling tone, like explaining to a curious friend.
- Names and numbers in digits (260 ईसा पूर्व, 1,00,000). English proper nouns may appear in brackets once, e.g. अशोक (Ashoka).
- No mention of AI, prompts or "this article was written by". No links inside the text.
- {length}

{style}

Return ONLY JSON:
{{
 "title": "Hindi headline (question / number / little-known truth) | short English keyword, max 70 chars",
 "description": "1-2 sentence Hindi meta description, max 155 chars",
 "keywords": ["5-8 search phrases, Hindi and English, e.g. 'अशोक का इतिहास', 'Ashoka history in Hindi'"],
 "intro": "a gripping opening paragraph (3-4 sentences)",
 "highlights": ["4-5 one-line Hindi bullet points: what the reader will learn (each a fact from the material)"],
 "people": [["name (Hindi)", "one-line role in this story"]],
 "did_you_know": ["1-3 surprising little-known facts from the material, one sentence each"],
 "sections": [{{"h2": "Hindi sub-heading", "paras": ["paragraph", "..."]}}],
 "key_dates": [["date/when", "what happened"]],
 "faq": [{{"q": "a question people search", "a": "2-3 sentence answer from the material"}}],
 "takeaway": "2-3 sentence closing: why this story matters"
}}

{context}

SOURCE MATERIAL
Source: {source}
Research summary (facts you may use):
{summary}

Video narration (Hindi, what the video says):
{narration}
"""


def material(job):
    sc = core.load_script(job["dir"] / "script.json")
    scenes = sc.get("long_scenes") if job["kind"] == "long" else sc.get("reel_scenes")
    narration = "\n".join(s["narration"] for s in scenes or [])
    summary = sc.get("summary") or []
    if job["series"] and job["part"]:          # a part: its own Short + the series' facts
        full = core.load_script(job["dir"].parent / "full" / "script.json")
        summary = full.get("summary") or summary
    src = sc.get("source", {})
    return sc, narration, summary, f'{src.get("title", "")} - {src.get("url", "")}'


def write(job):
    out = ROOT / "data" / "blog" / f"{job['slug']}.json"
    if out.exists() and not REDO:
        return job["slug"], "exists"
    sc, narration, summary, source = material(job)
    if job["series"] and job["part"]:
        series = json.loads((job["dir"].parent / "series.json").read_text(encoding="utf-8"))["plan"]
        ep = series["episodes"][job["part"] - 1]
        context = (f"THIS ARTICLE: part {job['part']} of {job['of']} of the series '{series['series_title']}'. Focus ONLY on "
                   f"this part's topic: '{ep.get('title')}' ({ep.get('angle', '')}). Use the series facts only where they "
                   f"belong to this part; end by teasing the next part's question without answering it.")
        length = ("1100-1500 words, 5-6 sections (background, the event itself, the people, what the sources disagree on, "
                  "why it mattered), 4 FAQ, 3-5 key dates, 2-5 people.")
    elif job["series"]:
        series = json.loads((job["dir"].parent / "series.json").read_text(encoding="utf-8"))["plan"]
        context = (f"THIS ARTICLE: the complete story of the series '{series['series_title']}' "
                   f"({len(series['episodes'])} parts) - cover every part in order, one section per part.")
        length = ("2200-3000 words, one section per part plus an opening and a legacy section, 6 FAQ, 6-10 key dates, "
                  "4-8 people.")
    else:
        context = "THIS ARTICLE: the full story of this single video."
        length = ("1600-2200 words, 6-8 sections (background, the main story step by step, the people, what the sources "
                  "disagree on, legacy), 5 FAQ, 4-8 key dates, 3-6 people.")
    prompt = PROMPT.format(length=length, context=context, source=source, style=STYLE,
                           summary="\n".join(f"- {s}" for s in summary), narration=narration)
    data = core.ask_claude(prompt, log=lambda m: None,
                           validate=lambda d: isinstance(d, dict) and d.get("sections") and d.get("title"))
    ids = {}
    f = job["dir"] / "youtube_ids.json"
    if f.exists():
        ids = json.loads(f.read_text(encoding="utf-8"))
    data.update({"slug": job["slug"], "series": job["series"], "part": job["part"], "of": job["of"],
                 "video": ids.get("long") if job["kind"] == "long" else ids.get("short"),
                 "short": ids.get("short"), "source": {"title": sc.get("source", {}).get("title", ""),
                                                       "url": sc.get("source", {}).get("url", "")},
                 "written": __import__("datetime").date.today().isoformat()})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    words = sum(len(p.split()) for s in data["sections"] for p in s["paras"])
    return job["slug"], f"ok {words} words"


HUMANIZE = """Below is a Hindi blog article as JSON. Rewrite ONLY the wording so it reads like a human writer
wrote it. Keep every fact, name, number and date exactly as it is: do not add, drop or change any fact. Keep the
same JSON keys and the same number of sections, paragraphs per section (you may merge or split a little), key_dates,
faq, highlights, people and did_you_know items. key_dates dates stay identical.

{style}
Return ONLY the JSON with the same keys.

ARTICLE
{article}
"""
TEXT_KEYS = ("title", "description", "intro", "sections", "key_dates", "faq", "takeaway", "highlights", "people",
             "did_you_know", "keywords")


def numbers(x):
    return set(re.findall(r"\d[\d,.]*", json.dumps(x, ensure_ascii=False)))


def humanize(slug):
    """A style-only rewrite of an existing article (no new facts: every number must already be in the old one)."""
    f = ROOT / "data" / "blog" / f"{slug}.json"
    old = json.loads(f.read_text(encoding="utf-8"))
    part = {k: old[k] for k in TEXT_KEYS if k in old}
    new = core.ask_claude(HUMANIZE.format(style=STYLE, article=json.dumps(part, ensure_ascii=False, indent=1)),
                          log=lambda m: None,
                          validate=lambda d: isinstance(d, dict) and d.get("sections") and d.get("title"))
    extra = numbers(new) - numbers(part)
    if extra:
        return slug, f"KEPT OLD (new numbers {sorted(extra)[:5]})"
    if len(new.get("key_dates", [])) != len(part.get("key_dates", [])) or \
            [d[0] for d in new.get("key_dates", [])] != [d[0] for d in part.get("key_dates", [])]:
        return slug, "KEPT OLD (key dates changed)"
    old.update({k: new[k] for k in TEXT_KEYS if k in new})
    f.write_text(json.dumps(old, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    t = json.dumps(new, ensure_ascii=False)
    return slug, f"ok (सोचिए {t.count('सोचिए')}, यानी {t.count('यानी')})"


def _human(slug):
    try:
        return humanize(slug)
    except Exception as e:  # keep going with the others
        return slug, f"FAILED {str(e)[:200]}"


def _run(j):
    try:
        return write(j)
    except Exception as e:  # keep going with the others
        return j["slug"], f"FAILED {str(e)[:200]}"


def slugify(t):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (t or "").lower())).strip("-")[:60].rstrip("-")


def link(job, ok_only=True):
    """<project>/website.json = the article's address (the studio puts it in descriptions and the pinned comment)."""
    if ok_only and not (ROOT / "data" / "blog" / f"{job['slug']}.json").exists():
        return
    if job["dir"].exists():
        (job["dir"] / "website.json").write_text(json.dumps({"article": f"{SITE}/blog/{job['slug']}/"}) + "\n",
                                                 encoding="utf-8")


def register(project):
    """Give a studio project a place on the website; returns the jobs that belong to it."""
    d = Path(project).resolve()
    reg = registry()
    if (d.parent / "series.json").exists():
        folder = d.parent.name
        slug = next((k for k, v in all_series().items() if v == folder), None)
        if not slug:
            plan = json.loads((d.parent / "series.json").read_text(encoding="utf-8"))["plan"]
            name = (plan.get("series_title_en") or folder).split(":")[0]
            slug = slugify(name.split()[0] if len(name.split()) == 1 or name.split()[0].isalpha() else name) or slugify(folder)
            while slug in all_series():
                slug += "-2"
            reg["series"][slug] = folder
        mine = [j for j in jobs_with(reg) if j["series"] == slug]
    else:
        slug = next((k for k, v in all_singles() if v == d.name), None)
        if not slug:
            sc = core.load_script(d / "script.json")
            yt = sc.get("youtube", {})
            t = yt.get("english_title") or (yt.get("titles") or [""])[0]
            slug = slugify(t.split("|")[-1]) or slugify(sc.get("source", {}).get("title")) or slugify(d.name)
            taken = {k for k, _ in all_singles()} | {f"{s}-full-story" for s in all_series()}
            base, n = slug, 2
            while slug in taken:
                slug, n = f"{base}-{n}", n + 1
            reg["singles"][slug] = d.name
        mine = [j for j in jobs_with(reg) if j["slug"] == slug]
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return slug, mine


def jobs_with(reg):
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return jobs()


def publish():
    """Rebuild the site and push it (only the website repo, as Gyaanoxa)."""
    git = ["git", "-c", "user.name=Gyaanoxa", "-c", "user.email=351388292+gyaanoxa@users.noreply.github.com"]
    subprocess.run([sys.executable, str(ROOT / "build" / "build.py")], cwd=ROOT, check=True)
    subprocess.run(git + ["add", "-A"], cwd=ROOT, check=True)
    if subprocess.run(git + ["diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        print("publish: nothing changed")
        return
    subprocess.run(git + ["commit", "-q", "-m", "New articles from the studio"], cwd=ROOT, check=True)
    subprocess.run(git + ["pull", "-q", "--rebase"], cwd=ROOT, check=True)
    subprocess.run(git + ["push", "-q"], cwd=ROOT, check=True)
    print("publish: pushed - live on gyaanoxa.com in about a minute")


def run_all(todo):
    print(len(todo), "articles", flush=True)
    with ThreadPoolExecutor(3) as ex:
        for slug, res in ex.map(_run, todo):
            print(slug, res, flush=True)


REDO = "--redo" in sys.argv

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--humanize" in sys.argv:
        names = args or sorted(f.stem for f in (ROOT / "data" / "blog").glob("*.json"))
        with ThreadPoolExecutor(2) as ex:
            for slug, res in ex.map(_human, names):
                print(slug, res, flush=True)
        sys.exit(0)
    if "--project" in sys.argv:
        slug, mine = register(args[0])
        for j in mine:                                   # the address is known now; the page follows soon
            if Path(args[0]).resolve() == j["dir"].resolve():
                link(j, ok_only=False)
                print("link:", f"{SITE}/blog/{j['slug']}/", flush=True)
        if mine and mine[0]["series"]:
            src = mine[0]["dir"].parent
            if not (src / "full" / "script.json").exists():
                print("series: waiting for the full video's script")
                sys.exit(0)
            import export_series
            export_series.main(slug, src)
        run_all([j for j in mine if (j["dir"] / "script.json").exists()])
    else:
        run_all([j for j in jobs() if not args or j["slug"] in args])
    for j in jobs():
        link(j)
    if "--publish" in sys.argv:
        publish()
