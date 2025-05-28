import streamlit as st
import requests
import time

st.title("Data Processing Pipeline")
gse_id = st.text_input("Enter GSE ID (e.g. GSE17833)")

PROGRESS_STEPS = [
    ("Processing GSE pipeline for ID", 10),
    ("Fetching GSE data...", 20),
    ("GSE data fetched successfully", 30),
    ("Extracting PubMed ID...", 40),
    ("PubMed ID extracted", 50),
    ("Fetching PubMed article...", 60),
    ("PubMed article fetched successfully", 70),
    ("Generating predicates from GSE metadata", 80),
    ("Predicates from abstract generated successfully", 90),
    ("Predicates from GSE metadata generated successfully", 95),
    ("Combining predicates", 100)
]

def process_gse(gse_id):
    """Process GSE ID and display actual results"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    result_container = st.empty()
    
    try:
        for step, progress in PROGRESS_STEPS:
            progress_bar.progress(progress)
            status_text.info(step)
            time.sleep(0.3)
            
        response = requests.post(
            "http://localhost:8000/process",
            json={"query": gse_id},
            timeout=60
        )
        
        progress_bar.progress(100)
        
        if response.status_code == 200:
            response_data = response.json()
            
            if isinstance(response_data, dict):
                response_data.pop("result", None)
                response_data.pop("status", None)
                
                if response_data:  
                    status_text.success("Processing complete! Here are the results:")
                    result_container.json(response_data)
                else:
                    status_text.success("Processing complete")
                    result_container.info("No additional data returned from backend")
            else:
                status_text.success("Processing complete")
                result_container.json(response_data)
                
        else:
            status_text.error("Processing failed")
            try:
                error_data = response.json()
                result_container.error(error_data)
            except:
                result_container.error(f"Error {response.status_code}: {response.text}")
                
    except Exception as e:
        progress_bar.progress(100)
        status_text.error("Processing failed")
        result_container.error(f"Error: {str(e)}")

if st.button("Submit"):
    if gse_id:
        process_gse(gse_id)
    else:
        st.warning("Please enter a valid GSE ID")