#!/usr/bin/env python3
"""Show this build's own name in the interface.

The upstream strings call the app Yingxia / 映匣 in 244 places. Only the right-hand
side of a .strings entry is rewritten: the left-hand side is the lookup key the Swift
code passes to L10n.text(), so changing it would make the lookup miss.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD = {"映匣": "影栗", "Yingxia": "Yingli"}


def main() -> int:
    changed = 0
    for path in sorted(ROOT.glob("App/Resources/*.lproj/InfoPlist.strings")) + sorted(
        ROOT.glob("Sources/TVCore/Resources/*.lproj/Localizable.strings")
    ):
        out, count = [], 0
        for line in path.read_text(encoding="utf-8").splitlines(True):
            match = re.match(r'^(\s*".*?"\s*=\s*")(.*)("\s*;\s*)$', line)
            if match:
                value = match.group(2)
                for old, new in OLD.items():
                    value = value.replace(old, new)
                if value != match.group(2):
                    count += 1
                    line = match.group(1) + value + match.group(3)
            out.append(line)
        if count:
            path.write_text("".join(out), encoding="utf-8")
            changed += count
            print(f"{path.relative_to(ROOT)}: {count}")
    print(f"renamed {changed} strings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
