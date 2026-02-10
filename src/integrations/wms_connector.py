"""
Warehouse Management System Connector
Integrates with WMS for inventory operations
"""

import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .base_connector import BaseConnector

logger = logging.getLogger(__name__)


class WMSConnector(BaseConnector):
    """Connector for Warehouse Management System"""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 5
    ):
        """
        Initialize WMS connector
        
        Args:
            base_url: WMS API base URL
            api_key: API authentication key
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, api_key, timeout)
    
    def get_inventory(
        self,
        sku: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get inventory details for SKU
        
        Args:
            sku: Stock keeping unit identifier
            location: Specific location (optional)
            
        Returns:
            Inventory data
        """
        endpoint = f"/api/v1/inventory/{sku}"
        params = {}
        
        if location:
            params["location"] = location
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            logger.info(f"Retrieved inventory for {sku}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to get inventory for {sku}: {e}")
            raise
    
    def update_inventory(
        self,
        sku: str,
        quantity: int,
        location: str,
        operation: str = "add",
        reason: Optional[str] = None,
        worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update inventory quantity
        
        Args:
            sku: Stock keeping unit
            quantity: Quantity to add/remove
            location: Warehouse location
            operation: Operation type (add, remove, adjust)
            reason: Reason for update
            worker_id: Worker performing update
            
        Returns:
            Updated inventory data
        """
        endpoint = "/api/v1/inventory/update"
        
        payload = {
            "sku": sku,
            "quantity": quantity,
            "location": location,
            "operation": operation,
            "reason": reason,
            "worker_id": worker_id,
            "timestamp": datetime.now().isoformat(),
            "source": "voice_assistant"
        }
        
        try:
            response = self._make_request("POST", endpoint, data=payload)
            logger.info(f"Updated inventory: {operation} {quantity} units of {sku} at {location}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to update inventory: {e}")
            raise
    
    def find_location(
        self,
        sku: Optional[str] = None,
        pallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find location of item or pallet
        
        Args:
            sku: Stock keeping unit (optional)
            pallet_id: Pallet identifier (optional)
            
        Returns:
            Location data
        """
        endpoint = "/api/v1/locations/find"
        params = {}
        
        if sku:
            params["sku"] = sku
        if pallet_id:
            params["pallet_id"] = pallet_id
        
        if not params:
            raise ValueError("Either sku or pallet_id must be provided")
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            logger.info(f"Found location: {response.get('data', {}).get('location')}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to find location: {e}")
            raise
    
    def move_item(
        self,
        sku: str,
        from_location: str,
        to_location: str,
        quantity: int,
        worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Move item from one location to another
        
        Args:
            sku: Stock keeping unit
            from_location: Source location
            to_location: Destination location
            quantity: Quantity to move
            worker_id: Worker performing move
            
        Returns:
            Move transaction data
        """
        endpoint = "/api/v1/inventory/move"
        
        payload = {
            "sku": sku,
            "from_location": from_location,
            "to_location": to_location,
            "quantity": quantity,
            "worker_id": worker_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = self._make_request("POST", endpoint, data=payload)
            logger.info(f"Moved {quantity} units of {sku} from {from_location} to {to_location}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to move item: {e}")
            raise
    
    def get_pick_list(
        self,
        wave_id: Optional[str] = None,
        worker_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pick list for order fulfillment
        
        Args:
            wave_id: Wave identifier (optional)
            worker_id: Worker identifier (optional)
            
        Returns:
            List of items to pick
        """
        endpoint = "/api/v1/pick-lists"
        params = {}
        
        if wave_id:
            params["wave_id"] = wave_id
        if worker_id:
            params["worker_id"] = worker_id
        
        try:
            response = self._make_request("GET", endpoint, params=params)
            pick_list = response.get("data", [])
            logger.info(f"Retrieved pick list with {len(pick_list)} items")
            return pick_list
        
        except Exception as e:
            logger.error(f"Failed to get pick list: {e}")
            raise
    
    def confirm_pick(
        self,
        pick_id: str,
        quantity_picked: int,
        worker_id: str
    ) -> Dict[str, Any]:
        """
        Confirm item picked
        
        Args:
            pick_id: Pick task identifier
            quantity_picked: Actual quantity picked
            worker_id: Worker performing pick
            
        Returns:
            Confirmation data
        """
        endpoint = f"/api/v1/pick-lists/{pick_id}/confirm"
        
        payload = {
            "quantity_picked": quantity_picked,
            "worker_id": worker_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = self._make_request("POST", endpoint, data=payload)
            logger.info(f"Confirmed pick {pick_id}: {quantity_picked} units")
            return response
        
        except Exception as e:
            logger.error(f"Failed to confirm pick: {e}")
            raise
    
    def get_location_capacity(self, location: str) -> Dict[str, Any]:
        """
        Get capacity information for location
        
        Args:
            location: Location identifier
            
        Returns:
            Capacity data
        """
        endpoint = f"/api/v1/locations/{location}/capacity"
        
        try:
            response = self._make_request("GET", endpoint)
            logger.info(f"Retrieved capacity for location {location}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to get location capacity: {e}")
            raise
    
    def create_pallet(
        self,
        items: List[Dict[str, Any]],
        location: str,
        worker_id: str
    ) -> Dict[str, Any]:
        """
        Create new pallet
        
        Args:
            items: List of items on pallet
            location: Pallet location
            worker_id: Worker creating pallet
            
        Returns:
            Created pallet data
        """
        endpoint = "/api/v1/pallets"
        
        payload = {
            "items": items,
            "location": location,
            "worker_id": worker_id,
            "created_at": datetime.now().isoformat()
        }
        
        try:
            response = self._make_request("POST", endpoint, data=payload)
            pallet_id = response.get("data", {}).get("pallet_id")
            logger.info(f"Created pallet {pallet_id} at {location}")
            return response
        
        except Exception as e:
            logger.error(f"Failed to create pallet: {e}")
            raise


if __name__ == "__main__":
    # Test WMS connector (with mock server)
    wms = WMSConnector(
        base_url="https://api.example-wms.com",
        api_key="test-key"
    )
    
    print("WMS Connector initialized")
    print(f"Base URL: {wms.base_url}")
