import unittest
from unittest.mock import patch, MagicMock
import json
import base64
import sys
import os

# Add src to path so we can import the ingestion module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/ingestion')))

import main

class TestIngestion(unittest.TestCase):

    @patch('main.requests.get')
    @patch('main.publisher')
    def test_fetch_and_publish_success(self, mock_publisher, mock_get):
        # 1. Setup Mock API Response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Global Quote": {
                "01. symbol": "IBM",
                "05. price": "150.00",
                "10. change percent": "-0.5%"
            }
        }
        mock_get.return_value = mock_response

        # 2. Setup Environment Variables
        os.environ['PROJECT_ID'] = 'test-project'
        os.environ['TOPIC_ID'] = 'stock-ticks-topic'
        os.environ['API_KEY'] = 'test-key'

        # 3. Call the Function
        # Cloud Functions (Gen 2) expects a Flask Request object
        mock_request = MagicMock()
        response = main.entry_point(mock_request)

        # 4. Assertions
        assert response == ("Data published.", 200)
        
        # Verify we tried to publish
        mock_publisher.publish.assert_called_once()
        
        # Verify the payload structure
        call_args = mock_publisher.publish.call_args
        published_data = json.loads(call_args[1]['data'].decode('utf-8'))
        
        assert published_data['symbol'] == 'IBM'
        assert published_data['price'] == 150.00
        assert 'timestamp' in published_data

if __name__ == '__main__':
    unittest.main()