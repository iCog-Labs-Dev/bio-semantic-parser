# from .services import fetch_gse_data, extract_pubmed_id, fetch_pubmed_article
from .services.gse_loader import fetch_gse_data
from .services.abstract_loader import extract_pubmed_id, fetch_pubmed_article
from .services.metadata_to_fol import generate_valid_predicates_from_gse as generate_valid_predicates_from_gse_metadata
from .services.abstract_to_fol import generate_valid_predicates_from_abstract as generate_valid_predicates_from_abstract


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

    # article = fetch_pubmed_article(pubmed_id)
    # return [article]
    article=  """
                An age-related decline in immune functions, referred to as immunosenescence, is partially responsible for the increased prevalence and severity of infectious diseases, and the low efficacy of vaccination in elderly persons. Immunosenescence is characterized by a decrease in cell-mediated immune function as well as by reduced humoral immune responses. Age-dependent defects in T- and B-cell function coexist with age-related changes within the innate immune system. In this review, we discuss the mechanisms and consequences of age-associated immune alterations as well as their implications for health in old age.
                """

    abstract_predicates = generate_valid_predicates_from_abstract(article)
    gse_predicates = generate_valid_predicates_from_gse_metadata(gse_data)
    
    predicates = {
    "abstract_predicates": abstract_predicates,
    "gse_metadata_predicates": gse_predicates
        }
    return predicates
