import requests
import re
from app.core.config import config
import json
from app.utils.openai_utils import openai_generate
from app.core.prompts import FOL_generation_prompt 


def annotate_with_medcat(text, medcat_url= config.MEDCAT_URL):
    """
    Sends text to the MedCAT API and returns the JSON response.
    """
    payload = {"content": {"text": text}}
    headers = {"Content-Type": "application/json"}

    response = requests.post(medcat_url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

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

    filled_prompt = prompt.format(concepts= concepts_str, texts=text)
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



def parse_triples_to_predicates(triples_json):
    """
    Converts a list of triples into predicate(subject, object) format.
    
    Args:
        triples_json (dict): A dictionary containing a "triples" key with a list of subject-predicate-object dictionaries.
    
    Returns:
        list: A list of strings in predicate(subject, object) format.
    """

    predicate_lines = []

    if isinstance(triples_json, dict):
        triples = triples_json.get("triples", [])
    elif isinstance(triples_json, list):
        triples = triples_json
    else:
        print("Unexpected format for triples_json:", type(triples_json))
        triples = []

    for triple in triples:
        subject = triple["subject"]
        predicate = triple["predicate"]
        obj = triple["object"]
        line = f"{predicate}({subject}, {obj})"
        predicate_lines.append(line)
    
    return predicate_lines


def generate_valid_predicates_from_abstract(chunks):
    """
    Orchestrates the process of generating valid FOL predicates from a list of abstract chunks.

    Args:
        chunks (list of str): List of text chunks from the abstract.

    Returns:
        list: Combined list of FOL predicate strings from all chunks.
    """
    all_predicates = []

    for chunk in chunks:
        # Step 1: Annotate with MedCAT
        medcat_json = annotate_with_medcat(chunk)

        # Step 2: Parse MedCAT response
        parsed_response = parse_medcat_response(medcat_json)

        # Step 3: Generate triples (FOL-like) from concepts via LLM
        triples_text = generate_triples_from_concepts(parsed_response, FOL_generation_prompt)

        # Step 4: Parse the LLM text output to JSON
        try:
            clean_text = triples_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
            triples_json = json.loads(clean_text)
        except json.JSONDecodeError as e:
            print(f"[Chunk Error] JSON parsing failed: {e}")
            print("Raw output:", triples_text)
            continue  # Skip this chunk

        # Step 5: Convert to predicates
        predicates = parse_triples_to_predicates(triples_json)
        all_predicates.extend(predicates)

    return all_predicates

