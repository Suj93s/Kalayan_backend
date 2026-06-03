import asyncio
import json
from crawler import NovoxCrawler
from ingest import clean_website_text, generate_overlapping_chunks
from bs4 import BeautifulSoup
import re

async def main():
    crawler = NovoxCrawler(max_requests_per_crawl=1)
    from crawlee import Request
    pages = await crawler.start_crawl([Request.from_url("https://novoxcore.com/contact")])
    for url, html in pages.items():
        print(f"--- URL: {url} ---")
        
        soup = BeautifulSoup(html, "html.parser")
        contacts = []
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").strip()
                if email not in contacts:
                    contacts.append(f"Email: {email}")
            elif href.startswith("tel:"):
                phone = href.replace("tel:", "").strip()
                if phone not in contacts:
                    contacts.append(f"Phone: {phone}")
        print("Found contacts in HTML:", contacts)
        
        clean = clean_website_text(html, skip_nav_footer=True)
        print("Cleaned Text:\n", clean)
        
        chunks = generate_overlapping_chunks(clean, chunk_size=200, overlap=30, min_chunk_words=5)
        print("Chunks:", chunks)

if __name__ == "__main__":
    asyncio.run(main())
