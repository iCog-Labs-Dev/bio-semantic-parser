import pytest
from app.services.gse_loader import fetch_gse_data
from app.services.abstract_loader import extract_pubmed_id, fetch_abstract
import warnings
import pandas as pd

# Replace with a known valid GSE ID with linked PubMed ID
KNOWN_GSE_ID = "GSE12277"

@pytest.mark.integration
def test_fetch_gse_data():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=pd.errors.DtypeWarning)
        gse = fetch_gse_data("GSE12277")
        assert gse is not None
@pytest.mark.integration
def test_extract_pubmed_id():
    pubmed_id = extract_pubmed_id(KNOWN_GSE_ID)
    assert pubmed_id is not None, "PubMed ID not found"
    assert pubmed_id.isdigit(), "PubMed ID is not numeric"

@pytest.mark.integration
def test_fetch_abstract():
    pubmed_id = extract_pubmed_id(KNOWN_GSE_ID)
    if pubmed_id:
        abstract = fetch_abstract(pubmed_id)
        assert isinstance(abstract, str), "Abstract is not a string"
        assert "Error" not in abstract, "Failed to fetch abstract"
        assert len(abstract) > 20, "Abstract too short, likely invalid"

