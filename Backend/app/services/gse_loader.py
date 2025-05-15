import GEOparse
from typing import Union, Dict, Optional, List

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



# gse= GEOparse.get_GEO(geo="GSE17833")
# Ensure gse_ is a GSE object
# gse = gse if isinstance(gse, GEOparse.GEOTypes.GSE) else None
# print("GSE object:", gse_)
