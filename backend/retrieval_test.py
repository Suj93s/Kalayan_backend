import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from qdrant_client import QdrantClient
from backend.embedding import get_embedding

COLLECTION_NAME = "novoxcore"

client = QdrantClient(
    host="localhost",
    port=6333
)

MIN_SCORE = 0.40


def search_query(query: str):

    query_vector = get_embedding(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3
    ).points

    filtered_results = []

    for result in results:

        if result.score >= MIN_SCORE:
            filtered_results.append(result)

    return filtered_results


def main():

    print("=" * 60)
    print("NOVOXCORE RETRIEVAL TEST")
    print("Top 3 Results Mode")
    print("Type 'exit' to quit")
    print("=" * 60)

    while True:

        query = input("\nAsk: ").strip()

        if query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not query:
            continue

        try:

            results = search_query(query)

            if not results:
                print("\nInformation not found.")
                continue

            print("\nTOP MATCHES")
            print("-" * 60)

            for i, result in enumerate(results, start=1):

                print(f"\nResult {i}")

                print(
                    f"Score: {round(result.score, 4)}"
                )

                print("\nAnswer Source Text:")
                print(
                    result.payload.get(
                        "text",
                        ""
                    )
                )

                print("\nSource:")
                print(
                    result.payload.get(
                        "source_url",
                        "Unknown"
                    )
                )

                print("-" * 60)

        except Exception as e:

            print(
                f"\nError: {str(e)}"
            )


if __name__ == "__main__":
    main()