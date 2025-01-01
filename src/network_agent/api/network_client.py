from typing import Dict, Optional
import requests
from pydantic import BaseModel

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

class NetworkClient:
    def __init__(self, base_url: str, api_token: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout
        
    def query(self, endpoint: str, method: str = "GET", 
             params: Optional[Dict] = None, data: Optional[Dict] = None) -> APIResponse:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Token {self.api_token}"}
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return APIResponse(success=True, data=response.json())
        except requests.exceptions.RequestException as e:
            return APIResponse(success=False, error=str(e))