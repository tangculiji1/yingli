#!/usr/bin/env python3
"""Rename this build: display name, bundle identifiers, copyright line.

Usage:
    python3 Scripts/rebrand.py "影巢" "YingChao" "com.yingchao.player"

Idempotent: running it twice with the same arguments changes nothing.
The bundle identifier is the iOS one; macOS and tvOS get ".macos" and ".tv" appended.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def replace(path: Path, pattern: str, replacement: str, required: bool = True) -> int:
    text = path.read_text(encoding="utf-8")
    new, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count and new != text:
        path.write_text(new, encoding="utf-8")
    if required and count == 0:
        print(f"warning: no match in {path.relative_to(ROOT)}: {pattern}")
    return count


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    name = sys.argv[1]
    english = sys.argv[2] if len(sys.argv) > 2 else name
    bundle = sys.argv[3] if len(sys.argv) > 3 else "com.yingchao.player"

    project = ROOT / "project.yml"
    replace(project, r"^(\s*INFOPLIST_KEY_CFBundleDisplayName: ).*$", rf"\g<1>{name}")
    replace(project, r"^(\s*CFBundleDisplayName: ).*$", rf"\g<1>{name}")
    # Any previous bundle identifier: com.<something>.<...> on the three PRODUCT_BUNDLE_IDENTIFIER lines.
    text = project.read_text(encoding="utf-8")
    text = re.sub(r"^(\s*PRODUCT_BUNDLE_IDENTIFIER: ).*\.macos\s*$", rf"\g<1>{bundle}.macos", text, flags=re.MULTILINE)
    text = re.sub(r"^(\s*PRODUCT_BUNDLE_IDENTIFIER: ).*\.tv\s*$", rf"\g<1>{bundle}.tv", text, flags=re.MULTILINE)
    text = re.sub(r"^(\s*PRODUCT_BUNDLE_IDENTIFIER: )(?!.*\.(macos|tv)\s*$).*$", rf"\g<1>{bundle}", text, flags=re.MULTILINE)
    project.write_text(text, encoding="utf-8")

    for plist in sorted((ROOT / "Config").glob("Info-TVBox-*.plist")):
        text = plist.read_text(encoding="utf-8")
        text = re.sub(r"(<key>CFBundleDisplayName</key>\s*<string>).*?(</string>)", rf"\g<1>{name}\g<2>", text)
        plist.write_text(text, encoding="utf-8")

    replace(
        ROOT / "App/GlassKit.swift",
        r'static let copyright = ".*"',
        f'static let copyright = "© 2026 {name} · 基于 Yingxia（GPL-3.0）"',
    )

    print(f"name: {name} ({english})")
    print(f"bundle: {bundle} (iOS), {bundle}.macos (macOS), {bundle}.tv (tvOS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
