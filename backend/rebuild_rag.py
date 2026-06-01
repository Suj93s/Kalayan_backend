"""RAG helper functions.

This module ties chunk files to the vector store rebuild routine.
"""
import json
from pathlib import Path
from logger_setup import get_logger
from backend.vector_store import rebuild_vector_store

logger = get_logger()


def rebuild_for_website(website_key: str, chunks_file: str, vector_dir: str = "vector_db") -> None:
    chunks_path = Path(chunks_file)
    if not chunks_path.exists():
        logger.error(f"Chunks file not found: {chunks_file}")
        return

    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    logger.info(f"Rebuilding vector store for {website_key} from {len(chunks)} chunks")
    rebuild_vector_store(chunks, output_dir=vector_dir)
    logger.info(f"Vector store rebuilt for {website_key}")
