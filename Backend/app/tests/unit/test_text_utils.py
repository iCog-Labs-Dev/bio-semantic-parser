from app.services.abstract_loader import clean_abstract_text

def test_clean_abstract_text_removes_metadata_and_whitespace():
    raw_text = (
        "FAU - Doe, John\n"
        "AU - Smith, Jane\n"
        "This is the actual abstract.\n\n"
        "It contains multiple lines,\n     and some    excessive spaces.\n"
        "AD - Some affiliation here\n"
    )

    expected_cleaned = "This is the actual abstract. It contains multiple lines, and some excessive spaces."

    result = clean_abstract_text(raw_text)
    assert result == expected_cleaned

def test_clean_abstract_text_empty_input():
    raw_text = ""
    expected_cleaned = ""
    
    result = clean_abstract_text(raw_text)
    assert result == expected_cleaned