import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

# We only initialize if the API key is present to avoid crashing immediately on import
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )
else:
    embeddings = None

def get_embedding(text: str):
    if not embeddings:
        raise ValueError("GOOGLE_API_KEY is missing. Cannot generate embeddings.")
    
    try:
        return embeddings.embed_query(text)[:768]
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg or "exhausted" in error_msg:
            raise RuntimeError("Gemini API rate limit exceeded.") from e
        else:
            raise RuntimeError(f"Gemini API failure: {str(e)}") from e

def get_embeddings(texts: list[str]):
    if not embeddings:
        raise ValueError("GOOGLE_API_KEY is missing. Cannot generate embeddings.")
    
    import time
    results = []
    # Batch into smaller chunks to avoid payload too large, but wait between batches
    batch_size = 5
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            batch_results = embeddings.embed_documents(batch)
            results.extend([res[:768] for res in batch_results])
            time.sleep(4.5)  # Stay under 15 RPM just in case it counts requests per doc or batch
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg or "exhausted" in error_msg:
                raise RuntimeError("Gemini API rate limit exceeded.") from e
            else:
                raise RuntimeError(f"Gemini API failure: {str(e)}") from e
    return results