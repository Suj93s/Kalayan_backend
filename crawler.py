import asyncio
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeout
)

from config import (
    is_allowed_url,
    canonicalize_url
)

from logger_setup import get_logger


class NovoxCrawler:

    def __init__(
        self,
        max_retries: int = 2,
        max_requests_per_crawl: int = 150
    ):

        self.logger = get_logger()

        self.max_retries = max_retries

        self.max_requests_per_crawl = (
            max_requests_per_crawl
        )

        self.downloaded_pages = {}

        self.stats = {
            "raw_urls_seen": 0,
            "duplicates_removed": 0,
            "junk_filtered": 0,
            "pages_downloaded": 0,
            "pages_failed": 0
        }

        self._seen_canonical = set()

        self._failed_urls = {}

    async def crawl_page(
        self,
        page,
        url
    ):
        """
        Crawl one page.
        """

        canonical_url = (
            canonicalize_url(url)
        )

        # Duplicate protection
        if canonical_url in self._seen_canonical:

            self.stats[
                "duplicates_removed"
            ] += 1

            return

        self._seen_canonical.add(
            canonical_url
        )

        # URL filtering
        if not is_allowed_url(url):

            self.stats[
                "junk_filtered"
            ] += 1

            return

        try:

            self.logger.info(
                f"[CRAWL] {url}"
            )

            # Safer navigation
            await page.goto(
                url,
                wait_until=
                "domcontentloaded",
                timeout=45000
            )

            # Small wait for JS-rendered text
            await page.wait_for_timeout(
                2000
            )

            html = (
                await page.content()
            )

            if html:

                self.downloaded_pages[
                    canonical_url
                ] = html

                self.stats[
                    "pages_downloaded"
                ] += 1

                self.logger.info(
                    f"[OK] "
                    f"{canonical_url}"
                )

            # Extract links
            links = (
                await page.eval_on_selector_all(
                    "a",
                    """
                    elements =>
                    elements.map(
                        el => el.href
                    )
                    """
                )
            )

            for link in links:

                if (
                    len(
                        self.downloaded_pages
                    )
                    >=
                    self.max_requests_per_crawl
                ):
                    break

                if (
                    link
                    and is_allowed_url(
                        link
                    )
                ):

                    canonical = (
                        canonicalize_url(
                            link
                        )
                    )

                    if (
                        canonical
                        not in
                        self._seen_canonical
                    ):

                        await self.crawl_page(
                            page,
                            link
                        )

        except PlaywrightTimeout:

            self.stats[
                "pages_failed"
            ] += 1

            self._failed_urls[
                canonical_url
            ] = "Timeout"

            self.logger.warning(
                f"[TIMEOUT] "
                f"{url}"
            )

        except Exception as e:

            self.stats[
                "pages_failed"
            ] += 1

            self._failed_urls[
                canonical_url
            ] = str(e)

            self.logger.warning(
                f"[ERROR] "
                f"{url}: "
                f"{str(e)}"
            )

    async def start_crawl(
        self,
        seed_urls: list
    ):
        """
        Start crawling.
        """

        self.logger.info(
            f"Starting crawl with "
            f"{len(seed_urls)} "
            f"seed URL(s)"
        )

        async with (
            async_playwright()
            as p
        ):

            browser = (
                await p.chromium.launch(

                    executable_path=
                    "/usr/bin/chromium",

                    headless=True,

                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-setuid-sandbox"
                    ]
                )
            )

            context = (
                await browser.new_context()
            )

            page = (
                await context.new_page()
            )

            for url in seed_urls:

                raw_url = (
                    url.url
                    if hasattr(
                        url,
                        "url"
                    )
                    else str(url)
                )

                await self.crawl_page(
                    page,
                    raw_url
                )

            await browser.close()

        self.logger.info(
            f"Downloaded pages: "
            f"{self.stats['pages_downloaded']}"
        )

        self.logger.info(
            f"Failed pages: "
            f"{self.stats['pages_failed']}"
        )

        return (
            self.downloaded_pages
        )

    def get_failed_urls(
        self
    ):

        return (
            self._failed_urls.copy()
        )