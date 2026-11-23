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

# The 映匣 account card and the run of feedback tiles that follows it on iPhone, iPad and Mac.
ACCOUNT_CARD = re.compile(
    r"            // Who is signed in: their feedback points, and Pro\.\n"
    r".*?\n            #endif\n\n",
    re.S,
)

# The same two sections on Apple TV.
ACCOUNT_CARD_TV = '''            if !updates.available.isEmpty { updateSection }
            TVSettingsSection { AccountSettingsRow() }
            // First in the list, beside the app: a problem or an idea is one press away.
            TVSettingsSection {
                TVSettingsLink(title: L10n.text("Send Feedback")) { FeedbackView() }
                TVSettingsLink(title: L10n.text("Telegram Group")) { TelegramGroupView() }
            }
'''

UPDATE_CHANNEL = (
    "    static var channel: Channel { Distribution.isTestFlight ? .testFlight"
    " : Distribution.isAppStore ? .none : .direct }"
)

ACCOUNTS_SECTION = '''            Section(L10n.text("Accounts")) {
                if store.extrasUnlocked {
                    FormLink(symbol: "play.tv.fill", tint: .pink, title: L10n.text("Bilibili"), value: bilibiliSummary) { BilibiliAccountView() }
                    FormLink(symbol: "music.note", tint: .black, title: L10n.text("Douyin"), value: douyinSummary) { DouyinAccountView() }
                    ForEach(sourceSignIns, id: \\.signIn.id) { entry in
                        FormLink(symbol: "play.rectangle.on.rectangle.fill", tint: .red, title: entry.signIn.name, value: entry.summary) { SourceAccountView(signIn: entry.signIn) }
                    }
                }
                FormLink(symbol: "externaldrive.fill.badge.person.crop", tint: .brown, title: L10n.text("Cloud Drive Accounts"), value: cloudSummary) { CloudDriveView() }
            }

'''

PROFILES_SECTION = '''            Section {
                FormLink(symbol: "person.2.fill", tint: .teal, title: L10n.text("Profiles"), value: store.profile.title) { ProfilesView() }
            }
            .id("settings.profiles")

'''

ICLOUD_SECTION = '''            // Only the main profile's library syncs (#1456).
            if store.profile.isMain {
                Section {
                    Toggle(isOn: $syncsWithICloud) {
                        FormLabel(symbol: "icloud.fill", tint: .blue, title: L10n.text("iCloud Sync"))
                    }
                    .settingsSwitch()
                    .onChange(of: syncsWithICloud) { _, on in store.cloudSync?.setEnabled(on) }
                } footer: {
                    Text(SettingsNote.iCloud)
                }
            }

'''

TOP_SECTION = '''            Section {
                settingsTopTiles
            } footer: {
                if store.profile.isMain { Text(SettingsNote.iCloud) }
            }
            .id("settings.profiles")

'''

TOP_TILES = '''    /// Profiles and iCloud Sync as the two cards under the app's name.
    private var settingsTopTiles: some View {
        HStack(spacing: 12) {
            NavigationLink { ProfilesView() } label: {
                SettingsTopTile(symbol: "person.2.fill", tint: .teal, title: L10n.text("Profiles"),
                                status: store.profile.title, active: true)
            }
            .buttonStyle(PressableStyle())
            Button {
                syncsWithICloud.toggle()
                store.cloudSync?.setEnabled(syncsWithICloud)
            } label: {
                SettingsTopTile(symbol: "icloud.fill", tint: .blue, title: L10n.text("iCloud Sync"),
                                status: L10n.text(syncsWithICloud ? "In sync" : "Off"), active: syncsWithICloud)
            }
            .buttonStyle(PressableStyle())
        }
        .listRowInsets(EdgeInsets())
        .listRowBackground(Color.clear)
        .accessibilityIdentifier("settings.topTiles")
    }

'''

TOP_TILE_VIEW = '''

/// The card under the app's name: a symbol, its name and a status line of its own.
private struct SettingsTopTile: View {
    let symbol: String
    let tint: Color
    let title: String
    let status: String
    let active: Bool
    var body: some View {
        let shape = RoundedRectangle(cornerRadius: 24, style: .continuous)
        VStack(alignment: .leading, spacing: 14) {
            Image(systemName: symbol)
                .font(.system(size: 29, weight: .semibold))
                .foregroundStyle(tint)
            Text(title).font(.title3.weight(.semibold)).foregroundStyle(.primary).lineLimit(1)
            HStack(spacing: 7) {
                Circle().fill(active ? Color.green : Color.gray.opacity(0.45)).frame(width: 9, height: 9)
                Text(status).font(.footnote.weight(.medium)).foregroundStyle(.secondary).lineLimit(1)
            }
        }
        .padding(18)
        .frame(maxWidth: .infinity, minHeight: 128, alignment: .leading)
        .background(SettingsStyle.rowFill, in: shape)
        .contentShape(shape)
    }
}
'''

LIVE_FEED = 'URL(string: "https://yingxia.getmegaportal.com/releases.json")!'
DEAD_FEED = 'URL(string: "http://127.0.0.1:9/releases.json")!'


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


def hide_upstream_accounts() -> list:
    """Take out the 映匣 account card, the Send Feedback tile and the Telegram group link."""
    path = ROOT / "App/SettingsView.swift"
    text = path.read_text(encoding="utf-8")
    before = text
    text, phones = ACCOUNT_CARD.subn("", text, count=1)
    tvs = text.count(ACCOUNT_CARD_TV)
    text = text.replace(ACCOUNT_CARD_TV, "")
    if text != before:
        path.write_text(text, encoding="utf-8")
    return [phones, tvs]


def turn_off_updates() -> list:
    """No news from the upstream release feed: no fetch, no Software Update row, no What's New."""
    channel = False
    path = ROOT / "App/Updates.swift"
    text = path.read_text(encoding="utf-8")
    if UPDATE_CHANNEL in text:
        path.write_text(text.replace(UPDATE_CHANNEL,
                                     "    static var channel: Channel { .none }"), encoding="utf-8")
        channel = True
    feed = False
    path = ROOT / "Sources/TVCore/ReleaseFeed.swift"
    text = path.read_text(encoding="utf-8")
    if LIVE_FEED in text:
        path.write_text(text.replace(LIVE_FEED, DEAD_FEED), encoding="utf-8")
        feed = True
    return [channel, feed]


def arrange_settings_top() -> bool:
    """Profiles and iCloud Sync as two cards under the app's name, with the accounts right below."""
    path = ROOT / "App/SettingsView.swift"
    text = path.read_text(encoding="utf-8")
    if "settingsTopTiles" in text:
        return False
    for piece, name in ((ACCOUNTS_SECTION, "the accounts"), (PROFILES_SECTION, "Profiles"),
                        (ICLOUD_SECTION, "iCloud Sync")):
        if piece not in text:
            raise SystemExit(f"App/SettingsView.swift: could not find {name}")
        text = text.replace(piece, "", 1)
    text = text.replace("            heroSection\n",
                        "            heroSection\n\n" + TOP_SECTION + ACCOUNTS_SECTION, 1)
    text = text.replace("    private var version: String? {\n",
                        TOP_TILES + "    private var version: String? {\n", 1)
    text = text + TOP_TILE_VIEW
    path.write_text(text, encoding="utf-8")
    return True


if __name__ == "__main__":
    print(f"renamed {rename_interface_strings()} strings")
    print("widened the file importer" if accept_any_file() else "file importer already widened")
    picked = pick_files_through_uikit()
    print("Add from File now uses DocumentPicker" if picked else "Add from File already uses DocumentPicker")
    phones, tvs = hide_upstream_accounts()
    print(f"removed {phones} account/feedback block(s) and {tvs} on Apple TV")
    channel, feed = turn_off_updates()
    print(f"update checks off (channel {channel}, feed {feed})")
    print("Profiles and iCloud Sync now sit as cards under the name"
          if arrange_settings_top() else "top of Settings already arranged")
