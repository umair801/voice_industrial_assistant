"""
Base Connector Class
Common functionality for system integrations
"""

import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseConnector:
    """Base class for system connectors"""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 5
    ):
        """
        Initialize base connector
        
        Args:
            base_url: API base URL
            api_key: API authentication key
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Headers for all requests
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "VoiceIndustrialAssistant/1.0"
        }
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        logger.info(f"Initialized connector for {base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"{method} {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {url}")
            raise Exception(f"API request timeout after {self.timeout}s")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code}: {e}")
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"API request failed: {str(e)}")
    
    def health_check(self) -> bool:
        """
        Check if API is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self._make_request("GET", "/health")
            return response.get("status") == "ok"
        
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def close(self):
        """Close session"""
        self.session.close()
        logger.info("Connector session closed")


if __name__ == "__main__":
    # Test base connector
    connector = BaseConnector(
        base_url="https://api.example.com",
        api_key="test-key"
    )
    
    print("Base Connector initialized")
