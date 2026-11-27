import SwiftUI
import UIKit

// Small pieces shared by the app and the widgets.

struct T: View {
    @Environment(\.look) var look
    var text: String
    var size: CGFloat = 15
    var weight: Font.Weight = .regular
    var color: Color?
    init(_ text: String, _ size: CGFloat = 15, _ weight: Font.Weight = .regular, color: Color? = nil) {
        self.text = text; self.size = size; self.weight = weight; self.color = color
    }
    var body: some View { Text(text).font(look.font(size, weight)).foregroundStyle(color ?? look.text) }
}

struct CardBox<Content: View>: View {
    @Environment(\.look) var look
    @ViewBuilder var content: Content
    var body: some View {
        content.frame(maxWidth: .infinity, alignment: .leading).padding(16)
            .background(look.card, in: RoundedRectangle(cornerRadius: look.corner))
    }
}

extension Color {
    var isDark: Bool {
        let c = UIColor(self)
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        c.getRed(&r, green: &g, blue: &b, alpha: &a)
        return 0.299 * r + 0.587 * g + 0.114 * b < 0.5
    }
}
