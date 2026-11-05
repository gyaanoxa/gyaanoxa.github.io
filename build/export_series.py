"""Copies a Gyaanoxa Studio series into the website: data/series/<slug>.json + real Short covers.

Run on the owner's PC (needs the studio's output folder), then commit; build.py makes the pages.
    python build/export_series.py ashoka "D:\\gyaanoxa-studio\\output\\20261030-0121-series-ashoka-..."
Keeps hand-written fields already in the JSON (quiz, years, timeline, intro_hi) when it is run again.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
KEEP = ("quiz", "years", "timeline", "intro_hi", "era", "place")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def clean(t):
    return re.sub(r"\s*#\w+", "", t or "").strip()


def best_title(yt):
    b = yt.get("best_title", 0)
    return yt["titles"][b] if isinstance(b, int) else b


def ids(d):
    f = d / "youtube_ids.json"
    return load(f) if f.exists() else {}


def cover(d, vid):
    out = ROOT / "assets" / "covers" / f"{vid}.webp"
    if out.exists():
        return
    c = sorted(d.glob("*(Short) (Cover).jpg"))
    if c:
        Image.open(c[0]).convert("RGB").resize((540, 960), Image.LANCZOS).save(out, "WEBP", quality=80, method=6)


def main(slug, src):
    src = Path(src)
    s = load(src / "series.json")
    plan = s["plan"]
    when = {x["part"]: f'{x["date"]}T{x["time"]}:00+05:30' for x in s.get("schedule", []) if isinstance(x.get("part"), int)}
    parts = []
    for i, ep in enumerate(plan["episodes"], 1):
        d = src / f"part{i}"
        sc = load(d / "script.json")
        vid = ids(d).get("short")
        if vid:
            cover(d, vid)
        parts.append({"n": i, "title": clean(sc["shorts"].get("title")), "topic": ep.get("title") or ep.get("topic", ""),
                      "hook": sc["reel_scenes"][0]["narration"], "short": vid, "at": when.get(i, "")})
    full = load(src / "full" / "script.json")
    yt = full["youtube"]
    meta = src / "full" / "render_meta.json"
    chapters = load(meta).get("chapters", []) if meta.exists() else []
    full_at = next((f'{x["date"]}T{x["time"]}:00+05:30' for x in s.get("schedule", []) if x.get("part") in ("full", 0, None)), "")
    out = ROOT / "data" / "series" / f"{slug}.json"
    old = load(out) if out.exists() else {}
    data = {
        "slug": slug,
        "title_hi": plan.get("series_title", ""),
        "title_en": plan.get("series_title_en", ""),
        "full": {"id": ids(src / "full").get("long"), "title": clean(plan.get("full_video_title") or best_title(yt)), "at": full_at,
                 "chapters": [[round(t), name] for t, name in chapters]},
        "about_en": yt.get("description_english", ""),
        "about_hi": yt.get("description_hindi", "").split("\n\n")[0],
        "facts": full.get("summary", []),
        "source": {"title": full["source"].get("title", ""), "url": full["source"].get("url", "")},
        "parts": parts,
    }
    for k in KEEP:
        if k in old:
            data[k] = old[k]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(slug, len(parts), "parts; full", data["full"]["id"], "; covers ok")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
