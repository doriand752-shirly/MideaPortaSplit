import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var monitor: StockMonitor
    @State private var settings = SettingsStore.shared.load()

    var body: some View {
        NavigationStack {
            List {
                statusSection
                actionableSection
                localStoresSection
                onlineSection
            }
            .navigationTitle("PortaSplit")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task {
                            await monitor.runCheck(settings: settings, source: .manual)
                        }
                    } label: {
                        if monitor.isChecking {
                            ProgressView()
                        } else {
                            Image(systemName: "arrow.clockwise")
                        }
                    }
                    .disabled(monitor.isChecking)
                }

                ToolbarItem(placement: .topBarLeading) {
                    Button(monitor.monitoringActive ? "Pause" : "Démarrer") {
                        if monitor.monitoringActive {
                            monitor.stop()
                        } else {
                            monitor.start(settings: settings)
                        }
                    }
                    .fontWeight(.semibold)
                }
            }
            .refreshable {
                await monitor.runCheck(settings: settings, source: .manual)
            }
            .onAppear {
                settings = SettingsStore.shared.load()
                if !monitor.monitoringActive {
                    monitor.start(settings: settings)
                }
            }
        }
    }

    private var statusSection: some View {
        Section("Surveillance") {
            LabeledContent("État") {
                Text(monitor.monitoringActive ? "Active" : "En pause")
                    .foregroundStyle(monitor.monitoringActive ? .green : .secondary)
            }
            LabeledContent("Zone", value: "\(settings.postalCode) · \(Int(settings.radiusKm)) km")
            LabeledContent("Intervalle", value: "\(settings.intervalMinutes) min (app ouverte)")
            if let snapshot = monitor.snapshot {
                LabeledContent("Dernière vérif") {
                    Text(snapshot.checkedAt, style: .relative)
                }
            }
            if let error = monitor.lastError {
                Text(error)
                    .font(.footnote)
                    .foregroundStyle(.red)
            }
            Text("iOS limite l’arrière-plan : gardez l’app ouverte ou utilisez Telegram + le moniteur PC pour une surveillance 24/7.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }

    @ViewBuilder
    private var actionableSection: some View {
        Section("Actionnable") {
            if let offers = monitor.snapshot?.actionable, !offers.isEmpty {
                ForEach(offers) { offer in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(offer.title)
                                .fontWeight(.semibold)
                            Spacer()
                            Text(offer.kind == .magasin ? "Magasin" : "Livraison")
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(offer.kind == .magasin ? Color.green.opacity(0.15) : Color.blue.opacity(0.15))
                                .clipShape(Capsule())
                        }
                        Text(offer.detail)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        if let price = offer.price {
                            Text("\(Int(price)) €")
                                .font(.subheadline)
                        }
                        if let url = URL(string: offer.url) {
                            Link("Ouvrir", destination: url)
                                .font(.subheadline)
                        }
                    }
                    .padding(.vertical, 4)
                }
            } else {
                Text("Rien d’actionnable pour l’instant")
                    .foregroundStyle(.secondary)
            }
        }
    }

    @ViewBuilder
    private var localStoresSection: some View {
        if let stores = monitor.snapshot?.localStores, !stores.isEmpty {
            Section("Magasins proches") {
                ForEach(stores) { store in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(store.storeName)
                            Text("\(store.location) · \(store.distanceKm, specifier: "%.1f") km")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Image(systemName: store.inStock ? "checkmark.circle.fill" : "xmark.circle")
                            .foregroundStyle(store.inStock ? .green : .secondary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var onlineSection: some View {
        if let online = monitor.snapshot?.onlineOffers, !online.isEmpty {
            Section("En ligne") {
                ForEach(online) { item in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(item.retailerName)
                            if let price = item.price {
                                Text("\(Int(price)) €")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        if item.deliveryEligible {
                            Text("Livraison OK")
                                .font(.caption2)
                                .foregroundStyle(.blue)
                        }
                        Image(systemName: item.inStock ? "checkmark.circle.fill" : "xmark.circle")
                            .foregroundStyle(item.inStock ? .green : .secondary)
                    }
                }
            }
        }
    }
}

#Preview {
    DashboardView()
        .environmentObject(StockMonitor.shared)
}
