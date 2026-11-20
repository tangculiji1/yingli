#!/usr/bin/env python3
"""Small source adjustments applied to a clean checkout right before the Xcode build.

They live here instead of in the sources themselves because this repository is edited
through the GitHub API from a phone, which refuses files above roughly 150 KB.
Each one is idempotent, so running this twice changes nothing.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENAMES = {"映匣": "影栗", "Yingxia": "Yingli"}


def rename_interface_strings() -> int:
    """Only the right-hand side of a .strings entry: the left side is the lookup key."""
    changed = 0
    for path in sorted(ROOT.glob("App/Resources/*.lproj/InfoPlist.strings")) + sorted(
        ROOT.glob("Sources/TVCore/Resources/*.lproj/Localizable.strings")
    ):
        out, count = [], 0
        for line in path.read_text(encoding="utf-8").splitlines(True):
            match = re.match(r'^(\s*".*?"\s*=\s*")(.*)("\s*;\s*)$', line)
            if match:
                value = match.group(2)
                for old, new in RENAMES.items():
                    value = value.replace(old, new)
                if value != match.group(2):
                    count += 1
                    line = match.group(1) + value + match.group(3)
            out.append(line)
        if count:
            path.write_text("".join(out), encoding="utf-8")
            changed += count
    return changed


def accept_any_file() -> bool:
    """Add from File dimmed files whose type iOS did not recognise; accept any data file."""
    path = ROOT / "App/SettingsView.swift"
    text = path.read_text(encoding="utf-8")
    old = "static let types: [UTType] = [.json, .pythonScript, .javaScript, .m3uPlaylist, .plainText]"
    new = "static let types: [UTType] = [.json, .pythonScript, .javaScript, .m3uPlaylist, .plainText, .data]"
    if old not in text:
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    return True


if __name__ == "__main__":
    print(f"renamed {rename_interface_strings()} strings")
    print("widened the file importer" if accept_any_file() else "file importer already widened")
