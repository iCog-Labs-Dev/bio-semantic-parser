import GEOparse
import pprint
from utils.openai_utils import openai_generate
import re
from core.prompts import predicate_instruction
from core.prompts import refinement_prompt
from core.aspects import annotation_aspects_list



gse= GEOparse.get_GEO(geo="GSE17833")
# Ensure gse_ is a GSE object
gse = gse if isinstance(gse, GEOparse.GEOTypes.GSE) else None
# print("GSE object:", gse_)

import re

def format_metadata(gse, gsm):
    gse_fields = ['summary', 'overall_design', 'type']
    gsm_fields = [
        'source_name_ch1', 'organism_ch1', 'characteristics_ch1',
        'treatment_protocol_ch1', 'molecule_ch1', 'extract_protocol_ch1',
        'label_ch1', 'label_protocol_ch1', 'hyb_protocol_ch1', 
        'scan_protocol', 'data_processing'
    ]

    metadata_str = []

    for field in gse_fields:
        value = gse.metadata.get(field, ['N/A'])[0]
        metadata_str.append(f"GSE {field.replace('_', ' ').title()}: {value}")

    for field in gsm_fields:
        value = gsm.metadata.get(field, ['N/A'])[0]
        metadata_str.append(f"GSM {field.replace('_', ' ').title()}: {value}")

    return "\n".join(metadata_str)


def get_all_metadata_samples(gse):
    field_values = set()
    for gsm in gse.gsms.values():
        field_values.add(format_metadata(gse, gsm))
    return list(field_values)


def extract_predicates_for_aspect(aspect, field_values):
    aspect_details = annotation_aspects_list[aspect]
    irrelevant_aspects = [x for x in annotation_aspects_list if x != aspect]

    input_samples_combined = "List of examples to extract predicates from:\n" + "\n\n\n".join(field_values)

    resp = openai_generate([
        {
            "role": 'system',
            'content': predicate_instruction.format(
                aspect=aspect,
                aspect_details=aspect_details,
                irrelevant_aspects_combined='\n'.join(irrelevant_aspects)
            )
        },
        {
            'role': 'user',
            'content': input_samples_combined
        }
    ])
    
    combined_predicates = "Draft predicate lists:\n" + resp.choices[0].message.content

    refined_resp = openai_generate([
        {
            "role": 'system',
            'content': refinement_prompt.format(
                aspect=aspect,
                aspect_details=aspect_details,
                metadata=input_samples_combined,
                irrelevant_aspects_combined='\n'.join(irrelevant_aspects)
            )
        },
        {
            'role': 'user',
            'content': combined_predicates
        }
    ])

    return refined_resp.choices[0].message.content


def extract_all_predicates(gse):
    field_values = get_all_metadata_samples(gse)
    all_predicates = {}

    for aspect in annotation_aspects_list:
        predicates = extract_predicates_for_aspect(aspect, field_values)
        all_predicates[aspect] = predicates

    return all_predicates


def is_valid_predicate_line(line):
    allowed_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*\([a-zA-Z0-9_]+\)$'
    disallowed_chars = r'[\[\]{};:,.<>!?@#$%^&*=+"\'\\|`~]'
    line = line.strip()

    return bool(re.match(allowed_pattern, line)) and not re.search(disallowed_chars, line)


def extract_valid_predicates(all_predicates_dict):
    valid_predicates = []
    for text in all_predicates_dict.values():
        lines = text.splitlines()
        cleaned = [line for line in lines if is_valid_predicate_line(line)]
        valid_predicates.extend(cleaned)
    return valid_predicates


def generate_valid_predicates_from_gse(gse):
    all_predicates = extract_all_predicates(gse)
    valid_predicates = extract_valid_predicates(all_predicates)
    return valid_predicates



valid_predicates = generate_valid_predicates_from_gse(gse)

print("Valid predicates extracted:")
for predicate in valid_predicates:
    print(predicate)