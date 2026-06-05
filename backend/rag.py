import sys
import os
import re
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.retrieval import retrieve_context
from backend.prompt import SYSTEM_PROMPT


def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash"
    )

llm = get_llm()


def answer_question(question: str):
    # Remove punctuation for flexible matching
    q_clean = re.sub(r'[^\w\s]', '', question.strip().lower())
    
    # Handle greetings (fuzzy match for variations of hi, hello, hey, good morning, etc)
    if re.match(r'^(h[i]+|h[e]+l+[o]+|h[e]+y+|good\s*(morning|afternoon|evening)|gm)$', q_clean):
        return (
            "Hi! 👋\n\n"
            "Welcome to Kalyan AI.\n\n"
            "How can I help you today?\n\n"
            "• Products\n"
            "• Services\n"
            "• Contact\n"
            "• About Us"
        )
        
    # Handle thanks and bye
    if re.match(r'^(thanks|thank\s*you|thx)$', q_clean):
        return "You're welcome! Let me know if you need anything else. 😊"
        
    if re.match(r'^(bye|goodbye|see\s*you)$', q_clean):
        return "Goodbye! Have a great day! 👋"

    contexts = retrieve_context(
        question,
        k=8
    )

    if not contexts:
        return (
            "I couldn't find that "
            "information in the "
            "knowledge base."
        )

    # 1. Retrieved chunks from Qdrant
    print("\n" + "="*50)
    print("DEBUG - 1. Retrieved chunks from Qdrant:")
    for idx, chunk in enumerate(contexts):
        print(f"--- Chunk {idx + 1} ---\n{chunk}\n")

    # Combine the top matching chunks
    context_text = "\n\n".join(contexts)

    # 2. Raw context sent to Gemini
    print("DEBUG - 2. Raw context sent to Gemini:")
    print(f"{context_text}\n")

    prompt = f"""
{SYSTEM_PROMPT}

CONTEXT:
{context_text}

QUESTION:
{question}

Provide a complete but concise answer based ONLY on the context above.

ANSWER:
"""

    # 3. Final prompt sent to Gemini
    print("DEBUG - 3. Final prompt sent to Gemini:")
    print(f"{prompt}\n")

    if not llm:
        return "Error: GOOGLE_API_KEY is not set. Please check your .env configuration."

    try:

        response = llm.invoke(prompt)

        # 4. Gemini response before formatting
        print("DEBUG - 4. Gemini response before formatting:")
        print(f"{repr(response)}\n")
        print("="*50 + "\n")

        if not response.content:
            return (
                "I couldn't generate "
                "an answer."
            )

        return response.content.strip()

    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg or "exhausted" in error_msg:
            return "Error: Gemini API rate limit exceeded. Please try again later."
        elif "api_key" in error_msg or "api key" in error_msg or "unauthenticated" in error_msg:
            return "Error: Invalid or missing Google API key."
        else:
            return f"Gemini API failure: {str(e)}"


def main():

    print("=" * 60)
    print("KALYAN AI ASSISTANT")
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