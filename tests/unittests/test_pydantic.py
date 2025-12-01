from fastapi.testclient import TestClient
import multipart
from main import app # or wherever your app object is

client = TestClient(app)

def test_create_entry_wrong_types():
    """
    Test that sending a string for a boolean field fails.
    """
    bad_payload = {
        "title": "Bad Types",
        "content": "Testing...",
        "use_for_prompt_generation": "not-a-boolean" # Should be true/false
    }

    response = client.post("/journal/", json=bad_payload)
    
    assert response.status_code == 422
