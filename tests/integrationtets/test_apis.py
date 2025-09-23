import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'saga-backend'))

from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
import uuid

# Run by: pytest tests/integrationtets/test_apis.py

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Journal API"}

@patch('main.client.chat.completions.create')
def test_add_and_get_entry(mock_create):
    # Mock the OpenAI API call
    mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="This is a test summary."))])

    # Test adding an entry
    entry_data = {"title": "Test Title", "content": "Test Content"}
    response = client.post("/journal/", json=entry_data)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["message"] == "Entry added with summary"
    assert response_json["entry"]["title"] == "Test Title"
    assert response_json["entry"]["summary"] == "This is a test summary."
    entry_id = response_json["entry"]["id"]

    # Test getting all entries
    response = client.get("/journal/")
    assert response.status_code == 200
    assert any(entry['id'] == entry_id for entry in response.json()["entries"])

@patch('main.client.chat.completions.create')
def test_update_entry(mock_create):
    # First, create an entry to update
    mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="Initial summary."))])
    entry_data = {"title": "Initial Title", "content": "Initial Content"}
    response = client.post("/journal/", json=entry_data)
    entry_id = response.json()["entry"]["id"]

    # Now, update the entry
    mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="Updated summary."))])
    updated_data = {"title": "Updated Title", "content": "Updated Content"}
    response = client.put(f"/journal/{entry_id}", json=updated_data)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["entry"]["title"] == "Updated Title"
    assert response_json["entry"]["summary"] == "Updated summary."

def test_delete_entry():
    # First, create an entry to delete
    with patch('main.client.chat.completions.create') as mock_create:
        mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="To be deleted."))])
        entry_data = {"title": "To Delete", "content": "Delete me"}
        response = client.post("/journal/", json=entry_data)
        entry_id = response.json()["entry"]["id"]

    # Delete the entry
    response = client.delete(f"/journal/{entry_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Entry with id {entry_id} deleted successfully"}

    # Verify it's gone
    response = client.get(f"/journal/{entry_id}")
    # The GET /journal/{entry_id} endpoint doesn't exist, so we check the list
    response = client.get("/journal/")
    assert not any(entry['id'] == entry_id for entry in response.json()["entries"])


def test_update_nonexistent_entry():
    fake_id = str(uuid.uuid4())
    updated_data = {"title": "Updated Title", "content": "Updated Content"}
    response = client.put(f"/journal/{fake_id}", json=updated_data)
    assert response.status_code == 404

def test_delete_nonexistent_entry():
    fake_id = str(uuid.uuid4())
    response = client.delete(f"/journal/{fake_id}")
    assert response.status_code == 404

@patch('main.client.chat.completions.create')
def test_generate_prompt(mock_create):
    mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="This is a test prompt."))])
    request_data = {"promptType": "daily", "recentEntries": ""}
    response = client.post("/generate-prompt", json=request_data)
    assert response.status_code == 200
    assert response.json() == {"prompt": "This is a test prompt."}