import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from ingest import clean_website_text

with open("../novox-core-website/team.html", "r", encoding="utf-8") as f:
    html = f.read()

cleaned = clean_website_text(html, skip_nav_footer=False)
print("=== CLEANED TEXT ===")
print(cleaned)
