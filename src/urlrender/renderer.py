
from dataclasses import dataclass
from time import perf_counter
from urllib.parse import urlparse

from playwright.sync_api import (
    Browser,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from .exceptions import NavigationError, RenderTimeoutError


@dataclass(slots=True)
class RenderResult:
    """Result returned by a page rendering operation."""

    url: str
    html: str
    text: str
    status_code: int | None
    title: str
    elapsed_ms: float


class Renderer:
    """Render JavaScript-enabled web pages using Playwright Chromium."""

    def __init__(
        self,
        *,
        timeout: int = 15_000,
        wait_until: str = "domcontentloaded",
        headless: bool = True,
        viewport_width: int = 1366,
        viewport_height: int = 768,
    ):
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        if wait_until not in {
            "commit",
            "domcontentloaded",
            "load",
            "networkidle",
        }:
            raise ValueError("Invalid wait_until value")

        self.timeout = timeout
        self.wait_until = wait_until
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._closed = False


    def start(self) -> "Renderer":
        """Start Playwright and launch Chromium."""

        if self._closed:
            raise RuntimeError("This Renderer has been closed")

        if self._browser is not None and self._browser.is_connected():
            return self

        if self._playwright is None:
            self._playwright = sync_playwright().start()

        try:
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ],
            )
        except Exception:
            self._playwright.stop()
            self._playwright = None
            raise

        return self



    def render(self, url: str, *, wait_for_selector: str | None = None,) -> RenderResult:
        """Render a URL and return its HTML, text, and metadata."""

        url = self._normalize_url(url)
        self.start()

        assert self._browser is not None

        started_at = perf_counter()

        try:
            v = {
                 "width": self.viewport_width,
                 "height": self.viewport_height,
                }
            
            with self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport=v,
                java_script_enabled=True
            ) as context:
                page = context.new_page()
                page.set_default_navigation_timeout(self.timeout)
                page.set_default_timeout(self.timeout)

                response = page.goto(
                    url,
                    timeout=self.timeout,
                    wait_until=self.wait_until,
                )

                try:
                    page.wait_for_load_state(
                        "networkidle",
                        timeout=5_000,
                    )
                except PlaywrightTimeoutError:
                    pass

                if wait_for_selector:
                    page.wait_for_selector(
                        wait_for_selector,
                        state="attached",
                        timeout=self.timeout,
                    )

                html = page.content()

                text = page.locator("body").inner_text() if page.locator(
                    "body"
                ).count() else ""

                title = page.title()

                return RenderResult(
                    url=page.url,
                    html=html,
                    text=text.strip(),
                    status_code=response.status if response else None,
                    title=title,
                    elapsed_ms=round(
                        (perf_counter() - started_at) * 1000,
                        2,
                    ),
                )

        except PlaywrightTimeoutError as exc:
            raise RenderTimeoutError(
                f"Rendering timed out for {url}"
            ) from exc

        except NavigationError:
            raise

        except Exception as exc:
            raise NavigationError(
                f"Failed to render {url}: {exc}"
            ) from exc


    def get_html(self, url: str) -> str:
        """Return the rendered HTML of a URL."""
        return self.render(url).html


    def get_text(self, url: str) -> str:
        """Return the visible text of a URL."""
        return self.render(url).text


    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize and validate an HTTP or HTTPS URL."""

        if not isinstance(url, str) or not url.strip():
            raise ValueError("A non-empty URL is required")

        url = url.strip()
        parsed = urlparse(url)

        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("URL must be a valid HTTP or HTTPS URL")

        if parsed.username is not None or parsed.password is not None:
            raise ValueError("URLs containing credentials are not supported")

        try:
            parsed.port
        except ValueError as exc:
            raise ValueError("URL contains an invalid port") from exc

        return url


    def close(self) -> None:
        """Close Chromium and stop Playwright."""

        if self._closed:
            return

        self._closed = True

        try:
            if self._browser is not None:
                self._browser.close()
                self._browser = None
        finally:
            if self._playwright is not None:
                self._playwright.stop()
                self._playwright = None


    def __enter__(self) -> "Renderer":
        return self.start()


    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


