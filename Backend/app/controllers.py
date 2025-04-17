from services import fetch_gse_data, extract_pubmed_id, fetch_pubmed_article


def process_gse_pipeline(gse_id: str) -> list:
    """
    Orchestrates the GSE to predicate pipeline.
    
    Args:
        gse_id (str): GEO Series identifier (e.g., 'GSE12345').

    Returns:
        list: A list of predicates generated from the GSE and PubMed article.
    """