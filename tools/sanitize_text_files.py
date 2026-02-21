#!/usr/bin/env python3
"""Normalize text files to UTF-8 + LF and strip bidi override chars."""

from __future__ import annotations

from pathlib import Path

TEXT_EXTS = {".py", ".md", ".txt"}
BIDI_CHARS = {
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u2066", "\u2067", "\u2068", "\u2069",
}


def sanitize_text(content: str) -> str:
    content = content.replace("\u2028", "\n").replace("\u2029", "\n")
    for ch in BIDI_CHARS:
        content = content.replace(ch, "")
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    return content


def iter_targets(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTS and ".git" not in p.parts]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    changed = 0
    for path in iter_targets(root):
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        sanitized = sanitize_text(text)
        out = sanitized.encode("utf-8")
        if out != raw:
            path.write_bytes(out)
            changed += 1
            print(f"sanitized: {path.relative_to(root)}")
    print(f"done: {changed} files normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
