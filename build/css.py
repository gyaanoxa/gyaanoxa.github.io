"""One small stylesheet for every page: style.css + portal.css, minified and trimmed, written to site.min.css.

The two source files stay as they are (edit those). At the end of the build, site.min.css is made from them:
comments and spaces are removed, and rules whose class or id names appear nowhere in the site's pages or scripts are
dropped (a name counts as used when the word appears anywhere in a page, an inline script or a .js file, so classes added
by scripts are kept; classes of a state that is not on any page today come back at the next build when that state appears). Every page links it as /site.min.css?v=<code>; the code changes when the
file changes, so a new version is never served from an old cache."""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS = ("style.css", "portal.css")
_KEEP = re.compile(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|url\([^)]*\))')
LINK = re.compile(r"/site\.min\.css\?v=\w+")


def minify(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    keep = []

    def hold(m):
        keep.append(m.group(0))
        return "\x00%d\x00" % (len(keep) - 1)

    css = _KEEP.sub(hold, css)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    css = css.replace(";}", "}")
    css = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], css)
    return css.strip()


def _split(text, sep):
    """Split on sep outside (), [] and strings."""
    out, depth, cur, q = [], 0, [], ""
    for ch in text:
        if q:
            cur.append(ch)
            if ch == q:
                q = ""
            continue
        if ch in "\"'":
            q = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def _blocks(css):
    """Yield (prelude, body) for each top-level rule or at-rule of minified css."""
    i, n = 0, len(css)
    while i < n:
        j = i
        depth_paren, q = 0, ""
        while j < n:
            ch = css[j]
            if q:
                if ch == q:
                    q = ""
            elif ch in "\"'":
                q = ch
            elif ch == "(":
                depth_paren += 1
            elif ch == ")":
                depth_paren -= 1
            elif depth_paren == 0 and ch in "{;":
                break
            j += 1
        if j >= n:
            break
        prelude = css[i:j]
        if css[j] == ";":
            yield prelude, None
            i = j + 1
            continue
        depth, k, q = 1, j + 1, ""
        while k < n and depth:
            ch = css[k]
            if q:
                if ch == q:
                    q = ""
            elif ch in "\"'":
                q = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            k += 1
        yield prelude, css[j + 1:k - 1]
        i = k


# classes added by other people's scripts (Google Translate) are never on our pages, but their rules must stay
EXTERNAL = ("goog-", "VIpgJd", "skiptranslate", "notranslate")
_TOK = re.compile(r"[.#]([A-Za-z_][\w-]*)")


def prune(css, words):
    out = []
    for prelude, body in _blocks(css):
        if body is None:
            out.append(prelude + ";")
        elif prelude.startswith("@media") or prelude.startswith("@supports"):
            inner = prune(body, words)
            if inner:
                out.append(prelude + "{" + inner + "}")
        elif prelude.startswith("@"):
            out.append(prelude + "{" + body + "}")
        else:
            sels = [s for s in _split(prelude, ",") if all(t in words or t.startswith(EXTERNAL) for t in _TOK.findall(re.sub(r"\[[^\]]*\]", "", s)))]
            if sels:
                out.append(",".join(sels) + "{" + body + "}")
    return "".join(out)


def site_words():
    words = set()
    files = [p for p in ROOT.rglob("*.html") if "build" not in p.relative_to(ROOT).parts] + list(ROOT.glob("*.js"))
    for p in files:
        try:
            words.update(re.findall(r"[A-Za-z0-9_-]+", p.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):
            pass
    return words


def build():
    """Write site.min.css from the sources and the current pages; return its version code."""
    src = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in PARTS)
    full = minify(src)
    out = prune(full, site_words())
    assert out.count("{") == out.count("}"), "the trimmed css has unbalanced braces"
    (ROOT / "site.min.css").write_text(out, encoding="utf-8", newline="\n")
    return hashlib.sha1(out.encode("utf-8")).hexdigest()[:8]


def apply(version):
    """Put the version code into every page's stylesheet link (only files that change are written)."""
    n = 0
    for p in ROOT.rglob("*.html"):
        if "build" in p.relative_to(ROOT).parts:
            continue
        with open(p, encoding="utf-8", newline="") as f:
            t = f.read()
        new = LINK.sub("/site.min.css?v=" + version, t)
        if new != t:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            n += 1
    return n


if __name__ == "__main__":
    v = build()
    print(v, (ROOT / "site.min.css").stat().st_size // 1024, "KB; pages updated:", apply(v))
