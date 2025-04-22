from .services import fetch_gse_data, extract_pubmed_id, fetch_pubmed_article


def process_gse_pipeline(gse_id: str) -> list:
    """
    Orchestrates the GSE to predicate pipeline.
    
    Args:
        gse_id (str): GEO Series identifier (e.g., 'GSE12345').

    Returns:
        list: A list of predicates generated from the GSE and PubMed article.
    """

    gse_data = fetch_gse_data(gse_id)
    if not gse_data:
        return ["Failed to fetch GSE data"]

    pubmed_id = extract_pubmed_id(gse_id)
    if not pubmed_id:
        return ["No PubMed ID found for this GSE"]

    article = fetch_pubmed_article(pubmed_id)
    return [article]
