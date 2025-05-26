# from .services import fetch_gse_data, extract_pubmed_id, fetch_pubmed_article
from .services.gse_loader import fetch_gse_data
from .services.abstract_loader import extract_pubmed_id, fetch_pubmed_article, fetch_abstract, chunk_text, clean_abstract_text
from .services.metadata_to_fol import generate_valid_predicates_from_gse as generate_valid_predicates_from_gse_metadata
from .services.abstract_to_fol import generate_valid_predicates_from_abstract as generate_valid_predicates_from_abstract
import logging

logging.basicConfig(level=logging.INFO)

def process_gse_pipeline(gse_id: str) -> list:
    """
    Orchestrates the GSE to predicate pipeline.
    
    Args:
        gse_id (str): GEO Series identifier (e.g., 'GSE12345').

    Returns:
        list: A list of predicates generated from the GSE and PubMed article.
    """

    logging.info(f"Processing GSE pipeline for ID: {gse_id}")
    logging.info("Fetching GSE data...")
    gse_data = fetch_gse_data(gse_id)
    if not gse_data:
        return ["Failed to fetch GSE data"]
    logging.info("GSE data fetched successfully.")
    logging.info("Extracting PubMed ID...")
    pubmed_id = extract_pubmed_id(gse_id)
    if not pubmed_id:
        return ["No PubMed ID found for this GSE"]
    logging.info(f"PubMed ID extracted: {pubmed_id}")
    logging.info("Fetching PubMed article...")
    # article = fetch_pubmed_article(pubmed_id)
    # if not article:
    #     return ["Failed to fetch PubMed article"]
    
    # article=  """
    #             An age-related decline in immune functions, referred to as immunosenescence, is partially responsible for the increased prevalence and severity of infectious diseases, and the low efficacy of vaccination in elderly persons. Immunosenescence is characterized by a decrease in cell-mediated immune function as well as by reduced humoral immune responses. Age-dependent defects in T- and B-cell function coexist with age-related changes within the innate immune system. In this review, we discuss the mechanisms and consequences of age-associated immune alterations as well as their implications for health in old age.
    #             """

    article = fetch_abstract(pubmed_id)
    if not article:
        return ["Failed to fetch PubMed article"]
    # return article
    logging.info("PubMed article fetched successfully.")

    cleanned_article = clean_abstract_text(article)
    logging.info("chunking abstract...")
    chunks= chunk_text(cleanned_article)
    if not chunks:
        return ["Failed to chunk the abstract"]
    logging.info("Abstract chunked successfully.")
    
    # logging.info("PubMed article fetched successfully.")
    logging.info("Generating predicates from abstract...")

    abstract_predicates = generate_valid_predicates_from_abstract(chunks)
    if not abstract_predicates:
        return ["Failed to generate predicates from abstract"]
    logging.info("Predicates from abstract generated successfully.")

    logging.info("Generating predicates from GSE metadata...")
    gse_predicates = generate_valid_predicates_from_gse_metadata(gse_data)
    if not gse_predicates:
        return ["Failed to generate predicates from GSE metadata"]
    logging.info("Predicates from GSE metadata generated successfully.")

    logging.info("Combining predicates...")
    result = {
    "abstract": article,
    "cleanned_abstract": cleanned_article,
    "abstract_predicates": abstract_predicates,
    "gse_metadata_predicates": gse_predicates
        }
    return result
