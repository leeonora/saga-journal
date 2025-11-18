import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

class DBTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('main.client.chat.completions.create')
    def test_use_for_prompt_generation(self, mock_create):
        # 1. Define dummy entries
        entry1 = {"id": "1", "title": "Test 1", "content": "Content 1", "use_for_prompt_generation": True, "date": "2025-11-17T12:00:00"}
        entry2 = {"id": "2", "title": "Test 2", "content": "Content 2", "use_for_prompt_generation": False, "date": "2025-11-17T12:00:00"}
        entry3 = {"id": "3", "title": "Test 3", "content": "Content 3", "use_for_prompt_generation": True, "date": "2025-11-17T12:00:00"}
        
        # Mock the response from the OpenAI API
        mock_create.return_value.choices[0].message.content = "Test prompt"

        # 2. Call the /generate-prompt endpoint
        response = self.client.post("/generate-prompt", json={
            "promptType": "daily",
            "recentEntries": [entry1, entry2, entry3]
        })

        # 3. Assert that the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["prompt"], "Test prompt")

        # 4. Assert that the OpenAI API was called with the correct messages
        mock_create.assert_called_once()
        messages = mock_create.call_args[1]['messages']
        user_message = messages[1]['content']

        # Check that the content of the used entries is present
        self.assertIn("Content 1", user_message)
        self.assertIn("Content 3", user_message)

        # Check that the content of the unused entry is NOT present
        self.assertNotIn("Content 2", user_message)


if __name__ == '__main__':
    unittest.main()
