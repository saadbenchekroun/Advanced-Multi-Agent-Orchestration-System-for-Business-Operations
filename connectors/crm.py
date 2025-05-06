"""
CRM Connector for integrating with various CRM platforms.
Supports common operations like contact management, lead tracking, and opportunity handling.
"""

from typing import Dict, List, Optional, Any
import logging
import requests
from datetime import datetime
from enum import Enum

logger = logging.getLogger("agent_system.connectors.crm")

class CRMPlatform(Enum):
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    ZOHO = "zoho"
    DYNAMICS = "dynamics"
    GENERIC = "generic"

class ContactStatus(Enum):
    LEAD = "lead"
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    CHURNED = "churned"

class CRMConnector:
    """Connector for CRM systems like Salesforce, HubSpot, etc."""
    
    def __init__(self, api_key: str, base_url: str, platform: str = "generic", 
                 timeout: int = 30, retry_attempts: int = 3):
        """
        Initialize the CRM connector.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for the CRM API
            platform: CRM platform name (salesforce, hubspot, etc.)
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.platform = CRMPlatform(platform.lower())
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._session = None
        
        logger.info(f"Initialized CRM connector for {self.platform.value} platform")
    
    @property
    def session(self):
        """Lazy-loaded session object"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            })
        return self._session
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                      data: Dict = None) -> Dict:
        """Make an HTTP request to the CRM API with retry logic"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        attempt = 0
        
        while attempt < self.retry_attempts:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                attempt += 1
                logger.warning(f"CRM API request failed (attempt {attempt}/{self.retry_attempts}): {str(e)}")
                if attempt >= self.retry_attempts:
                    logger.error(f"CRM API request failed after {self.retry_attempts} attempts: {str(e)}")
                    raise
    
    def get_contacts(self, limit: int = 100, offset: int = 0, 
                     filters: Dict = None) -> List[Dict]:
        """
        Fetch contacts from the CRM system.
        
        Args:
            limit: Maximum number of contacts to retrieve
            offset: Pagination offset
            filters: Optional filtering criteria
            
        Returns:
            List of contact records
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            params.update(filters)
            
        response = self._make_request("GET", "contacts", params=params)
        logger.debug(f"Retrieved {len(response.get('data', []))} contacts from CRM")
        return response.get("data", [])
    
    def get_contact(self, contact_id: str) -> Dict:
        """
        Fetch a specific contact by ID.
        
        Args:
            contact_id: Unique identifier for the contact
            
        Returns:
            Contact record dictionary
        """
        response = self._make_request("GET", f"contacts/{contact_id}")
        return response.get("data", {})
    
    def create_contact(self, contact_data: Dict) -> Dict:
        """
        Create a new contact in the CRM.
        
        Args:
            contact_data: Dictionary with contact information
            
        Returns:
            Created contact record
        """
        required_fields = ["email", "first_name", "last_name"]
        for field in required_fields:
            if field not in contact_data:
                raise ValueError(f"Missing required field: {field}")
        
        response = self._make_request("POST", "contacts", data=contact_data)
        contact_id = response.get("data", {}).get("id")
        logger.info(f"Created new contact with ID: {contact_id}")
        return response.get("data", {})
    
    def update_contact(self, contact_id: str, contact_data: Dict) -> Dict:
        """
        Update an existing contact.
        
        Args:
            contact_id: Unique identifier for the contact
            contact_data: Updated contact information
            
        Returns:
            Updated contact record
        """
        response = self._make_request("PUT", f"contacts/{contact_id}", data=contact_data)
        logger.info(f"Updated contact with ID: {contact_id}")
        return response.get("data", {})
    
    def delete_contact(self, contact_id: str) -> bool:
        """
        Delete a contact from the CRM.
        
        Args:
            contact_id: Unique identifier for the contact
            
        Returns:
            True if deletion was successful
        """
        self._make_request("DELETE", f"contacts/{contact_id}")
        logger.info(f"Deleted contact with ID: {contact_id}")
        return True
    
    def get_deals(self, limit: int = 100, offset: int = 0, 
                  filters: Dict = None) -> List[Dict]:
        """
        Fetch deals/opportunities from the CRM.
        
        Args:
            limit: Maximum number of deals to retrieve
            offset: Pagination offset
            filters: Optional filtering criteria
            
        Returns:
            List of deal records
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            params.update(filters)
            
        response = self._make_request("GET", "deals", params=params)
        return response.get("data", [])
    
    def create_deal(self, deal_data: Dict) -> Dict:
        """
        Create a new deal/opportunity in the CRM.
        
        Args:
            deal_data: Dictionary with deal information
            
        Returns:
            Created deal record
        """
        required_fields = ["name", "value", "expected_close_date"]
        for field in required_fields:
            if field not in deal_data:
                raise ValueError(f"Missing required field: {field}")
        
        response = self._make_request("POST", "deals", data=deal_data)
        deal_id = response.get("data", {}).get("id")
        logger.info(f"Created new deal with ID: {deal_id}")
        return response.get("data", {})
    
    def search(self, query: str, entity_type: str = "contacts") -> List[Dict]:
        """
        Search the CRM for entities matching the query.
        
        Args:
            query: Search query string
            entity_type: Type of entity to search (contacts, deals, companies)
            
        Returns:
            List of matching records
        """
        params = {
            "q": query,
            "type": entity_type
        }
        
        response = self._make_request("GET", "search", params=params)
        return response.get("data", [])
    
    def get_activities(self, contact_id: str = None, 
                       date_from: datetime = None,
                       date_to: datetime = None) -> List[Dict]:
        """
        Fetch activities/events from the CRM.
        
        Args:
            contact_id: Filter activities by contact ID
            date_from: Filter activities after this date
            date_to: Filter activities before this date
            
        Returns:
            List of activity records
        """
        params = {}
        
        if contact_id:
            params["contact_id"] = contact_id
            
        if date_from:
            params["date_from"] = date_from.isoformat()
            
        if date_to:
            params["date_to"] = date_to.isoformat()
            
        response = self._make_request("GET", "activities", params=params)
        return response.get("data", [])
    
    def add_note(self, entity_id: str, entity_type: str, content: str) -> Dict:
        """
        Add a note to a CRM entity.
        
        Args:
            entity_id: ID of the entity (contact, deal, etc.)
            entity_type: Type of entity (contact, deal, company)
            content: Note content
            
        Returns:
            Created note record
        """
        data = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        
        response = self._make_request("POST", "notes", data=data)
        return response.get("data", {})
    
    def close(self):
        """Close any open connections"""
        if self._session:
            self._session.close()
            self._session = None
            logger.debug("Closed CRM connector session")