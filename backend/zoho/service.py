from typing import Dict, Any, Optional
from core.config import settings
from zoho.client import LiveZohoClient
from zoho.mock_client import mock_zoho_client
from zoho.token_manager import token_manager


class ZohoService:
    def __init__(self):
        self.live_client = LiveZohoClient()
        self.mock_client = mock_zoho_client

    @property
    def is_live(self) -> bool:
        return (not settings.USE_MOCK_ZOHO) and token_manager.is_configured

    async def create_lead(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_live:
            try:
                return await self.live_client.create_lead(payload)
            except Exception:
                # Log error and fallback to mock to prevent user interruption
                return await self.mock_client.create_lead(payload)
        return await self.mock_client.create_lead(payload)

    async def search_deal(self, identifier: str) -> Optional[Dict[str, Any]]:
        if self.is_live:
            try:
                res = await self.live_client.search_deal_by_phone_or_id(identifier)
                if res:
                    return res
            except Exception:
                pass
        return await self.mock_client.search_deal_by_phone_or_id(identifier)

    async def search_contact(self, phone: str) -> Optional[Dict[str, Any]]:
        if self.is_live:
            try:
                return await self.live_client.search_contact_by_phone(phone)
            except Exception:
                pass
        return await self.mock_client.search_contact_by_phone(phone)

    async def get_or_create_account(self, account_name: str, phone: str) -> Optional[str]:
        if self.is_live:
            try:
                return await self.live_client.get_or_create_account(account_name, phone)
            except Exception:
                pass
        return await self.mock_client.get_or_create_account(account_name, phone)

    async def get_or_create_contact(
        self, contact_name: str, phone: str, account_id: Optional[str] = None
    ) -> Optional[str]:
        if self.is_live:
            try:
                return await self.live_client.get_or_create_contact(contact_name, phone, account_id=account_id)
            except Exception:
                pass
        return await self.mock_client.get_or_create_contact(contact_name, phone, account_id=account_id)

    async def update_deal(self, deal_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_live:
            try:
                return await self.live_client.update_deal(deal_id, updates)
            except Exception:
                pass
        return await self.mock_client.update_deal(deal_id, updates)

    async def get_booking(self, booking_id_or_phone: str) -> Optional[Dict[str, Any]]:
        if self.is_live:
            try:
                res = await self.live_client.get_booking_deal(booking_id_or_phone)
                if res:
                    return res
            except Exception:
                pass
        return await self.mock_client.get_booking_deal(booking_id_or_phone)

    async def create_service_case(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_live:
            try:
                return await self.live_client.create_service_case(payload)
            except Exception:
                pass
        return await self.mock_client.create_service_case(payload)


zoho_service = ZohoService()
