import pytest
from fastapi.testclient import TestClient
from app.main import app  # Ensure this imports the FastAPI app instance

client = TestClient(app)

KNOWN_GSE_ID = "GSE12272"

@pytest.mark.integration
def test_pipeline_endpoint_returns_valid_predicates():
    response = client.get(f"/pipeline/{KNOWN_GSE_ID}")
    
    assert response.status_code == 200, "Pipeline endpoint did not return 200"
    
    json_response = response.json()
    assert "result" in json_response, "No 'result' key in response"

    predicates = json_response["result"]
    assert isinstance(predicates, str), "Predicates should be returned as a string"
    assert len(predicates) > 10, "Result string too short, may indicate failure"

    print("Returned predicates:\n", predicates)
