from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

def get_embedding(text: str):
    return embeddings.embed_query(text)