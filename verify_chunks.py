import json
import sys

def verify_data(keyword=None):
    try:
        with open("cleaned_chunks.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except FileNotFoundError:
        print("Error: cleaned_chunks.json not found. Run the pipeline first.")
        return
    except json.JSONDecodeError:
        print("Error: cleaned_chunks.json is corrupted or not valid JSON.")
        return

    # Gather stats
    total_chunks = len(chunks)
    unique_urls = set(chunk["metadata"]["source_url"] for chunk in chunks)
    
    print("=" * 60)
    print("                PIPELINE DATA VERIFICATION")
    print("=" * 60)
    print(f"Total Chunks Extracted : {total_chunks}")
    print(f"Unique URLs Crawled   : {len(unique_urls)}")
    print("-" * 60)
    print("Crawled URLs:")
    for idx, url in enumerate(sorted(unique_urls), 1):
        print(f"  {idx}. {url}")
    print("-" * 60)

    if keyword:
        print(f"Searching for chunks containing keyword: '{keyword}'...")
        print("=" * 60)
        found_count = 0
        for chunk in chunks:
            if keyword.lower() in chunk["text"].lower():
                found_count += 1
                print(f"Chunk ID   : {chunk['id']}")
                print(f"Source URL : {chunk['metadata']['source_url']}")
                print(f"Word Count : {chunk['metadata']['word_count']}")
                print(f"Snippet    : ... {chunk['text'][:150]} ...")
                print("-" * 60)
        
        print(f"Found {found_count} matching chunks.")
    else:
        print("\nTip: Pass a search keyword to inspect specific chunks, e.g.:")
        print("     python verify_chunks.py <keyword>")
    print("=" * 60)

if __name__ == "__main__":
    search_keyword = sys.argv[1] if len(sys.argv) > 1 else None
    verify_data(search_keyword)
