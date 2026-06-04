import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from ingest import clean_website_text, generate_overlapping_chunks

with open("../novox-core-website/team.html", "r", encoding="utf-8") as f:
    html = f.read()

cleaned = clean_website_text(html, skip_nav_footer=False)
chunks = generate_overlapping_chunks(cleaned, chunk_size=300, overlap=50, min_chunk_words=15)
for i, c in enumerate(chunks):
    print(f"--- Chunk {i} ---")
    print(c)
