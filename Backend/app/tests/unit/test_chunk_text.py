from app.services.abstract_loader import chunk_text

def test_chunk_text_empty():
    text = ""

    chunks = chunk_text(text, max_tokens=5)
    expected_chunks = []
    assert chunks == expected_chunks


def test_chunk_text_basic_chunking():
    text = "This is a simple sentence to be split into chunks for testing."
    expected_chunks = [
        "This is a simple sentence",
        " to be split into chunks",
        " for testing."
    ]
    
    chunks = chunk_text(text, max_tokens = 5)
    assert chunks == expected_chunks