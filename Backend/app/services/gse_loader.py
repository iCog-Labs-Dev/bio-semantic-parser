import GEOparse
from typing import Union, Dict, Optional, List

def fetch_gse_data(gse_id: str) -> Union[str, Dict[str, str]]:
    """
    Fetches a GSE entry from GEO database.
    
    Parameters:
    - gse_id: The GEO Series ID (e.g., "GSE12277").
    
    Returns:
    - The GSE file as a GEOparse GSE object or a dictionary with error details.
    """
    try:               
        gse = GEOparse.get_GEO(geo=gse_id, destdir="./data", silent=True)

        if not gse:
            return {"error": "not_found", "message": f"{gse_id} not found in GEO database"}
        return gse
    except Exception as e:
        print(f"Error fetching GSE {gse_id} with GEOparse: {e}")
        return None

def load_gse_data(gse_id: str) -> Union[str, Dict[str, str]]:
    """
    Loads GSE data from a local file.

    Parameters:
    - gse_id: The GEO Series ID (e.g., "GSE12277").

    Returns:
    - The GSE file as a GEOparse GSE object or a dictionary with error details.
    """
    gse = GEOparse.get_GEO(filepath=f"./data/{gse_id}_family.soft.gz")
    if not gse:
        return {"error": "not_found", "message": f"{gse_id} not found in local files"}
    return gse
  
