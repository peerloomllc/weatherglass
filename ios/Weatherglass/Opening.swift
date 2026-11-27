import ImageIO
import SwiftUI
import UIKit

// The big weather icon, animated once when the app opens, in the skin's own
// way, as on Android (ui/Opening.kt). Skins with clips play the Android
// app's own animated WebP files (res/raw/clip_<skin>_<weather>_<day|night>),
// copied into the app as "raw". Minimal Mono draws its symbol on. The first
// frame holds for a moment, so the movement is not over before the app is
// on screen.

private let startDelay = 0.45

struct OpeningIcon: View {
    @Environment(\.look) var look
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    var code: Int
    var isDay: Bool
    var size: CGFloat
    /// Changes each time the app opens; the animation plays once per value.
    var playKey: Int
    var enabled: Bool
    @State private var playedKey: Int?
    @State private var frame: Int?
    @State private var drawn = false

    var body: some View {
        let clip = enabled && !reduceMotion ? Clip.load(look.skin.id, code: code, isDay: isDay) : nil
        ZStack {
            // Until the clip has played for this open, hold its first frame
            // rather than flash the finished picture.
            if let clip, let f = frame ?? (playedKey != playKey ? 0 : nil) {
                Image(uiImage: clip.frames[f]).resizable().interpolation(.high).scaledToFit().frame(width: size, height: size)
            } else if clip == nil, Skins.art(look.skin, code: code, isDay: isDay) == nil, #available(iOS 26.0, *) {
                Image(systemName: Skins.symbol(code: code, isDay: isDay)).resizable().scaledToFit()
                    .foregroundStyle(look.icon).frame(width: size * 0.86, height: size * 0.86).frame(width: size, height: size)
                    .symbolEffect(.drawOn, isActive: enabled && !reduceMotion && !drawn)
            } else {
                WeatherIcon(code: code, isDay: isDay, size: size)
            }
        }
        .task(id: "\(playKey)-\(look.skin.id)") {
            guard enabled, !reduceMotion, playedKey != playKey else { drawn = true; return }
            playedKey = playKey
            if let clip {
                frame = 0
                try? await Task.sleep(nanoseconds: UInt64(startDelay * 1e9))
                if Task.isCancelled { return }
                for i in clip.frames.indices {
                    if Task.isCancelled { return }
                    frame = i
                    try? await Task.sleep(nanoseconds: UInt64(clip.delay * 1e9))
                }
                frame = nil
            } else if Skins.art(look.skin, code: code, isDay: isDay) == nil {
                try? await Task.sleep(nanoseconds: UInt64(startDelay * 1e9))
                drawn = true
            }
        }
    }
}

/// An animated WebP clip, decoded into frames.
struct Clip {
    var frames: [UIImage]
    var delay: Double

    private static let dir = Bundle.main.resourceURL?.appendingPathComponent("raw")
    private static var cache: [String: Clip] = [:]

    static func load(_ skin: String, code: Int, isDay: Bool) -> Clip? {
        let base = "clip_\(skin)_\(condition(code).rawValue)"
        for name in (isDay ? [] : ["\(base)_night"]) + ["\(base)_day"] {
            if let c = cache[name] { return c }
            guard let url = dir?.appendingPathComponent(name + ".webp"),
                  let src = CGImageSourceCreateWithURL(url as CFURL, nil) else { continue }
            let n = CGImageSourceGetCount(src)
            guard n > 1 else { continue }
            var frames: [UIImage] = []
            for i in 0..<n { if let img = CGImageSourceCreateImageAtIndex(src, i, nil) { frames.append(UIImage(cgImage: img)) } }
            var delay = 0.08
            if let props = CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [CFString: Any],
               let webp = props[kCGImagePropertyWebPDictionary] as? [CFString: Any],
               let d = (webp[kCGImagePropertyWebPUnclampedDelayTime] ?? webp[kCGImagePropertyWebPDelayTime]) as? Double, d > 0 {
                delay = d
            }
            let c = Clip(frames: frames, delay: delay)
            cache[name] = c
            return c
        }
        return nil
    }
}
