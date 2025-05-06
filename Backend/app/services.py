import requests
import re
from core.config import config
from typing import Union, Dict, Optional, List
import GEOparse
import json
from utils.openai_utils import openai_generate
from core.prompts import FOL_generation_prompt

NCBI_API_KEY = config.NCBI_API_KEY



def fetch_pmc_id(pmid, api_key):
    """Check if a given PubMed ID (PMID) has a corresponding PMC ID."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    params = {
        "dbfrom": "pubmed",
        "db": "pmc",
        "id": pmid,
        "retmode": "json",
        "api_key": api_key
    }
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        linksets = data.get("linksets", [])
        if linksets and "linksetdbs" in linksets[0]:
            for link in linksets[0]["linksetdbs"]:
                if link["dbto"] == "pmc":
                    return link["links"][0]  # Return first PMC ID found
    return None

def fetch_pmc_pdf(pmc_id):
    pdf_url = f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmc_id}/pdf/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }  # Replace with your actual User-Agent
    try:
        response = requests.get(pdf_url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PDF for PMC{pmc_id}: {e}")
        return None

def fetch_abstract(pmid, api_key):
    """Retrieve only the abstract of a PubMed article."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "text",
        "rettype": "medline",
        "api_key": api_key
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        text_data = response.text
        abstract_match = re.search(r"AB  - (.+)", text_data, re.DOTALL)
        if abstract_match:
            return abstract_match.group(1).strip()  # Extract abstract
        return "No abstract available."
    else:
        return f"Error: {response.status_code}, {response.text}"


def fetch_pubmed_article(pmid, api_key: Optional[str] = NCBI_API_KEY):
    """Check PMC for full-text availability, otherwise return the abstract."""
    pmc_id = fetch_pmc_id(pmid, api_key)
    
    if pmc_id:
        pdf_content = fetch_pmc_pdf(pmc_id)
        if pdf_content:
            print(f"Successfully fetched PDF for PMC ID: {pmc_id}")
            return pdf_content  # Return the PDF as binary data
    
    # If no full text is found, return abstract
    return fetch_abstract(pmid, api_key)



##### Test case for the above the methods

# pmid = "30092180"  # Example PubMed ID
# result = fetch_pubmed_article(pmid)
# if isinstance(result, bytes):
#     print("PDF downloaded successfully (binary data).")
# else:
#     print("Abstract:", result)


def fetch_gse_summary(gse_id: str, api_key: Optional[str] = NCBI_API_KEY) -> Union[str, Dict[str, str]]:
   
    if not gse_id or not isinstance(gse_id, str):
        return {"error": "invalid_input", "message": "GSE ID must be a non-empty string"}
        
    if not re.match(r'^GSE\d+$', gse_id):
        return {"error": "invalid_id", "message": f"Invalid GSE ID format: {gse_id}"}
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    headers = {"User-Agent": "GSE_Fetcher/1.0"}
    
    search_params = {
            "db": "gds",
            "term": f"{gse_id}[Accession]",
            "api_key": api_key,
            "retmode": "json"
        }
        
    search_response = requests.get(
            f"{base_url}esearch.fcgi",
            params=search_params,
            headers=headers,
            timeout=15
        )
    search_response.raise_for_status()
    search_data = search_response.json()
        
    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
            return {"error": "not_found", "message": f"{gse_id} not found in GEO database"}
            
    uid = id_list[0]

    summary_params = {
                "db": "gds",
                "id": uid,
                "retmode": "json",
                "api_key": api_key
            }
    summary_response = requests.get(
                f"{base_url}esummary.fcgi",
                params=summary_params,
                headers=headers,
                timeout=15
            )
    summary_response.raise_for_status()
    summary_data = summary_response.json()
    return summary_data                   

    
##### Test case for the above the method

# result = fetch_gse_summary("GSE12277")
# import json
# print(json.dumps(result, indent=2)) 



def fetch_gse_data(gse_id: str) -> Union[str, Dict[str, str]]:
    """
    Fetches a GSE entry from GEO database.
    
    Parameters:
    - gse_id: The GEO Series ID (e.g., "GSE12277").
    
    Returns:
    - A string containing the GSE entry in JSON format or a dictionary with error details.
    """
    try:
        # gse = GEOparse.get_GEO(geo=gse_id, destdir="../data", silent=True)
        gse = GEOparse.get_GEO(geo=gse_id, silent=True)  # No writing to disk
        if not gse:
            return {"error": "not_found", "message": f"{gse_id} not found in GEO database"}
        print("Successfully fetched GSE data.")
        return gse
    except Exception as e:
        print(f"Error fetching GSE {gse_id} with GEOparse: {e}")
        return None


# gse= fetch_gse_data("GSE12277")
# metadata = gse.metadata
# print(json.dumps(metadata, indent=2))

def extract_pubmed_id(gse_id: str, api_key: Optional[str] = NCBI_API_KEY) -> Optional[str]:
    """
    Extracts the PubMed ID associated with a given GSE ID using NCBI Entrez utilities.

    Args:
        gse_id (str): The GEO Series identifier (e.g., 'GSE12345').
        api_key (str): NCBI API key (optional, uses default from config).

    Returns:
        Optional[str]: The PubMed ID if found, else None.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    headers = {"User-Agent": "GSE_PubMed_Fetcher/1.0"}

    # Step 1: Search for the UID
    search_params = {
        "db": "gds",
        "term": f"{gse_id}[Accession]",
        "retmode": "json",
        "api_key": api_key
    }
    try:
        search_res = requests.get(f"{base_url}esearch.fcgi", params=search_params, headers=headers, timeout=15)
        search_res.raise_for_status()
        id_list = search_res.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            print(f"No GDS entry found for {gse_id}")
            return None
        uid = id_list[0]

        # Step 2: Get the summary to extract PubMed IDs
        summary_params = {
            "db": "gds",
            "id": uid,
            "retmode": "json",
            "api_key": api_key
        }
        summary_res = requests.get(f"{base_url}esummary.fcgi", params=summary_params, headers=headers, timeout=15)
        summary_res.raise_for_status()
        result = summary_res.json().get("result", {}).get(uid, {})
        pubmed_ids = result.get("pubmedids", [])
        return pubmed_ids[0] if pubmed_ids else None
    except Exception as e:
        print(f"Error extracting PubMed ID from GSE {gse_id}: {e}")
        return None


def annotate_with_medcat(text, medcat_url= config.MEDCAT_URL):
    """
    Sends text to the MedCAT API and returns the JSON response.
    """
    payload = {"content": {"text": text}}
    headers = {"Content-Type": "application/json"}

    response = requests.post(medcat_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

##### Test case for the above method
# annotated_text= annotate_with_medcat("Breast cancer is a type of cancer that forms in the cells of the breasts.")
# print(json.dumps(annotated_text, indent=2))


def parse_medcat_response(medcat_json):
    """
    Parses MedCAT's response JSON to keep only the required fields.

    Returns:
        dict: {
            "text": <original text>,
            "annotations": [ 
                {
                    "pretty_name": ...,
                    "cui": ...,
                    "types": [...],
                    "detected_name": ...
                },
                ...
            ]
        }
    """
    result = medcat_json.get("result", {})
    raw_annotations = result.get("annotations", [])
    text = result.get("text", "")

    filtered_annotations = []

    if raw_annotations and isinstance(raw_annotations[0], dict):
        for _, annotation in raw_annotations[0].items():
            filtered = {
                "pretty_name": annotation.get("pretty_name"),
                "detected_name": annotation.get("detected_name"),
                "cui": annotation.get("cui"),
                "types": annotation.get("types", []),
                
            }
            filtered_annotations.append(filtered)

    return {
        "text": text,
        "annotations": filtered_annotations
    }

##### test case for the above method
# text = "The patient was diagnosed with cancer."
# json_response = annotate_with_medcat(text)
# cleaned = parse_medcat_response(json_response)
# print(json.dumps(cleaned, indent=2))


def generate_triples_from_concepts(parsed_medcat_response, prompt):
    """
    Generate First-Order Logic (FOL) relationships from annotated MedCAT concepts using an LLM.

    Args:
        parsed_medcat_response (list of dict): List of parsed concept dictionaries.
        prompt (str): Prompt with a placeholder for concept list (e.g., {concepts}).

    Returns:
        str: LLM-generated FOL output.
    """

    annotations = parsed_medcat_response.get("annotations", [])

    text= parsed_medcat_response.get("text")
    concepts_str = "\n".join([
        f"- Concept: {c['pretty_name']} (Type: {', '.join(c['types'])}, Mentioned as: \"{c['detected_name']}\")"
        for c in annotations
    ])

    # Debugging print statements to see the values being passed
    print("Concepts String:")
    print(concepts_str)
    print("Text:")
    print(text)


    filled_prompt = prompt.format(concepts= concepts_str, texts=text)

    print("Filled Prompt:")
    print(filled_prompt)

    messages = [
        {'role': 'system', 'content': """
            You are an AI expert specialized in knowledge graph extraction. 
Your task is to identify and extract factual Subject-Predicate-Object (SPO) triples from the given text and its annotation.
Focus on accuracy and adhere strictly to the JSON output format requested in the user prompt.
Extract core entities and the most direct relationship.
"""},
        {'role': 'user', 'content': filled_prompt}
    ]

    response = openai_generate(messages=messages)
    return response.choices[0].message.content.strip()


###### Test case for the above method

# text = """
# An age-related decline in immune functions, referred to as immunosenescence, is partially responsible for the increased prevalence and severity of infectious diseases, and the low efficacy of vaccination in elderly persons. Immunosenescence is characterized by a decrease in cell-mediated immune function as well as by reduced humoral immune responses. Age-dependent defects in T- and B-cell function coexist with age-related changes within the innate immune system. In this review, we discuss the mechanisms and consequences of age-associated immune alterations as well as their implications for health in old age.
# """
# json_response = annotate_with_medcat(text)
# cleaned_reponse = parse_medcat_response(json_response)
# # print(json.dumps(cleaned_reponse, indent=2))
# triples_json = generate_triples_from_concepts(cleaned_reponse, FOL_generation_prompt)

# # Strip leading/trailing whitespace and backticks (including optional "json" label)
# triples_json = triples_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```")

# Show result
# print("Generated FOL:")
# print(triples_json)


def parse_triples_to_predicates(triples_json):
    """
    Converts a list of triples into predicate(subject, object) format.
    
    Args:
        triples_json (dict): A dictionary containing a "triples" key with a list of subject-predicate-object dictionaries.
    
    Returns:
        list: A list of strings in predicate(subject, object) format.
    """

   
    predicate_lines = []
    for triple in triples_json.get("triples", []):
        subject = triple["subject"]
        predicate = triple["predicate"]
        obj = triple["object"]

        # Ensure valid variable-like formatting (optional)
        subject_str = subject.replace(" ", "_")
        object_str = obj.replace(" ", "_")
        predicate_str = predicate.replace(" ", "_")

        predicate_lines.append(f"{predicate_str}({subject_str}, {object_str})")
    
    return predicate_lines

##### test case for the above method

# triples_output = json.loads(triples_json)  # run this after generating triples_json
# predicates = parse_triples_to_predicates(triples_output)
# print("\n\n Generated predicates: \n")
# print("\n".join(predicates))
