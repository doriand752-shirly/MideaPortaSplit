from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from .models import StockStatus
from .notifiers import format_summary, notify_stock_available
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
) -> list:
    retailers = load_retailers(config_path)
    if retailer_filter:
        retailers = [r for r in retailers if r.id == retailer_filter]
        if not retailers:
            print(f"Revendeur inconnu ou désactivé : {retailer_filter}", file=sys.stderr)
            return []

    if verbose:
        print(f"Vérification de {len(retailers)} revendeur(s) en parallèle...", flush=True)

    results = check_all_retailers(retailers)
    store = StateStore(state_path)

    for result in results:
        if dry_run:
            continue

        became_available = store.update(result)
        if became_available:
            channels = notify_stock_available(result)
            if channels:
                print(
                    f"[ALERTE] Envoyee ({', '.join(channels)}) : {result.retailer.name}",
                    flush=True,
                )
            else:
                print(
                    f"[STOCK] {result.retailer.name} — configurez Telegram dans .env",
                    flush=True,
                )

    if not dry_run:
        store.save()

    if verbose:
        print()
        print(format_summary(results))
        available = [r for r in results if r.status == StockStatus.IN_STOCK]
        errors = [r for r in results if r.status == StockStatus.ERROR]
        if available:
            print()
            print(f"{len(available)} revendeur(s) avec stock detecte !")
        else:
            print()
            print("Aucun stock detecte pour l'instant.")
        if errors:
            print(f"{len(errors)} erreur(s) reseau — verifiez les URLs dans config.yaml")

    return results


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Surveille la disponibilité du Midea PortaSplit chez les revendeurs français."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--once", action="store_true", help="Une vérification puis quitter")
    parser.add_argument("--dry-run", action="store_true", help="Sans sauvegarde ni notification")
    parser.add_argument("--retailer", help="Vérifier un seul revendeur (ex: darty)")
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("CHECK_INTERVAL_MINUTES", "5")),
        help="Intervalle en minutes (mode boucle)",
    )
    args = parser.parse_args(argv)

    if not args.config.exists():
        print(f"Config introuvable : {args.config}", file=sys.stderr)
        return 1

    if args.once or args.dry_run:
        run_check(
            args.config,
            args.state,
            dry_run=args.dry_run,
            retailer_filter=args.retailer,
        )
        return 0

    print(
        f"Surveillance démarrée — toutes les {args.interval} min. Ctrl+C pour arrêter.",
        flush=True,
    )
    while True:
        try:
            run_check(args.config, args.state, retailer_filter=args.retailer)
        except KeyboardInterrupt:
            print("\nArrêt.")
            return 0
        except Exception as exc:
            print(f"Erreur inattendue : {exc}", flush=True)
        time.sleep(max(args.interval, 1) * 60)


if __name__ == "__main__":
    raise SystemExit(main())
