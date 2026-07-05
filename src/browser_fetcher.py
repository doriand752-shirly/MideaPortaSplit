from __future__ import annotations

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightError = Exception  # type: ignore[misc, assignment]


class BrowserFetcher:
    """Navigateur headless pour les sites qui bloquent les requetes HTTP simples."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None

    def __enter__(self) -> BrowserFetcher:
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright requis. Executez: pip install playwright "
                "puis playwright install chromium"
            )
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        return self

    def __exit__(self, *args: object) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def fetch(self, url: str, *, timeout_ms: int = 35_000) -> str:
        if not self._browser:
            raise RuntimeError("BrowserFetcher non initialise — utilisez 'with BrowserFetcher()'")

        context = self._browser.new_context(
            user_agent=USER_AGENT,
            locale="fr-FR",
            viewport={"width": 1366, "height": 768},
            extra_http_headers={"Accept-Language": "fr-FR,fr;q=0.9"},
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(2500)
            return page.content()
        except PlaywrightError as exc:
            raise RuntimeError(f"Playwright: {exc}") from exc
        finally:
            context.close()


def is_playwright_available() -> bool:
    return PLAYWRIGHT_AVAILABLE
