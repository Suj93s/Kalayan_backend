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