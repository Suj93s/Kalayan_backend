import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from qdrant_client import QdrantClient
from backend.embedding import get_embedding

COLLECTION_NAME = "novoxcore"

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
        "what is novox", "tell me about", "tell about", "who are you", 
        "about novox", "company overview", "about your company", "edtech llp"
    ]):
        query = query_lower + " novoxcore company overview digital product agency team 20+ skilled employees AI capabilities ML integration automation IoT certifications Google Certified Flutter Developer startup agency"

    # Query rewriting for services questions
    elif (
        "services" in query_lower.split()
        or "what do you do" in query_lower
        or "capabilities" in query_lower
    ):
        query = query_lower + " services Web Development Mobile App Development Data Analytics Digital Marketing UI/UX Design AI/ML Integration IoT Solutions No-Code Solutions"
        
    # Query rewriting for technology questions
    elif any(q in query_lower for q in [
        "technologies", "tech stack", "what do you use", "how do you build"
    ]):
        query = query_lower + " technologies AI ML IoT SEO automation Adobe tools Flutter AI capabilities ML integration automation"

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