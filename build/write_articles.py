"""Writes the blog articles with Claude from the studio's own scripts (facts only from each video's script/summary).

Run on the owner's PC:  python build/write_articles.py [--redo] [slug ...]   (no slug = every article not written yet;
--redo writes them again even if they exist - the old file stays when Claude fails)
Output: data/blog/<slug>.json, rendered to /blog/<slug>/ by build/blog.py.
"""
import json
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
SINGLES = [
    ("kalinga-war", "20261023-0328-ashoka"),
    ("kohinoor-curse", "20261102-2228-koh-i-noor"),
    ("aurangzeb-diwali-ban", "20261023-1047-diwali"),
    ("dussehra-ravan-worship", "20261023-1111-vijayadashami"),
    ("chandragupta-maurya-origin", "20261029-1944-chandragupta-maurya"),
    ("sardar-patel-ekta-diwas", "20261030-1506-vallabhbhai-patel"),
    ("homi-bhabha-death", "20261030-1453-homi-j-bhabha"),
]


def jobs():
    out = []
    for s, folder in SER.items():
        d = OUT / folder
        n = len(json.loads((d / "series.json").read_text(encoding="utf-8"))["plan"]["episodes"])
        out.append({"slug": f"{s}-full-story", "dir": d / "full", "series": s, "part": 0, "of": n, "kind": "long"})
        for i in range(1, n + 1):
            out.append({"slug": f"{s}-part-{i}", "dir": d / f"part{i}", "series": s, "part": i, "of": n, "kind": "reel"})
    for slug, folder in SINGLES:
        out.append({"slug": slug, "dir": OUT / folder, "series": "", "part": 0, "of": 0, "kind": "long"})
    return out


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
    prompt = PROMPT.format(length=length, context=context, source=source,
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


def _run(j):
    try:
        return write(j)
    except Exception as e:  # keep going with the others
        return j["slug"], f"FAILED {str(e)[:200]}"


REDO = "--redo" in sys.argv

if __name__ == "__main__":
    want = set(a for a in sys.argv[1:] if a != "--redo")
    todo = [j for j in jobs() if not want or j["slug"] in want]
    print(len(todo), "articles", flush=True)
    with ThreadPoolExecutor(3) as ex:
        for slug, res in ex.map(_run, todo):
            print(slug, res, flush=True)
