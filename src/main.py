from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dependance optionnelle : variables d'env deja fournies (CI, shell)
    def load_dotenv(*_args, **_kwargs) -> bool:
        return False

from .availability import (
    build_actionable_offers,
    format_actionable_summary,
)
from .heartbeat import HEARTBEAT_STATE_KEY, send_daily_heartbeat
from .snapshot_state import (
    record_stock_alert,
    seed_store_from_snapshot,
    should_send_stock_alert,
    today_local,
)
from .local_stores import fetch_local_stores, local_config_from_env
from .notifiers import notify_actionable_offer, test_telegram
from .verification import confirm_actionable_offer
from .snapshot_export import build_snapshot, write_snapshot
from .state import StateStore
from .stock_checker import check_all_retailers, load_retailers

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.yaml"
DEFAULT_STATE = ROOT / "data" / "state.json"


def run_check(
    config_path: Path,
    state_path: Path,
    *,
    dry_run: bool = False,
    verbose: bool = True,
    retailer_filter: str | None = None,
    use_browser: bool = True,
    postal_code: str | None = None,
    radius_km: float | None = None,
    export_path: Path | None = None,
    notify_stores: bool = True,
) -> list:
    configured_postal, configured_radius = local_config_from_env()
    postal_code = postal_code or configured_postal
    radius_km = radius_km if radius_km is not None else configured_radius

    retailers = load_retailers(config_path)
    if retailer_filter:
        retailers = [r for r in retailers if r.id == retailer_filter]
        if not retailers:
            print(f"Revendeur inconnu ou desactive : {retailer_filter}", file=sys.stderr)
            return []

    if verbose:
        print("Verification en ligne + magasins locaux...", flush=True)
        if postal_code:
            print(f"  Zone : {postal_code} (rayon {radius_km:.0f} km)", flush=True)

    online_results = check_all_retailers(retailers, use_browser=use_browser)

    local_stores = []
    if postal_code:
        try:
            local_stores = fetch_local_stores(postal_code, radius_km=radius_km)
            if verbose and not local_stores:
                print(
                    "  Magasins : ClimRadar ne renvoie plus de donnees (rendu JavaScript). "
                    "Stock en ligne verifie via sites revendeurs.",
                    flush=True,
                )
        except Exception as exc:
            print(f"Erreur magasins locaux : {exc}", flush=True)

    actionable = build_actionable_offers(online_results, local_stores, postal_code or "?")
    store = StateStore(state_path)
    if export_path:
        seed_store_from_snapshot(store, export_path)

    today = today_local()

    for offer in actionable:
        if dry_run:
            continue

        # Magasins physiques exclus des notifications (ex: GitHub Actions),
        # mais conserves dans l'etat/snapshot pour l'app mobile.
        if not notify_stores and offer.kind == "magasin":
            store.update_local_store(offer.state_key, True, offer.detail, offer.url)
            continue

        if not should_send_stock_alert(store, offer.state_key, today, kind=offer.kind):
            store.update_local_store(offer.state_key, True, offer.detail, offer.url)
            continue

        if postal_code and not confirm_actionable_offer(
            offer,
            postal_code=postal_code,
            radius_km=radius_km,
            retailers=retailers,
            use_browser=use_browser,
        ):
            print(
                f"[WARN] {offer.retailer_name} : stock non confirme, "
                f"nouvel essai au prochain cycle",
                flush=True,
            )
            continue

        channels = notify_actionable_offer(offer, postal_code or "?")
        if not channels:
            print(
                f"[ERREUR] Notification echouee pour {offer.retailer_name} "
                f"— nouvel essai au prochain cycle",
                flush=True,
            )
            continue

        store.update_local_store(offer.state_key, True, offer.detail, offer.url)
        record_stock_alert(store, offer.state_key, today, kind=offer.kind)
        label = "MAGASIN" if offer.kind == "magasin" else "LIVRAISON"
        print(
            f"[ALERTE {label}] {offer.retailer_name} ({', '.join(channels)})",
            flush=True,
        )

    if not dry_run:
        store.mark_missing_offers({o.state_key for o in actionable})
        store.save()

        hb_channels = send_daily_heartbeat(
            store,
            postal_code=postal_code,
            actionable_count=len(actionable),
        )
        if hb_channels and verbose:
            print(f"[HEARTBEAT] Rapport quotidien envoye ({', '.join(hb_channels)})", flush=True)

    if verbose:
        print()
        if postal_code:
            print(
                format_actionable_summary(
                    actionable,
                    online_results,
                    local_stores,
                    postal_code,
                    radius_km,
                )
            )
        else:
            from .notifiers import format_summary
            print(format_summary(online_results))
            print()
            print("Definissez POSTAL_CODE dans .env pour magasins + livraison ciblee.")

    if export_path and postal_code:
        payload = build_snapshot(
            online_results=online_results,
            local_stores=local_stores,
            actionable=actionable,
            postal_code=postal_code,
            radius_km=radius_km or 100.0,
            last_heartbeat_date=store.get_meta(HEARTBEAT_STATE_KEY),
            alert_dates=store.export_alert_dates(),
            stock_state=store.export_stock_state(),
        )
        write_snapshot(export_path, payload)
        if verbose:
            print(f"Snapshot exporte : {export_path}", flush=True)

    return online_results


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Surveille le Midea PortaSplit : magasin proche OU livraison."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--once", action="store_true", help="Une verification puis quitter")
    parser.add_argument("--dry-run", action="store_true", help="Sans sauvegarde ni notification")
    parser.add_argument("--retailer", help="Verifier un seul revendeur (ex: darty)")
    parser.add_argument("--no-browser", action="store_true", help="Desactiver Playwright")
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Ignorer la verification en ligne (magasins uniquement)",
    )
    parser.add_argument("--postal-code", help="Code postal (ex: 33400)")
    parser.add_argument("--radius-km", type=float, help="Rayon magasins en km")
    parser.add_argument(
        "--no-store-alerts",
        action="store_true",
        help="Ne pas notifier les magasins physiques (stock en ligne uniquement)",
    )
    parser.add_argument("--test-telegram", action="store_true", help="Test Telegram")
    parser.add_argument(
        "--test-heartbeat",
        action="store_true",
        help="Envoyer le message quotidien maintenant",
    )
    parser.add_argument(
        "--export",
        type=Path,
        metavar="PATH",
        help="Exporter un snapshot JSON (app mobile / GitHub Actions)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("CHECK_INTERVAL_MINUTES", "2")),
        help="Intervalle en minutes",
    )
    args = parser.parse_args(argv)

    if not args.config.exists():
        print(f"Config introuvable : {args.config}", file=sys.stderr)
        return 1

    if args.test_telegram:
        ok, message = test_telegram()
        print(message)
        return 0 if ok else 1

    if args.test_heartbeat:
        store = StateStore(args.state)
        channels = send_daily_heartbeat(
            store,
            postal_code=args.postal_code or os.getenv("POSTAL_CODE"),
            actionable_count=0,
            force=True,
        )
        if channels:
            print(f"Heartbeat envoye ({', '.join(channels)})")
            return 0
        print("Aucun canal configure (Telegram / Discord / ntfy)")
        return 1

    if args.local_only:
        args.dry_run = args.dry_run  # noqa: B018 — keep flag
        # Magasins seulement : on passe un filtre vide en ligne
        configured_postal, configured_radius = local_config_from_env()
        postal = args.postal_code or configured_postal
        if not postal:
            print("POSTAL_CODE requis", file=sys.stderr)
            return 1
        from .local_stores import fetch_local_stores
        from .availability import build_actionable_offers

        stores = fetch_local_stores(postal, radius_km=args.radius_km or configured_radius)
        offers = build_actionable_offers([], stores, postal)
        print(format_actionable_summary(offers, [], stores, postal, args.radius_km or configured_radius))
        return 0

    if args.once or args.dry_run:
        run_check(
            args.config,
            args.state,
            dry_run=args.dry_run,
            retailer_filter=args.retailer,
            use_browser=not args.no_browser,
            postal_code=args.postal_code,
            radius_km=args.radius_km,
            export_path=args.export,
            notify_stores=not args.no_store_alerts,
        )
        return 0

    print(
        f"Surveillance demarree — toutes les {args.interval} min. Ctrl+C pour arreter.",
        flush=True,
    )
    while True:
        try:
            run_check(
                args.config,
                args.state,
                retailer_filter=args.retailer,
                use_browser=not args.no_browser,
                postal_code=args.postal_code,
                radius_km=args.radius_km,
                notify_stores=not args.no_store_alerts,
            )
        except KeyboardInterrupt:
            print("\nArret.")
            return 0
        except Exception as exc:
            print(f"Erreur inattendue : {exc}", flush=True)
        time.sleep(max(args.interval, 1) * 60)


if __name__ == "__main__":
    raise SystemExit(main())
