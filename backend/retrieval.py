import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from qdrant_client import QdrantClient
from backend.embedding import get_embedding

COLLECTION_NAME = "kalyan"

client = QdrantClient(
    path="qdrant_db"
)

MIN_SCORE = 0.40


def retrieve_context(
    query: str,
    k: int = 5
):
    query_lower = query.lower()

    # Query rewriting for company overview questions
    if any(q in query_lower for q in [
        "what is kalyan", "tell me about", "tell about", "who are you", 
        "about kalyan", "company overview", "about your company"
    ]):
        query = query_lower + " kalyan engineering corporation company overview jewellery manufacturing machines 1969 exclusive company calicut"

    # Query rewriting for services/products questions
    elif (
        "products" in query_lower.split()
        or "machines" in query_lower.split()
        or "what do you do" in query_lower
        or "manufacture" in query_lower
    ):
        query = query_lower + " Jewellery Rolling Machines Hydraulic Coining Presses Gold Tar Patti Machines precision rolling"
        
    query_vector = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=10  # Retrieve more for reranking
    ).points

    contexts = []
    
    # Reranking based on exact keyword matches
    query_terms = set(query_lower.split())
    
    reranked_results = []
    for r in results:
        chunk_text = r.payload["text"]
        chunk_lower = chunk_text.lower()
        
        # Calculate term overlap
        overlap = sum(1 for term in query_terms if term in chunk_lower)
        
        # Final score = semantic score + (overlap * 0.05)
        final_score = r.score + (overlap * 0.05)
        
        reranked_results.append((final_score, r, chunk_text))
        
    # Sort by final score descending
    reranked_results.sort(key=lambda x: x[0], reverse=True)
    
    # Debug logging
    print(f"--- RETRIEVAL DEBUG FOR: '{query}' ---")
    for i, (f_score, r, chunk_text) in enumerate(reranked_results[:k]):
        source_url = r.payload.get("metadata", {}).get("source_url", "unknown")
        print(f"[{i+1}] Score: {r.score:.4f} | Reranked: {f_score:.4f} | URL: {source_url}")
        print(f"Preview: {chunk_text[:100].replace(chr(10), ' ')}...\n")

        if r.score >= MIN_SCORE:
            contexts.append(chunk_text)

    return contexts