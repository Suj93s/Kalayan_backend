import sys
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.rag import answer_question

def test():
    print("Testing valid question...")
    ans1 = answer_question("What services does NovoxCore provide?")
    print("Answer 1:", ans1)
    print("-" * 50)
    
    print("Testing hallucination question...")
    ans2 = answer_question("What is the recipe for NovoxCore's special chocolate cake?")
    print("Answer 2:", ans2)
    print("-" * 50)

if __name__ == "__main__":
    test()
