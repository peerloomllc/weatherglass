import SwiftUI
import UIKit

// The About page and the one-time donation reminder, matching the Android
// app (ui/About.kt) and the other PeerLoom apps.

/// Donations are hidden on iOS for now (asked for 2026-11-26): no "Support
/// development" section and no two-week reminder. Set to true to bring both back.
let showDonations = false

private let lightningAddress = "peerloomllc@strike.me"
private let strikeTipUrl = "https://strike.me/peerloomllc/"
private let btcOnchain = "bc1q0kksenz3j4u9ppe6f4krclvzwxk7sjy00cc9cf"
private let buyMeACoffee = "https://buymeacoffee.com/peerloomllc"
private let crashCourse = "https://nakamotoinstitute.org/crash-course/"
private let email = "peerloomllc@proton.me"
private let issues = "https://github.com/peerloomllc/weatherglass/issues"
private let site = "https://peerloomllc.com/weatherglass/"

private let wallets = [
    ("Strike", "Simple Lightning payments", "https://strike.me"),
    ("Cash App", "Send Bitcoin via Lightning", "https://cash.app"),
    ("Wallet of Satoshi", "Beginner-friendly Lightning wallet", "https://walletofsatoshi.com"),
    ("Phoenix", "Self-custodial Lightning wallet", "https://phoenix.acinq.co"),
]

private let credits = [
    ("Open-Meteo", "CC BY 4.0", "Forecasts, 15-minute rain and city search"),
    ("US National Weather Service", "Public domain", "Severe weather alerts"),
    ("Natural Earth", "Public domain", "Coastlines, borders and city names on the map"),
    ("Blender", "GPL", "Used to make the skin art (not part of the app)"),
]

private func open(_ url: String) { if let u = URL(string: url) { UIApplication.shared.open(u) } }

struct AboutSheet: View {
    @Environment(\.look) var look
    @Environment(\.dismiss) var dismiss
    @State var openId: String?
    @State private var btc = false
    @State private var sharing = false

    var body: some View {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? ""
        NavigationStack {
            ScrollView {
                VStack(spacing: 10) {
                    VStack(spacing: 4) {
                        T("Weatherglass", 24, .medium)
                        T("Simple weather. No ads, no accounts, no tracking.", 14, color: look.subtle).multilineTextAlignment(.center)
                    }
                    .padding(.bottom, 6)
                    section("How it works", "how") {
                        T("Your phone asks Open-Meteo for the forecast and the US National Weather Service for alerts, directly. There is no Weatherglass server in between, no account and no tracking. Your location is only sent to them to get your forecast, and only roughly.", 14)
                    }
                    if showDonations { section("Support development", "support") {
                        T("Weatherglass is free, with no ads, accounts or subscriptions. If you get value from it, please consider returning value.", 14)
                        HStack(spacing: 10) {
                            PillButton("⚡ BTC ⚡", primary: true) { btc = true }
                            PillButton("$ USD $") { open(buyMeACoffee) }
                        }
                    } }
                    section("Learn about Bitcoin", "bitcoin") {
                        T("New to Bitcoin? The Satoshi Nakamoto Institute has a free, short crash course on how Bitcoin works and why it matters.", 14)
                        PillButton("Bitcoin crash course ↗\u{FE0E}") { open(crashCourse) }
                    }
                    section("Share the app", "share") {
                        T("Know someone who wants a simple weather app with no ads, and widgets and skins they can make their own? Tell them about Weatherglass.", 14)
                        ShareLink(item: URL(string: site)!, message: Text("Check out Weatherglass - a simple weather app with widgets and skins, no ads or accounts.")) {
                            T("Share Weatherglass", 15, .medium).frame(maxWidth: .infinity).padding(12)
                                .background(look.subtle.opacity(0.18), in: RoundedRectangle(cornerRadius: 12))
                        }
                    }
                    section("Contact", "contact") {
                        T("Questions, ideas or something not working? Write to us.", 14)
                        HStack(spacing: 10) {
                            PillButton("Email us") { open("mailto:\(email)?subject=%5BWeatherglass%5D%20Feedback") }
                            PillButton("Report a problem") { open(issues) }
                        }
                    }
                    section("Credits", "credits") {
                        T("Weatherglass is built on these, used under their licenses.", 14)
                        ForEach(credits, id: \.0) { name, licence, use in
                            VStack(alignment: .leading, spacing: 2) {
                                T("\(name)  ·  \(licence)", 14, .medium)
                                T(use, 13, color: look.subtle)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    T("© PeerLoom LLC", 12, color: look.subtle).padding(.top, 8)
                    T("v\(version)", 12, color: look.subtle)
                }
                .padding(20)
            }
            .background(look.bgTop)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .sheet(isPresented: $btc) { BtcSheet().environment(\.look, look) }
        }
    }

    @ViewBuilder
    private func section<C: View>(_ title: String, _ id: String, @ViewBuilder content: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Button { withAnimation { openId = openId == id ? nil : id } } label: {
                HStack {
                    T(look.label(title), 15, .medium)
                    Spacer()
                    T(openId == id ? "−" : "+", 20, color: look.subtle)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            if openId == id { content() }
        }
        .padding(.horizontal, 16).padding(.vertical, 14)
        .background(look.card, in: RoundedRectangle(cornerRadius: min(look.corner, 16)))
    }
}

struct PillButton: View {
    @Environment(\.look) var look
    var title: String
    var primary = false
    var action: () -> Void
    init(_ title: String, primary: Bool = false, action: @escaping () -> Void) { self.title = title; self.primary = primary; self.action = action }
    var body: some View {
        Button(action: action) {
            T(title, 15, .medium, color: primary ? look.bgTop : look.text).frame(maxWidth: .infinity).padding(12)
                .background(primary ? look.accent : look.subtle.opacity(0.18), in: RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(.plain)
    }
}

/// Ways to give in Bitcoin: open a Lightning wallet, copy the address, pay in a browser or on-chain.
struct BtcSheet: View {
    @Environment(\.look) var look
    @State private var copied: String?

    var body: some View {
        let wallet = UIApplication.shared.canOpenURL(URL(string: "lightning:\(lightningAddress)")!)
        ScrollView {
            VStack(spacing: 10) {
                T("⚡ Bitcoin Lightning ⚡", 20, .medium)
                T("Support Weatherglass with Bitcoin over Lightning (fast and low-fee) or on-chain.", 14)
                if wallet {
                    PillButton("Open in your Lightning wallet", primary: true) { open("lightning:\(lightningAddress)") }
                    T("or use another method:", 13, color: look.subtle)
                }
                copyRow("Lightning address", lightningAddress, "Paste into any Lightning, ecash or web wallet.")
                PillButton("Show a QR code or pay in a browser") { open(strikeTipUrl) }
                T("Scan it from another device.", 12, color: look.subtle)
                copyRow("On-chain Bitcoin", btcOnchain, "Fees are higher on-chain, so Lightning is cheaper for small amounts.")
                if !wallet {
                    T(look.label("No Lightning wallet yet?"), 15, .medium).frame(maxWidth: .infinity, alignment: .leading)
                    ForEach(wallets, id: \.0) { name, what, url in
                        Button { open(url) } label: {
                            VStack(alignment: .leading, spacing: 2) {
                                T("\(name) ↗\u{FE0E}", 14, .medium)
                                T(what, 13, color: look.subtle)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        .buttonStyle(.plain)
                    }
                    T("After installing, come back here and tap BTC again.", 13, color: look.subtle)
                }
            }
            .padding(20)
        }
        .background(look.bgTop)
        .presentationDetents([.large])
    }

    private func copyRow(_ label: String, _ value: String, _ hint: String) -> some View {
        Button {
            UIPasteboard.general.string = value
            copied = label
        } label: {
            VStack(alignment: .leading, spacing: 3) {
                T(look.label(label), 13, color: look.subtle)
                T(value, 14, .medium).lineLimit(1).minimumScaleFactor(0.6)
                T(copied == label ? "Copied" : "Tap to copy. \(hint)", 12, color: look.subtle)
            }
            .frame(maxWidth: .infinity, alignment: .leading).padding(12)
            .background(look.card, in: RoundedRectangle(cornerRadius: 12))
        }
        .buttonStyle(.plain)
    }
}

/// The donation reminder is due once, two weeks after first use, and never again.
enum DonationReminder {
    static func due(now: Date = Date()) -> Bool {
        guard showDonations else { return false }
        let d = Store.shared.defaults
        if d.object(forKey: "firstUseAt") == nil { d.set(now.timeIntervalSince1970, forKey: "firstUseAt") }
        let first = d.double(forKey: "firstUseAt")
        return !d.bool(forKey: "donateShown") && now.timeIntervalSince1970 - first >= 14 * 86400
    }

    static func markShown() { Store.shared.defaults.set(true, forKey: "donateShown") }
}
