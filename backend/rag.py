import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from langchain_ollama import ChatOllama

from backend.retrieval import retrieve_context
from backend.prompt import SYSTEM_PROMPT


llm = ChatOllama(
    model="llama3"
)


def answer_question(question: str):

    contexts = retrieve_context(
        question,
        k=1
    )

    if not contexts:
        return (
            "I couldn't find that "
            "information in the "
            "knowledge base."
        )

    # Use only the best matching chunk
    context_text = contexts[0]

    prompt = f"""
{SYSTEM_PROMPT}

CONTEXT:
{context_text}

QUESTION:
{question}

Provide a complete but concise answer.
List all major services or capabilities when relevant,
but omit technical sub-details.

ANSWER:
"""

    try:

        response = llm.invoke(prompt)

        if not response.content:
            return (
                "I couldn't generate "
                "an answer."
            )

        return response.content.strip()

    except Exception as e:

        return (
            f"Error generating answer: "
            f"{str(e)}"
        )


def main():

    print("=" * 60)
    print("NOVOXCORE AI ASSISTANT")
    print("Type 'exit' to quit")
    print("=" * 60)

    while True:

        question = input(
            "\nAsk: "
        ).strip()

        if not question:
            continue

        if question.lower() in [
            "exit",
            "quit"
        ]:
            print("\nGoodbye!")
            break

        answer = answer_question(
            question
        )

        print("\nAnswer:")
        print("-" * 60)
        print(answer)
        print("-" * 60)


if __name__ == "__main__":
    main()