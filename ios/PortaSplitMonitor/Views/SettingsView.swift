import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var monitor: StockMonitor
    @State private var settings = SettingsStore.shared.load()
    @State private var savedMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Localisation") {
                    TextField("Code postal", text: $settings.postalCode)
                        .keyboardType(.numberPad)
                    Stepper(
                        "Rayon magasins : \(Int(settings.radiusKm)) km",
                        value: $settings.radiusKm,
                        in: 10...200,
                        step: 10
                    )
                }

                Section("Vérifications") {
                    Stepper(
                        "Intervalle (app ouverte) : \(settings.intervalMinutes) min",
                        value: $settings.intervalMinutes,
                        in: 1...30
                    )
                    Toggle("Double vérification avant alerte", isOn: $settings.confirmStock)
                    Toggle("Rafraîchissement en arrière-plan", isOn: $settings.backgroundRefreshEnabled)
                }

                Section {
                    Button("Enregistrer et relancer") {
                        SettingsStore.shared.save(settings)
                        monitor.start(settings: settings)
                        savedMessage = "Réglages enregistrés"
                    }
                    .fontWeight(.semibold)

                    Button("Test notification") {
                        Task {
                            await NotificationService.shared.requestAuthorization()
                            await NotificationService.shared.notifyHeartbeat(
                                actionableCount: monitor.snapshot?.actionable.count ?? 0,
                                postalCode: settings.postalCode
                            )
                            savedMessage = "Notification de test envoyée"
                        }
                    }
                }

                if let savedMessage {
                    Section {
                        Text(savedMessage)
                            .foregroundStyle(.green)
                    }
                }

                Section("À propos") {
                    Text("Même logique que le moniteur Python : magasin < rayon OU livraison vers votre code postal. Source : ClimRadar.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Réglages")
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(StockMonitor.shared)
}
