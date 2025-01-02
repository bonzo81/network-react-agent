import logging
from typing import Any, Dict, Optional, Union
import json

import requests
from pydantic import BaseModel

from ..utils.logger import setup_logger


class APIError(Exception):
    """Base exception for API-related errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(APIError):
    """Raised when API authentication fails"""

    pass


class ResourceNotFoundError(APIError):
    """Raised when requested resource is not found"""

    pass


class APIResponse(BaseModel):
    """Standardized API response model

    Attributes:
        success: Whether the API call was successful
        data: Response data if successful
        error: Error message if unsuccessful
        status_code: HTTP status code of the response
        raw_response: Raw response data for debugging
    """

    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    raw_response: Optional[Any] = None


class NetworkClient:
    """Client for interacting with network management APIs

    This client provides a standardized interface for interacting with network
    management systems like NetBox and LibreNMS. It handles authentication,
    request formatting, and error handling.

    Args:
        base_url: Base URL of the API
        api_token: Authentication token
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
    """

    def __init__(
        self, base_url: str, api_token: str, timeout: int = 30, verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.logger = logging.getLogger(f"NetworkClient-{base_url}")

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def query(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs,
    ) -> APIResponse:
        """Execute an API query

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            **kwargs: Additional request parameters

        Returns:
            APIResponse object containing the response or error

        Raises:
            AuthenticationError: If API authentication fails
            ResourceNotFoundError: If requested resource doesn't exist
            APIError: For other API-related errors
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.session.request(method, url, params=params, data=data, **kwargs)

        self.logger.debug(f"Executing {method} request to {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs,
            )

            # Log response status
            self.logger.debug(
                f"Received response: {response.status_code} "
                f"({len(response.content)} bytes)"
            )

            # Handle different status codes
            if response.status_code == 200:
                return APIResponse(
                    success=True,
                    data=response.json(),
                    status_code=response.status_code,
                    raw_response=response.text,
                )

            elif response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check API token.",
                    status_code=response.status_code,
                    response=response.text,
                )

            elif response.status_code == 404:
                raise ResourceNotFoundError(
                    f"Resource not found: {endpoint}",
                    status_code=response.status_code,
                    response=response.text,
                )

            else:
                raise APIError(
                    f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response=response.text,
                )

        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout for {url}")
            return APIResponse(
                success=False, error=f"Request timed out after {self.timeout} seconds"
            )

        except requests.exceptions.SSLError as e:
            self.logger.error(f"SSL verification failed: {e}")
            return APIResponse(
                success=False, error=f"SSL verification failed: {str(e)}"
            )

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return APIResponse(success=False, error=f"Request failed: {str(e)}")

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return APIResponse(success=False, error=f"Unexpected error: {str(e)}")

    def test_connection(self) -> bool:
        """Test API connectivity

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try a simple API call
            response = self.query("", method="GET")
            return response.success
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
