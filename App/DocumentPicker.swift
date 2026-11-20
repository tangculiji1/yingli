#if os(iOS)
import UIKit
import UniformTypeIdentifiers

/// The system file browser, presented by UIKit instead of SwiftUI's `.fileImporter`.
///
/// On a real iPhone `.fileImporter` can do nothing at all: the tap flips the state, yet no browser
/// appears and the result closure never runs. It happens most reliably when the modifier lives on
/// a view inside a sheet — which is exactly where Add Subscription keeps it — while the simulator
/// and the iPad are fine. `UIDocumentPickerViewController` presented from the top view controller
/// works there, so Add from File goes through this, with `.fileImporter` kept as the fallback for
/// the rare case where there is no view controller to present from.
@MainActor
enum DocumentPicker {
    /// UIKit keeps its delegate weak, so this holds it — and the closure it calls — while the
    /// browser is up.
    private static var running: Delegate?

    /// Shows the browser over whatever is on screen. False when it could not be shown, so the
    /// caller can fall back to `.fileImporter`.
    @discardableResult
    static func present(_ types: [UTType], onPick: @escaping @MainActor (URL) -> Void) -> Bool {
        running = nil
        let scene = UIApplication.shared.appWindowScene
        var host = (scene?.keyWindow ?? scene?.windows.first)?.rootViewController
        while let next = host?.presentedViewController { host = next }
        guard let host, host.viewIfLoaded?.window != nil else { return false }
        // A copy, so the file is readable without a security scope and an iCloud file that is only
        // a placeholder here is downloaded first (asCopy does that for us).
        let browser = UIDocumentPickerViewController(forOpeningContentTypes: types, asCopy: true)
        browser.allowsMultipleSelection = false
        let delegate = Delegate(onPick: onPick)
        browser.delegate = delegate
        running = delegate
        host.present(browser, animated: true)
        return true
    }

    @MainActor
    private final class Delegate: NSObject, @preconcurrency UIDocumentPickerDelegate {
        private let pick: @MainActor (URL) -> Void

        init(onPick: @escaping @MainActor (URL) -> Void) {
            pick = onPick
            super.init()
        }

        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            guard let url = urls.first else { return }
            pick(url)
        }

        func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) {}
    }
}
#endif
