"""
Tests for the AdalaRetriever implementation.
"""
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from Researcher.retrievers.adala import AdalaRetriever


class TestAdalaRetriever(unittest.TestCase):
    """Test cases for the Adala retriever."""

    def setUp(self):
        """Set up test environment."""
        # Mock the config to provide test values
        self.config_patch = patch('Researcher.retrievers.adala.config')
        self.mock_config = self.config_patch.start()
        self.mock_config.get.return_value = {
            'base_url': 'https://adala.justice.gov.ma',
            'build_id': 'THP5ZL1eNCinRAZ1hWfN0',
            'max_results': 5
        }

    def tearDown(self):
        """Clean up after tests."""
        self.config_patch.stop()

    def test_initialization(self):
        """Test that AdalaRetriever initializes correctly."""
        retriever = AdalaRetriever()
        self.assertEqual(retriever.name, "adala_retriever")
        self.assertEqual(retriever.base_url, "https://adala.justice.gov.ma")
        self.assertEqual(retriever.build_id, "THP5ZL1eNCinRAZ1hWfN0")
        self.assertEqual(retriever.max_results, 5)

    def test_name_property(self):
        """Test the name property returns the correct identifier."""
        retriever = AdalaRetriever()
        self.assertEqual(retriever.name, "adala_retriever")

    def test_tool_property(self):
        """Test that the tool property returns a Tool object."""
        retriever = AdalaRetriever()
        tool = retriever.tool
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "AdalaSearch")
        self.assertIn("Adala Justice", tool.description)

    @patch('Researcher.retrievers.adala.httpx.AsyncClient')
    def test_async_search_success(self, mock_async_client):
        """Test successful async search."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "pageProps": {
                "searchResult": {
                    "data": [
                        {
                            "title": "Test Law",
                            "type": "Law",
                            "law_type": "Civil",
                            "date": "2024-01-01",
                            "relative_path": "/documents/test.pdf"
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        # Setup async context manager mock
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        retriever = AdalaRetriever()
        
        # Run async search using asyncio.run()
        results = asyncio.run(retriever._async_search("test", 5))
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Law")

    @patch('Researcher.retrievers.adala.httpx.AsyncClient')
    def test_retrieve_with_results(self, mock_async_client):
        """Test retrieve method with successful results."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "pageProps": {
                "searchResult": {
                    "data": [
                        {
                            "title": "Test Law",
                            "type": "Law",
                            "law_type": "Civil",
                            "date": "2024-01-01",
                            "relative_path": "/documents/test.pdf"
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = MagicMock()

        # Setup async context manager mock
        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        retriever = AdalaRetriever()
        documents = retriever.retrieve("test query")

        self.assertEqual(len(documents), 1)
        self.assertIn("Test Law", documents[0].page_content)
        self.assertEqual(documents[0].metadata["title"], "Test Law")
        self.assertEqual(documents[0].metadata["retriever"], "adala_retriever")

    def test_retrieve_with_empty_results(self):
        """Test retrieve method with no results."""
        with patch('Researcher.retrievers.adala.httpx.AsyncClient') as mock_async_client:
            # Mock empty response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "pageProps": {
                    "searchResult": {
                        "data": []
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance

            retriever = AdalaRetriever()
            documents = retriever.retrieve("test query")

            self.assertEqual(len(documents), 0)


if __name__ == '__main__':
    unittest.main()
