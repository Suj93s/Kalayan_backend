import sys
from pathlib import Path

# Allow imports from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import json
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from backend.embedding import get_embedding
from logger_setup import get_logger

logger = get_logger()

COLLECTION_NAME = "novoxcore"


def rebuild_vector_store():

    chunk_file = (
        ROOT_DIR
        / "cleaned_chunks"
        / "novoxcore_chunks.json"
    )

    if not chunk_file.exists():
        raise FileNotFoundError(
            f"Chunk file not found: {chunk_file}"
        )

    logger.info(
        f"Loading chunks from {chunk_file}"
    )

    with open(
        chunk_file,
        "r",
        encoding="utf-8"
    ) as f:

        chunks = json.load(f)

    logger.info(
        f"Loaded {len(chunks)} chunks"
    )

    # Connect to Qdrant
    client = QdrantClient(
        host="localhost",
        port=6333
    )

    # Delete old collection if exists
    try:

        client.delete_collection(
            collection_name=COLLECTION_NAME
        )

        logger.info(
            f"Deleted old collection: "
            f"{COLLECTION_NAME}"
        )

    except Exception:
        logger.info(
            "No existing collection found."
        )

    # Create fresh collection
    client.create_collection(
        collection_name=COLLECTION_NAME,

        vectors_config=VectorParams(
            size=768,
            distance=Distance.COSINE
        )
    )

    logger.info(
        f"Created collection: "
        f"{COLLECTION_NAME}"
    )

    points = []

    for chunk in chunks:

        text = chunk["text"]

        vector = get_embedding(text)

        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=vector,

                payload={
                    "chunk_id":
                    chunk["id"],

                    "text":
                    text,

                    "source_url":
                    chunk["metadata"][
                        "source_url"
                    ],

                    "word_count":
                    chunk["metadata"].get(
                        "word_count",
                        0
                    )
                }
            )
        )

    logger.info(
        f"Generated embeddings for "
        f"{len(points)} chunks"
    )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    logger.info(
        f"Stored {len(points)} chunks "
        f"in Qdrant"
    )

    return len(points)


if __name__ == "__main__":

    count = rebuild_vector_store()

    print(
        f"\nSUCCESS: Stored "
        f"{count} chunks "
        f"in Qdrant\n"
    )