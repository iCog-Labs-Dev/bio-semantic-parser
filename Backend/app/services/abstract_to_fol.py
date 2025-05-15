import requests
import re
from app.core.config import config
# from typing import Union, Dict, Optional, List
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

# # Show result
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



def generate_valid_predicates_from_abstract(abstract):
    """
    Orchestrates the process of generating valid FOL predicates from a PubMed abstract.

    Args:
        abstract (str): abstract the article to process.

    Returns:
        list: List of FOL predicate strings.
    """
    
    # Step 1: Annotate with MedCAT
    medcat_json = annotate_with_medcat(abstract)

    # Step 2: Parse MedCAT response
    parsed_response = parse_medcat_response(medcat_json)

    # Step 3: Generate triples (FOL-like) from concepts via LLM
    triples_text = generate_triples_from_concepts(parsed_response, FOL_generation_prompt)

    # Step 4: Parse the LLM text output to JSON
    try:
        # Strip any backticks or code block indicators
        clean_text = triples_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        triples_json = json.loads(clean_text)
    except json.JSONDecodeError as e:
        print("Error parsing triples JSON:", e)
        print("Raw output was:", triples_text)
        return []

    # Step 5: Convert to predicates
    predicates = parse_triples_to_predicates(triples_json)

    return predicates
