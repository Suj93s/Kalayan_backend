#!/usr/bin/env python3
"""
RAG Backend - Website Knowledge Base Ingestion Pipeline

This script crawls configured websites,
extracts content, and builds a
knowledge base for the RAG chatbot backend.
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import List

# Auto-run using venv python
if sys.prefix == sys.base_prefix:

    venv_python = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        ".venv",
        "bin",
        "python"
    )

    if os.path.exists(venv_python):
        os.execv(
            venv_python,
            [venv_python] + sys.argv
        )

from crawlee import Request
from crawler import NovoxCrawler
from ingest import (
    clean_website_text,
    generate_overlapping_chunks
)
from config import canonicalize_url
from logger_setup import (
    setup_logging,
    get_logger
)
from change_detector import (
    ChangeDetector
)
from backend.vector_store import rebuild_vector_store



class RagPipeline:
    """
    Main ingestion pipeline.
    """

    def __init__(
        self,
        config_file: str = "config.json"
    ):

        self.config_file = config_file

        self.config = (
            self._load_config()
        )

        self.logger = get_logger()

        self.change_detector = (
            ChangeDetector(
                self.config[
                    "output"
                ]["state_file"]
            )
        )

    def _load_config(
        self
    ) -> dict:
        """
        Load config.
        """

        with open(
            self.config_file,
            "r"
        ) as f:

            return json.load(f)

    async def run(self) -> bool:
        """
        Run full pipeline.
        """

        self.logger.info(
            "=" * 70
        )

        self.logger.info(
            "RAG BACKEND "
            "KNOWLEDGE BASE UPDATE"
        )

        self.logger.info(
            "=" * 70
        )

        try:

            websites = self.config.get(
                "websites",
                {}
            )

            total_chunks = 0

            for (
                website_key,
                website_config
            ) in websites.items():

                if not website_config.get(
                    "enabled",
                    False
                ):

                    self.logger.info(
                        f"Skipping disabled "
                        f"website: "
                        f"{website_config['name']}"
                    )

                    continue

                self.logger.info(
                    f"\nProcessing: "
                    f"{website_config['name']}"
                )

                chunks = (
                    await self._process_website(
                        website_key,
                        website_config
                    )
                )

                total_chunks += (
                    len(chunks)
                )

            self.logger.info(
                "=" * 70
            )

            self.logger.info(
                f"TOTAL CHUNKS "
                f"GENERATED: "
                f"{total_chunks}"
            )

            self.logger.info("Populating Qdrant vector store...")
            stored_count = rebuild_vector_store()
            self.logger.info(f"Stored {stored_count} chunks in Qdrant")

            self.logger.info(
                "Update completed "
                "successfully"
            )

            self.logger.info(
                "=" * 70
            )

            return True

        except Exception as e:

            self.logger.error(
                f"Pipeline error: {e}",
                exc_info=True
            )

            self.logger.info(
                "=" * 70
            )

            return False

    async def _process_website(
        self,
        website_key: str,
        website_config: dict
    ) -> List[dict]:
        """
        Process one website.
        """

        name = website_config["name"]

        url = website_config["url"]

        max_pages = (
            website_config.get(
                "max_pages",
                150
            )
        )

        self.logger.info(
            f"Starting crawl: "
            f"{url}"
        )

        # Create crawler
        crawler = NovoxCrawler(
            max_retries=
            self.config[
                "crawler"
            ].get(
                "max_retries",
                2
            ),

            max_requests_per_crawl=
            max_pages
        )

        # Seed request
        seed_request = (
            Request.from_url(
                url=url,
                unique_key=
                canonicalize_url(
                    url
                )
            )
        )

        # Crawl
        raw_site_data = (
            await crawler.start_crawl(
                [seed_request]
            )
        )

        crawler_stats = (
            crawler.stats
        )

        self.logger.info(
            f"Downloaded: "
            f"{crawler_stats['pages_downloaded']} "
            f"pages"
        )

        self.logger.info(
            f"Duplicates removed: "
            f"{crawler_stats['duplicates_removed']}"
        )

        self.logger.info(
            f"Junk filtered: "
            f"{crawler_stats['junk_filtered']}"
        )

        if (
            crawler_stats[
                "pages_failed"
            ] > 0
        ):

            self.logger.warning(
                f"Failed: "
                f"{crawler_stats['pages_failed']} "
                f"pages"
            )

        # Process HTML → chunks
        chunks = (
            await self._process_content(
                raw_site_data
            )
        )

        # Save chunks
        output_dir = Path(
            self.config[
                "output"
            ]["chunks_dir"]
        )

        output_dir.mkdir(
            exist_ok=True
        )

        output_file = (
            output_dir /
            f"{website_key}_chunks.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                chunks,
                f,
                indent=2,
                ensure_ascii=False
            )

        self.logger.info(
            f"Chunks generated: "
            f"{len(chunks)}"
        )

        self.logger.info(
            f"Saved to: "
            f"{output_file}"
        )

        # Save change hash
        content_hash = json.dumps(
            chunks,
            sort_keys=True
        )

        self.change_detector.update_hash(
            website_key,
            content_hash
        )

        return chunks

    async def _process_content(
        self,
        raw_site_data: dict
    ) -> List[dict]:
        """
        Convert raw HTML
        into chunks.
        """

        chunks = []

        chunk_size = (
            self.config[
                "chunking"
            ]["chunk_size"]
        )

        overlap = (
            self.config[
                "chunking"
            ]["chunk_overlap"]
        )

        for (
            url,
            html_content
        ) in raw_site_data.items():

            is_contact = (
                "contact"
                in url.lower()
            )

            clean_text = (
                clean_website_text(
                    html_content,
                    skip_nav_footer=False
                )
            )

            if not clean_text:

                self.logger.debug(
                    f"Empty text: {url}"
                )

                continue

            # Homepage detection
            if url.rstrip("/") == "https://kalyanjewellerymachines.com":
                page_name = "home"
            else:
                page_name = (
                    url.rstrip("/")
                    .split("/")[-1]
                )

            min_chunk_words = self.config["chunking"].get("min_chunk_words", 15)

            # Chunk generation
            if is_contact or page_name == "services":

                text_chunks = (
                    generate_overlapping_chunks(
                        clean_text,
                        chunk_size=chunk_size,
                        overlap=overlap,
                        min_chunk_words=5
                    )
                )

            else:

                text_chunks = (
                    generate_overlapping_chunks(
                        clean_text,
                        chunk_size=chunk_size,
                        overlap=overlap,
                        min_chunk_words=min_chunk_words
                    )
                )

            for idx, chunk_text in enumerate(text_chunks):

                # Page-specific keywords
                keywords = {
                    "about": "company history about us 1969 exclusive company",
                    "contact": "contact email phone address reach us location Calicut",
                    "products": "products machines Jewellery Rolling Machines Hydraulic Coining Presses Gold Tar Patti Machines precision rolling",
                    "home": "Kalyan Jewellery Machines manufacturer of jewellery manufacturing machines precision rolling"
                }

                page_keywords = keywords.get(
                    page_name.lower(),
                    ""
                )
                if page_name == "home":
                    chunk_text = (
                        "Kalyan engineering corporation is an exclusive company specializing "
                        "in the manufacture of various kinds of jewellery manufacturing machines since 1969.\n\n"
                        + chunk_text
                    )
                enhanced_chunk = (
                    f"Page: {page_name}\n"
                    f"Keywords: {page_keywords}\n"
                    f"Source: {url}\n\n"
                    f"{chunk_text}"
                )

                chunks.append({
                    "id": f"{url}#chunk-{idx}",
                    "text": enhanced_chunk,
                    "metadata": {
                        "source_url": url,
                        "page_name": page_name,
                        "chunk_index": idx,
                        "word_count": len(
                            enhanced_chunk.split()
                        )
                    }
                })

        return chunks


def main():
    """
    Main entry.
    """

    setup_logging(
        logs_dir="logs"
    )

    logger = (
        get_logger()
    )

    try:

        pipeline = (
            RagPipeline()
        )

        success = asyncio.run(
            pipeline.run()
        )

        sys.exit(
            0 if success else 1
        )

    except Exception as e:

        logger.error(
            f"Fatal error: {e}",
            exc_info=True
        )

        sys.exit(1)


if __name__ == "__main__":
    main()