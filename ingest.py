import re
from difflib import SequenceMatcher
import trafilatura

# Navigation/footer keywords that indicate a line is junk
_NAV_KEYWORDS = {"home", "about", "services", "service", "team", "blog", "contact", "careers",
                 "let's talk", "lets talk", "privacy", "terms", "cookie", "all rights reserved",
                 "copyright", "©", "follow us", "get in touch", "subscribe"}

# Minimum number of words a chunk must have to be included
MIN_CHUNK_WORDS = 30


def _is_nav_or_footer_line(line: str) -> bool:
    """Returns True if the line looks like a navbar, footer, or CTA text."""
    clean = line.strip().lower()
    if not clean:
        return False

    words = re.findall(r"[\w']+", clean)
    if len(words) == 0:
        return True
    # If the line is very short (≤10 words) and mostly nav keywords, discard it
    matched = sum(1 for w in words if w in _NAV_KEYWORDS or clean in _NAV_KEYWORDS)
    if len(words) <= 10 and matched / len(words) >= 0.5:
        return True

    # Detect common footer / CTA exact phrases
    for phrase in ("let's talk", "lets talk", "all rights reserved", "©"):
        if phrase in clean and len(words) <= 12:
            return True
    return False


def _remove_nav_footer(text: str) -> str:
    """Removes navbar/footer lines from extracted text."""
    lines = text.splitlines()
    cleaned = [line for line in lines if not _is_nav_or_footer_line(line)]
    return "\n".join(cleaned).strip()


def _split_sentences(text: str) -> list[str]:
    """Splits text into sentences, handling various boundary patterns."""
    # First, mark email and phone patterns as sentence boundaries by adding periods
    text = re.sub(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+', r'\1. ', text)
    text = re.sub(r'(\+\d{1,3}\s*[\d\s-]{6,})\s+', r'\1. ', text)
    
    # Also mark places where we have "word. Word" or "word Word" where it looks like
    # a sentence continuation. For long text, split on capital letters that aren't
    # part of an acronym (if there's a preceding lowercase letter or punctuation)
    # This helps catch repeated paragraphs that run together
    
    # Split on standard sentence boundaries: period/exclamation/question + space
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # For very long "sentences" (>150 chars), try to split on capital letters
    # if they appear after lowercase letters (suggesting a new sentence start)
    result = []
    for s in sentences:
        if len(s) > 150:
            # Split where we see lowercase-to-uppercase transitions with space
            parts = re.split(r'(?<=[a-z])\s+(?=[A-Z])', s)
            result.extend(parts)
        else:
            result.append(s)
    
    return [s.strip() for s in result if s.strip()]


def _deduplicate_sentences(sentences: list[str]) -> list[str]:
    """Removes duplicate or near-duplicate sentences while preserving order.

    Aggressive approach: removes exact and very similar sentences, using
    lower thresholds to catch real duplicates.
    """
    seen_norms: list[tuple[str, str]] = []  # (normalized, original)
    result: list[str] = []

    def normalize(s: str) -> str:
        # Collapse multiple spaces/newlines
        s2 = re.sub(r'\s+', ' ', s)
        # Remove punctuation
        s2 = re.sub(r'[^\w\s]', '', s2, flags=re.UNICODE)
        return s2.strip().lower()

    for s in sentences:
        norm = normalize(s)
        
        if not norm:
            continue

        is_dup = False
        
        # Check against all previously seen normalized sentences
        for prev_norm, _ in seen_norms:
            if not prev_norm:
                continue
            # Exact match: skip
            if norm == prev_norm:
                is_dup = True
                break
            
            # For non-trivial length content, use aggressive fuzzy matching
            # Lower threshold to catch paraphrases and restructured duplicates
            if len(norm) > 20 and len(prev_norm) > 20:
                ratio = SequenceMatcher(None, norm, prev_norm).ratio()
                if ratio >= 0.80:  # Lowered to catch more near-duplicates
                    is_dup = True
                    break

        if not is_dup:
            seen_norms.append((norm, s))
            result.append(s)

    return result


from bs4 import BeautifulSoup

def clean_website_text(
    raw_html: str,
    skip_nav_footer: bool = False
) -> str:
    """
    Extract content using Trafilatura first.
    Then supplement with BeautifulSoup to capture
    service cards, feature grids, and headings.
    """

    extracted = trafilatura.extract(
        raw_html,
        include_links=True,
        include_images=False,
        include_tables=True,
        favor_recall=True,
        favor_precision=False
    )

    if not extracted:
        extracted = ""

    # Fallback extraction for cards/headings
    soup = BeautifulSoup(
        raw_html,
        "html.parser"
    )

    extra_content = []

    for tag in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "li"
        ]
    ):
        text = tag.get_text(
            " ",
            strip=True
        )

        if (
            text
            and len(text.split()) >= 2
            and text not in extra_content
        ):
            extra_content.append(text)

    if extra_content:
        extracted += "\n\n" + "\n".join(
            extra_content
        )

    extracted = re.sub(
        r"\s+",
        " ",
        extracted
    )

    # Optional nav/footer cleaning
    if not skip_nav_footer:
        extracted = _remove_nav_footer(
            extracted
        )

    sentences = _split_sentences(
        extracted
    )

    sentences = _deduplicate_sentences(
        sentences
    )

    return " ".join(sentences)


def generate_overlapping_chunks(text: str, chunk_size: int = 200, overlap: int = 30, min_chunk_words: int | None = None) -> list[str]:
    """
    Splits prose into sentence-aware overlapping chunks.
    Each chunk targets ~chunk_size words. Overlap is achieved by including
    the last `overlap` words of the previous chunk as a prefix for the next.
    Chunks below MIN_CHUNK_WORDS are discarded.
    """
    if not text:
        return []

    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks = []
    current_sentences: list[str] = []
    current_word_count = 0
    overlap_buffer: list[str] = []  # tail sentences carried over for overlap

    for sentence in sentences:
        word_count = len(sentence.split())
        if current_word_count + word_count > chunk_size and current_sentences:
            # Emit the current chunk
            chunk_text = " ".join(current_sentences)
            effective_min = MIN_CHUNK_WORDS if min_chunk_words is None else min_chunk_words
            if len(chunk_text.split()) >= effective_min:
                chunks.append(chunk_text)

            # Build the overlap buffer: keep trailing sentences until ≥ overlap words
            overlap_sentences: list[str] = []
            overlap_words = 0
            for s in reversed(current_sentences):
                wc = len(s.split())
                if overlap_words + wc > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_words += wc

            current_sentences = overlap_sentences + [sentence]
            current_word_count = overlap_words + word_count
        else:
            current_sentences.append(sentence)
            current_word_count += word_count

    # Emit any remaining sentences
    if current_sentences:
        chunk_text = " ".join(current_sentences)
        effective_min = MIN_CHUNK_WORDS if min_chunk_words is None else min_chunk_words
        if len(chunk_text.split()) >= effective_min:
            chunks.append(chunk_text)

    return chunks