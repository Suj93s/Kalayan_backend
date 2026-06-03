import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.retrieval import retrieve_context

def test_retrieval(query: str):
    print(f"\n==== Testing Query via retrieve_context: {query} ====")
    contexts = retrieve_context(query)
    print(f"Retrieved {len(contexts)} contexts.")

test_retrieval("Services")
test_retrieval("What services do you provide?")
test_retrieval("Web development")
test_retrieval("AI services")
