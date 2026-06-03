import sys
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.retrieval import retrieve_context
from backend.rag import answer_question

def test():
    query = "What is the contact email and phone number?"
    
    print("--- RETRIEVAL TEST ---")
    contexts = retrieve_context(query, k=2)
    for i, ctx in enumerate(contexts):
        print(f"\nChunk {i+1}:")
        print(ctx)
        
    print("\n--- LLM TEST ---")
    ans = answer_question(query)
    print(ans)

if __name__ == "__main__":
    test()
