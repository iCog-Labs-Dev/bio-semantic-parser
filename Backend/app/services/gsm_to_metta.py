from typing import Union, Dict
from app.core.prompts import column_name_prompt
from app.core.config import config
from app.utils.openai_utils import openai_generate
import json


def load_gsm_data(gse: object, gsm_id: str) -> Union[str, Dict[str, str]]:
    """
    Load GSM data from a GSE object.

    Parameters:
    - gse: The GEOparse GSE object.
    - gsm_id: The GSM ID (e.g., "GSM123456").

    Returns:
    - The GSM file as a GEOparse GSM object or a dictionary with error details.
    """
    gsm= gse.gsms[gsm_id ]
    if not gsm:
        return {"error": "not_found", "message": f"{gsm_id} not found in GSE {gse.id}"}
    data= gsm.table
    return data


def declare_instances(df, predicate_mapping):
    """Generate MeTTa instance declarations with relationships to uniqueId."""
    metta_instances = []
    
    for _, row in df.iterrows():
        unique_id = row["Unique_ID"]  # Unique identifier for this row

        for col in df.columns:
            if col in predicate_mapping:  # Ensure only mapped columns are used
                mapped_col = predicate_mapping[col]
                instance = row[col]        
                
                if mapped_col == "uniqueId":
                    continue
                # Define relationship with uniqueId
                metta_instances.append(f"({mapped_col} {unique_id} {instance})")    
    return metta_instances

def generate_metta_from_gsm(gsm_data: Union[str, Dict[str, str]], gsm_id: str) -> Dict[str, str]:
    """
    Generate MeTTa code from GSM data.

    Parameters:
    - gsm_data: The GSM data as a GEOparse GSM object or a dictionary with error details.

    Returns:
    - A dictionary containing the MeTTa code.
    """

    sample_data = gsm_data.sample(10)
    # Create a unique ID by combining row index and GSM ID
    sample_data.insert(0, "Unique_ID", sample_data.index.astype(str) + "_" + gsm_id)

    columns = list(sample_data.columns) # will be modified to be inn a camel case format
    print("Extracted Columns:", columns)

    prompt = column_name_prompt
    filled_prompt = prompt.format(columns=columns)

    messages =[
    {'role':'system', 'content':"You are an expert in data standardization."},
    {'role':'user', 'content':filled_prompt}
    ]
    response = openai_generate(messages=messages)
    predicate_mapping = response.choices[0].message.content.strip()
    predicate_mapping = json.loads(predicate_mapping)

    instances= declare_instances(sample_data, predicate_mapping)

   
    return instances
