import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.retrieval import retrieve_context

queries = [
    "who is the director",
    "who is the md",
    "who is the founder",
]

for q in queries:
    print(f"=== Query: {q} ===")
    contexts = retrieve_context(q, k=3)
    if not contexts:
        print("No results found.")
    else:
        for i, ctx in enumerate(contexts):
            print(f"[{i}] {ctx}")
