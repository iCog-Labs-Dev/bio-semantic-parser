# from .services import fetch_gse_data, extract_pubmed_id, fetch_pubmed_article
from .services.gse_loader import fetch_gse_data, load_gse_data
from .services.abstract_loader import extract_pubmed_id, fetch_pubmed_article, fetch_abstract, chunk_text, clean_abstract_text
from .services.metadata_to_fol import generate_valid_predicates_from_gse as generate_valid_predicates_from_gse_metadata
from .services.abstract_to_fol import generate_valid_predicates_from_abstract as generate_valid_predicates_from_abstract
from .services.fol_to_metta import convert_all_to_metta, validate_metta_lines, split_predicates
from .services.gsm_to_metta import generate_metta_from_gsm, load_gsm_data
import logging
import json
import GEOparse

logging.basicConfig(level=logging.INFO)

def send_or_log(message, send_progress):
    if send_progress:
        send_progress(message)
    else:
        logging.info(message)

def process_gse_pipeline(gse_id: str, send_progress) -> list:
    """
    Orchestrates the GSE to predicate pipeline.
    
    Args:
        gse_id (str): GEO Series identifier (e.g., 'GSE12345').

    Returns:
        list: A list of predicates generated from the GSE and PubMed article.
    """

    send_or_log("Fetching GSE data...", send_progress)
 
    gse_data = fetch_gse_data(gse_id)
    if not gse_data:
        return ["Failed to fetch GSE data"]
    logging.info("GSE data fetched successfully.")

    gsms= gse_data.gsms
    if not gsms:
        logging.info("No GSMs found in GSE data")
    # gsms_result = {"gsms": list(gsms.keys())}
    gsms_result = {
    "gsms": {
        "gse_id": gse_id,
        "gsm_ids": list(gsms.keys())
             }
        }
    send_or_log(json.dumps(gsms_result, ensure_ascii=False), send_progress)

    send_or_log("Extracting PubMed ID...", send_progress)
    pubmed_id = extract_pubmed_id(gse_id)
    if not pubmed_id:
        return ["No PubMed ID found for this GSE"]
    logging.info(f"PubMed ID extracted: {pubmed_id}")
    send_or_log("Fetching PubMed article...", send_progress)

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
    abstract_result = {"abstract": article}
    send_or_log(json.dumps(abstract_result, ensure_ascii=False), send_progress)


    send_or_log("chunking abstract...", send_progress)
    chunks= chunk_text(cleanned_article)
    if not chunks:
        return ["Failed to chunk the abstract"]
    logging.info("Abstract chunked successfully.")
    
    # logging.info("PubMed article fetched successfully.")
    send_or_log("Generating predicates from abstract...", send_progress)

    # if send_progress:
    #     send_progress("Generating predicates from abstract...")
    send_or_log("Generating predicates from abstract...", send_progress)

    abstract_predicates = generate_valid_predicates_from_abstract(chunks)
    if not abstract_predicates:
        return ["Failed to generate predicates from abstract"]
    logging.info("Predicates from abstract generated successfully.")
    abstract_predicates_result = {"abstract_predicates": abstract_predicates}
    send_or_log(json.dumps(abstract_predicates_result, ensure_ascii=False), send_progress)

    send_or_log("Generating predicates from GSE metadata...", send_progress)
    gse_predicates = generate_valid_predicates_from_gse_metadata(gse_data)
    if not gse_predicates:
        return ["Failed to generate predicates from GSE metadata"]
    logging.info("Predicates from GSE metadata generated successfully.")

    gse_predicates_result = {"gse_metadata_predicates": gse_predicates}
    send_or_log(json.dumps(gse_predicates_result,ensure_ascii=False), send_progress)
    # send_or_log("Combining predicates...", send_progress)

    result = {
    "abstract": article,
    "cleanned_abstract": cleanned_article,
    "abstract_predicates": abstract_predicates,
    "gse_metadata_predicates": gse_predicates
        }
    
    send_or_log("Done ", send_progress)
    return result

def convert_fol_string_to_metta(text_block: str) -> dict:
    """
    Convert FOL-like multi-line string to MeTTa format.
    """
    # predicates = [line.strip() for line in text_block.strip().splitlines() if line.strip()]
    predicates = split_predicates(text_block)
    metta_lines = convert_all_to_metta(predicates)
    valid_lines = validate_metta_lines(metta_lines)
    invalid_lines = [line for line in metta_lines if line not in valid_lines]

    return {
        "metta_valid": valid_lines,
        "metta_invalid": invalid_lines,
        "original_predicates": predicates
    }
def get_gsm_data(gse_id: str, gsm_id: str) -> dict:

    gse= load_gse_data(gse_id)
    data= load_gsm_data(gse, gsm_id)

    return data.head(15)

def gsm_to_metta(gse_id: str, gsm_id: str) -> dict:
    
    gse= load_gse_data(gse_id)
    data= load_gsm_data(gse, gsm_id)
    metta = generate_metta_from_gsm(data, gsm_id)
    result_instances = {
        "table_metta": metta
    }

    return result_instances