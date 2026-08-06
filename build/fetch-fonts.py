#!/usr/bin/env python3
import base64
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path("/Users/ahmadelkattan/Poster-Generator")
BUILD_DIR = ROOT / "build"
FONTS_DIR = ROOT / "fonts"
CSS_OUT = BUILD_DIR / "fonts-embedded.css"
MANIFEST_OUT = BUILD_DIR / "fonts-manifest.txt"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

FAMILIES = [
    ("Cairo", "400..900", True),
    ("Reem Kufi", "400..700", True),
    ("Noto Kufi Arabic", "400..900", True),
    ("Tajawal", "400;500;700;900", False),
    ("Amiri", "400;700", False),
    ("Aref Ruqaa", "400;700", False),
]


def fetch(url: str, binary: bool = False):
    last_error = None
    for attempt in range(2):
        try:
            req = Request(url, headers={"User-Agent": UA})
            with urlopen(req, timeout=45) as response:
                body = response.read()
            return body if binary else body.decode("utf-8")
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(1)
    raise RuntimeError(str(last_error))


def css_url(family: str, weights: str) -> str:
    return (
        "https://fonts.googleapis.com/css2?family="
        + quote(family, safe="")
        + ":wght@"
        + quote(weights, safe=".;")
        + "&display=swap"
    )


def parse_blocks(css: str):
    return re.findall(r"@font-face\s*\{[^}]*\}", css, flags=re.S)


def decl(block: str, prop: str) -> str:
    m = re.search(rf"{re.escape(prop)}\s*:\s*([^;]+);", block)
    if not m:
        raise ValueError(f"missing {prop} in block: {block}")
    return " ".join(m.group(1).strip().split())


def src_url(block: str) -> str:
    m = re.search(r"url\((https://[^)]+?\.woff2)\)", block)
    if not m:
        raise ValueError(f"missing woff2 url in block: {block}")
    return m.group(1)


def subset_for(unicode_range: str):
    normalized = unicode_range.upper().replace(" ", "")
    ranges = [part.strip() for part in normalized.split(",")]
    if any(part.startswith("U+0600") or part == "U+0600" for part in ranges):
        return "arabic"
    if ranges and ranges[0].startswith("U+0000-00FF"):
        return "latin"
    return None


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")


def main() -> int:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    rules = []
    manifest = []
    failures = []

    for family, weights, is_variable in FAMILIES:
        try:
            css = fetch(css_url(family, weights))
        except Exception as exc:
            failures.append(f"{family} | {weights} | css | {exc}")
            continue

        for block in parse_blocks(css):
            try:
                font_family = decl(block, "font-family")
                font_style = decl(block, "font-style")
                font_weight = decl(block, "font-weight")
                unicode_range = decl(block, "unicode-range")
                subset = subset_for(unicode_range)
                if subset is None:
                    continue
                if is_variable and not re.fullmatch(r"\d+\s+\d+", font_weight):
                    raise ValueError(f"variable weight range not preserved: {font_weight}")

                url = src_url(block)
                name_bits = [safe_name(family)]
                if not is_variable:
                    name_bits.append(font_weight)
                name_bits.append(subset)
                font_path = FONTS_DIR / ("-".join(name_bits) + ".woff2")

                try:
                    raw = fetch(url, binary=True)
                except Exception as exc:
                    failures.append(f"{family} | {font_weight} | {subset} | {exc}")
                    continue

                if raw[:4] != b"wOF2":
                    failures.append(f"{family} | {font_weight} | {subset} | invalid magic bytes")
                    continue
                if len(raw) <= 5 * 1024:
                    failures.append(f"{family} | {font_weight} | {subset} | too small: {len(raw)} bytes")
                    continue

                font_path.write_bytes(raw)
                encoded = base64.b64encode(raw).decode("ascii")
                rule = (
                    "@font-face { "
                    f"font-family: {font_family}; "
                    f"font-style: {font_style}; "
                    f"font-weight: {font_weight}; "
                    "font-display: swap; "
                    f"src: url(data:font/woff2;base64,{encoded}) format('woff2'); "
                    f"unicode-range: {unicode_range}; "
                    "}"
                )
                rules.append(rule)
                manifest.append(
                    f"{font_family.strip(chr(39))} | {font_weight} | {subset} | {len(raw)} | {len(encoded)}"
                )
            except Exception as exc:
                failures.append(f"{family} | unknown | parse | {exc}")

    css_text = "\n".join(rules) + ("\n" if rules else "")
    CSS_OUT.write_text(css_text, encoding="utf-8")

    manifest.append(f"TOTAL CSS bytes | {len(css_text.encode('utf-8'))}")
    if failures:
        manifest.append("FAILURES")
        manifest.extend(failures)
    MANIFEST_OUT.write_text("\n".join(manifest) + "\n", encoding="utf-8")

    errors = []
    if "@import" in css_text:
        errors.append("CSS contains @import")
    if re.search(r"url\((?!data:font/woff2;base64,)", css_text):
        errors.append("CSS contains external or non-data URL")
    rule_count = css_text.count("@font-face")
    if rule_count != len(rules):
        errors.append("font-face count mismatch")
    for rule in rules:
        if "data:font/woff2;base64," not in rule:
            errors.append("rule missing data font URL")
        if "unicode-range:" not in rule:
            errors.append("rule missing unicode-range")
    for family, _, _ in FAMILIES:
        if family not in css_text:
            errors.append(f"CSS missing family: {family}")
    for family, _, is_variable in FAMILIES:
        if is_variable and not re.search(
            rf"font-family:\s*'{re.escape(family)}';[^}}]*font-weight:\s*\d+\s+\d+;",
            css_text,
        ):
            errors.append(f"CSS missing variable range syntax for {family}")
    for rule in rules:
        ur = decl(rule, "unicode-range")
        if subset_for(ur) not in {"arabic", "latin"}:
            errors.append(f"kept invalid subset: {ur}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {CSS_OUT} ({len(css_text.encode('utf-8'))} bytes)")
    print(f"Wrote {MANIFEST_OUT}")
    print(f"Rules: {rule_count}")
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"  {failure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
