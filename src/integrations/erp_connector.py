"""
ERP System Connector
Integrates with Enterprise Resource Planning systems
"""

import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .base_connector import BaseConnector

logger = logging.getLogger(__name__)


class ERPConnector(BaseConnector):
    """Connector for ERP system integration"""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 5
    ):
        """
        Initialize ERP connector
        
        Args:
            base_url: ERP API base URL
            api_key: API authentication key
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, api_key, timeout)
        
    def get_work_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get work order details
        
        Args:
            order_id: Work order identifier
            
        Returns:
            Work order data
        """
        endpoint = f"/api/v1/work-orders/{order_id}"
        
        try:
            response = self._make_request("GET", endpoint)
            logger.info(f"Retrieved work order {order_id}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to get work order {order_id}: {e}")
            raise
    
    def get_next_work_order(self, worker_id: str) -> Dict[str, Any]:
        """
        Get next assigned work order for worker
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            Next work order data
        """
        endpoint = "/api/v1/work-orders/next"
        params = {"worker_id": worker_id, "status": "pending"}
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            
            if response.get("data"):
                logger.info(f"Next work order for {worker_id}: {response['data'].get('id')}")
            else:
                logger.info(f"No pending work orders for {worker_id}")
            
            return response
        
        except Exception as e:
            logger.error(f"Failed to get next work order: {e}")
            raise
    
    def update_work_order_status(
        self,
        order_id: str,
        status: str,
        worker_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update work order status
        
        Args:
            order_id: Work order identifier
            status: New status (pending, in_progress, completed, cancelled)
            worker_id: Worker identifier
            notes: Optional notes
            
        Returns:
            Updated work order data
        """
        endpoint = f"/api/v1/work-orders/{order_id}/status"
        
        payload = {
            "status": status,
            "worker_id": worker_id,
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        }
        
        try:
            response = self._make_request("PUT", endpoint, data=payload)
            logger.info(f"Updated work order {order_id} to {status}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to update work order status: {e}")
            raise
    
    def get_worker_tasks(
        self,
        worker_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks assigned to worker
        
        Args:
            worker_id: Worker identifier
            status: Filter by status (optional)
            
        Returns:
            List of tasks
        """
        endpoint = "/api/v1/tasks"
        params = {"worker_id": worker_id}
        
        if status:
            params["status"] = status
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            tasks = response.get("data", [])
            logger.info(f"Retrieved {len(tasks)} tasks for {worker_id}")
            return tasks
        
        except Exception as e:
            logger.error(f"Failed to get worker tasks: {e}")
            raise
    
    def create_incident_report(
        self,
        worker_id: str,
        incident_type: str,
        description: str,
        severity: str = "medium",
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create incident report
        
        Args:
            worker_id: Reporter identifier
            incident_type: Type of incident
            description: Incident description
            severity: Severity level (low, medium, high, critical)
            location: Incident location
            
        Returns:
            Created incident data
        """
        endpoint = "/api/v1/incidents"
        
        payload = {
            "worker_id": worker_id,
            "type": incident_type,
            "description": description,
            "severity": severity,
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "source": "voice_assistant"
        }
        
        try:
            response = self._make_request("POST", endpoint, data=payload)
            incident_id = response.get("data", {}).get("id")
            logger.info(f"Created incident report {incident_id}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to create incident report: {e}")
            raise
    
    def get_equipment_manual(self, equipment_id: str) -> Dict[str, Any]:
        """
        Get equipment manual/documentation
        
        Args:
            equipment_id: Equipment identifier
            
        Returns:
            Equipment documentation
        """
        endpoint = f"/api/v1/equipment/{equipment_id}/manual"
        
        try:
            response = self._make_request("GET", endpoint)
            logger.info(f"Retrieved manual for equipment {equipment_id}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to get equipment manual: {e}")
            raise
    
    def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for help articles
        
        Args:
            query: Search query
            category: Filter by category
            
        Returns:
            List of matching articles
        """
        endpoint = "/api/v1/knowledge-base/search"
        params = {"q": query}
        
        if category:
            params["category"] = category
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            results = response.get("data", [])
            logger.info(f"Found {len(results)} knowledge base articles")
            return results
        
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            raise


if __name__ == "__main__":
    # Test ERP connector (with mock server)
    erp = ERPConnector(
        base_url="https://api.example-erp.com",
        api_key="test-key"
    )
    
    print("ERP Connector initialized")
    print(f"Base URL: {erp.base_url}")
