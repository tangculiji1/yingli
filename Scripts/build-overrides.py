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

# Add from File opens the browser from UIKit: SwiftUI's `.fileImporter` does nothing at all on some
# iPhones, and it is on a view inside the Add Subscription sheet there. The picked file goes through
# the same `importSubscriptionFile`, and `.fileImporter` stays in place as the fallback.
SETTINGS_METHODS = '''    /// The browser from UIKit (see `DocumentPicker`), with `.fileImporter` as the fallback.
    private func addFromFile() {
        focused = false
        if !DocumentPicker.present(SubscriptionFile.types, onPick: importFile) { choosesFile = true }
    }

    private func importFile(_ file: URL) {
        Task {
            await store.importSubscriptionFile(file)
            if store.importError == nil { dismiss() }
        }
    }

'''

LIVE_METHODS = '''    /// The browser from UIKit (see `DocumentPicker`), with `.fileImporter` as the fallback.
    private func addFromFile() {
        #if os(iOS)
        if DocumentPicker.present(SubscriptionFile.types, onPick: { file in
            Task { await store.importSubscriptionFile(file) }
        }) { return }
        #endif
        #if !os(tvOS)
        choosesFile = true
        #endif
    }

'''


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


def pick_files_through_uikit() -> int:
    """Point Add from File at `DocumentPicker`, in the subscription sheet and the live editor."""
    changed = 0
    for name, opening, methods in (
        ("App/SettingsView.swift", "    private func add() {\n        guard canAdd else { return }", SETTINGS_METHODS),
        ("App/LiveView.swift", "    private func add() {\n        Task { await store.importSubscription() }", LIVE_METHODS),
    ):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        if "private func addFromFile()" in text:
            continue
        before = text
        text = text.replace("Button { choosesFile = true } label: {", "Button(action: addFromFile) {", 1)
        if opening not in text:
            raise SystemExit(f"{name}: could not find the add() that follows the button")
        text = text.replace(opening, methods + opening, 1)
        if text != before:
            path.write_text(text, encoding="utf-8")
            changed += 1
    if changed:
        return changed
    return 0


if __name__ == "__main__":
    print(f"renamed {rename_interface_strings()} strings")
    print("widened the file importer" if accept_any_file() else "file importer already widened")
    picked = pick_files_through_uikit()
    print("Add from File now uses DocumentPicker" if picked else "Add from File already uses DocumentPicker")
