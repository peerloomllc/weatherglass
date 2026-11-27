import SwiftUI

struct PlacesSheet: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.look) var look
    @Environment(\.dismiss) var dismiss
    @State private var query = ""

    var body: some View {
        NavigationStack {
            List {
                if query.isEmpty {
                    Section {
                        ForEach(Array(model.places.enumerated()), id: \.element.id) { i, p in
                            Button { model.select(i); dismiss() } label: {
                                HStack {
                                    if p.isCurrent { Image(systemName: "location.fill") }
                                    VStack(alignment: .leading) {
                                        T(p.name, 16, i == model.selected ? .semibold : .regular)
                                        if !p.region.isEmpty { T(p.region, 13, color: look.subtle) }
                                    }
                                }
                            }
                        }
                        .onDelete { $0.forEach { model.remove($0) } }
                    }
                    .listRowBackground(look.card)
                    if !model.places.contains(where: { $0.isCurrent }) {
                        Button { model.addCurrentLocation(); dismiss() } label: { Label("Use my location", systemImage: "location") }
                            .listRowBackground(look.card)
                    }
                } else {
                    ForEach(model.results, id: \.id) { p in
                        Button { model.add(p); query = ""; dismiss() } label: {
                            VStack(alignment: .leading) {
                                T(p.name, 16)
                                T(p.region, 13, color: look.subtle)
                            }
                        }
                    }
                    .listRowBackground(look.card)
                }
            }
            .scrollContentBackground(.hidden)
            .background(look.bgTop)
            .searchable(text: $query, prompt: "Search for a city")
            .onChange(of: query) { _, q in model.search(q) }
            .navigationTitle(look.label("Places"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
    }
}

struct SettingsSheet: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.look) var look
    @Environment(\.dismiss) var dismiss
    @Environment(\.colorScheme) var scheme
    @State private var openGroup: String?

    var body: some View {
        let s = model.settings
        NavigationStack {
            List {
                Section(look.label("Skin")) {
                    ForEach(Skins.groups, id: \.0) { name, skins in
                        DisclosureGroup(isExpanded: Binding(get: { openGroup == name }, set: { openGroup = $0 ? name : nil })) {
                            LazyVGrid(columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible())], spacing: 12) {
                                ForEach(skins) { skin in SkinCard(skin: skin, picked: skin.id == s.skin, dark: scheme == .dark) {
                                    var n = s; n.skin = skin.id; model.update(n)
                                } }
                            }
                            .padding(.vertical, 6)
                        } label: {
                            HStack { T(look.label(name), 15); Spacer(); T("\(skins.count)", 13, color: look.subtle) }
                        }
                    }
                }
                .listRowBackground(look.card)
                Section(look.label("Units")) {
                    Picker("Temperature", selection: Binding(get: { s.tempUnit }, set: { var n = s; n.tempUnit = $0; model.update(n) })) {
                        Text("°F").tag(TempUnit.F); Text("°C").tag(TempUnit.C)
                    }
                    Picker("Wind", selection: Binding(get: { s.windUnit }, set: { var n = s; n.windUnit = $0; model.update(n) })) {
                        ForEach(WindUnit.allCases, id: \.self) { Text($0.label).tag($0) }
                    }
                    Picker("Clock", selection: Binding(get: { s.use24h }, set: { var n = s; n.use24h = $0; model.update(n) })) {
                        Text("12 hour").tag(false); Text("24 hour").tag(true)
                    }
                }
                .listRowBackground(look.card)
                Section {
                    Toggle("Severe weather (US)", isOn: Binding(get: { s.alerts }, set: { var n = s; n.alerts = $0; model.update(n) }))
                } header: { Text(look.label("Alerts")) } footer: {
                    Text("Official warnings from the US National Weather Service, shown at the top of the screen.")
                }
                .listRowBackground(look.card)
                Section {
                    T("Weather data by Open-Meteo.com (CC BY 4.0). Alerts from the US National Weather Service.", 12, color: look.subtle)
                }
                .listRowBackground(Color.clear)
            }
            .scrollContentBackground(.hidden)
            .background(look.bgTop)
            .font(look.font(16))
            .foregroundStyle(look.text)
            .navigationTitle(look.label("Settings"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .onAppear { openGroup = Skins.groups.first { $0.1.contains { $0.id == s.skin } }?.0 }
        }
    }
}

private struct SkinCard: View {
    var skin: Skin
    var picked: Bool
    var dark: Bool
    var onPick: () -> Void
    var body: some View {
        let p = skin.palette(dark: dark)
        let look = Look(skin: skin, p: p)
        Button(action: onPick) {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    WeatherIcon(code: 2, isDay: true, size: 32)
                    Text("72°").font(look.font(24, .light)).foregroundStyle(look.text)
                }
                Text(look.label(skin.name)).font(look.font(14, .medium)).foregroundStyle(look.text).lineLimit(1)
            }
            .frame(maxWidth: .infinity, alignment: .leading).padding(12)
            .background(look.bgTop, in: RoundedRectangle(cornerRadius: 14))
            .overlay(RoundedRectangle(cornerRadius: 14).stroke(picked ? look.accent : look.subtle.opacity(0.4), lineWidth: picked ? 3 : 1))
        }
        .buttonStyle(.plain)
        .environment(\.look, look)
    }
}
