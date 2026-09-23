import time
import httpx
from typing import Optional, Dict, Any
from core.config import settings


class ZohoTokenManager:
    """Manages Zoho OAuth 2.0 Access Token lifecycle with connection pooling.
    
    Exchanges refresh_token -> access_token, caches token in memory,
    refreshes proactively 5 minutes before expiration, and supports
    automatic retry on 401 Unauthorized responses using a shared HTTP client.
    """

    def __init__(self):
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0
        self.accounts_url = settings.ZOHO_ACCOUNTS_URL.rstrip("/")
        self.client_id = settings.ZOHO_CLIENT_ID
        self.client_secret = settings.ZOHO_CLIENT_SECRET
        self.refresh_token = settings.ZOHO_REFRESH_TOKEN
        # Persistent HTTP client with connection pooling to eliminate TLS handshake latency
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=15.0,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=60.0),
            )
        return self._http_client

    async def get_valid_access_token(self, force_refresh: bool = False) -> str:
        if not self.is_configured:
            raise ValueError("Zoho OAuth credentials are not fully configured in environment.")

        # Proactive refresh: if token expires within 300 seconds (5 minutes)
        now = time.time()
        if not force_refresh and self._access_token and (self._expires_at - now > 300):
            return self._access_token

        # Exchange refresh token for fresh access token
        url = f"{self.accounts_url}/oauth/v2/token"
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
        }

        client = self._get_client()
        response = await client.post(url, params=params)
        if response.status_code != 200:
            raise RuntimeError(
                f"Zoho Token Exchange failed with HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        if "error" in data:
            raise RuntimeError(f"Zoho OAuth Error: {data.get('error')}")

        token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)

        self._access_token = token
        self._expires_at = now + float(expires_in)
        return token

    async def execute_with_token(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Wraps Zoho API calls with persistent connection pooling and automatic 401 retry."""
        token = await self.get_valid_access_token()
        base_url = settings.ZOHO_API_BASE_URL.rstrip("/")
        url = f"{base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Zoho-oauthtoken {token}"}

        client = self._get_client()
        response = await client.request(method, url, headers=headers, json=json_data, params=params)

        # If 401 Unauthorized, force refresh token once and retry
        if response.status_code == 401:
            new_token = await self.get_valid_access_token(force_refresh=True)
            headers["Authorization"] = f"Zoho-oauthtoken {new_token}"
            response = await client.request(method, url, headers=headers, json=json_data, params=params)

        if response.status_code == 204 or not response.text.strip():
            return {"data": []}

        if response.status_code >= 400:
            raise RuntimeError(f"Zoho API error ({response.status_code}) on {url}: {response.text}")

        return response.json()

    async def aclose(self):
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()


token_manager = ZohoTokenManager()
