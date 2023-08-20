"""
API Interface Module
"""
import datetime
from typing import Any
import aiohttp
import logging

from .usage_datum import UsageDatum
from .consts import API_BASE_URL, API_KEY

_LOGGER = logging.getLogger(__name__)


class AuthException(Exception):
    """Error to indicate we cannot authenticate to API."""


class ContactEnergyApi:
    """Contact Energy auth and data poller."""

    def __init__(
        self, username: str = None, password: str = None, token: str = None
    ) -> None:
        self.username = username
        self.password = password
        self.token = token
        self.contract_id = None
        self.account_id = None

    @classmethod
    async def from_credentials(cls, username: str, password: str):
        """Construct instance of ContactEnergyConnector from username and password. Fetches API token"""
        instance = cls(username, password)
        await instance.get_token()
        return instance

    @classmethod
    def from_token(cls, token: str):
        """Construct instance of ContactEnergyConnector from API token"""
        return cls(token=token)

    async def get_token(self) -> str:
        """Perform authentication and get API token"""
        async with aiohttp.ClientSession() as session:
            headers = {"x-api-key": API_KEY}
            data = {"username": self.username, "password": self.password}
            async with session.post(
                f"{API_BASE_URL}/login/v2", headers=headers, json=data
            ) as response:
                try:
                    response_json = await response.json()
                    self.token = response_json.get("token", "")
                    return self.token
                except AttributeError as e:
                    raise AuthException(f"Error accessing JSON fields: {e}")

    def _set_headers(self) -> dict[str, str]:
        """Helper method to set required headers"""
        if self.token is None:
            raise ValueError("Authorisation token is empty")

        return {
            "x-api-key": API_KEY,
            "session": self.token,
            "authorization": self.token,
        }

    async def _try_fetch_data(self, url, method="get") -> Any:
        try:
            async with aiohttp.ClientSession() as session:
                fn = session.get if method == "get" else session.post
                async with fn(url, headers=self._set_headers()) as response:
                    if response.status == 401:
                        _LOGGER.warning("Unauthorized access: %s", response.reason)
                        raise AuthException(response.reason)
                    elif response.status == 403:
                        _LOGGER.warning("Access forbidden: %s", response.reason)
                        raise AuthException(response.reason)
                    else:
                        return await response.json()
        except aiohttp.ClientError as error:
            _LOGGER.error("Error fetching data from server: %s", error)
            raise

    async def account_summary(self):
        """Helper method to query account summary and determine account/contract id"""
        accounts = await self._try_fetch_data(f"{API_BASE_URL}/accounts/v2?ba=")
        account_summary = accounts.get("accountsSummary", [])
        if not account_summary:
            raise ValueError("No account_summary found in API response")

        first_account = account_summary[0]
        self.account_id = first_account.get("id", "")
        contracts = first_account.get("contracts", [])
        first_contract = contracts[0]
        self.contract_id = first_contract.get("contractId", "")

        if not self.account_id or not self.contract_id:
            raise ValueError("No account_id or contract_id found in API response")

    async def get_latest_usage(self) -> list[UsageDatum]:
        """Query latest available monthly usage stats"""
        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(
            day=(
                datetime.date(today.year, today.month + 1, 1)
                - datetime.timedelta(days=1)
            ).day
        )

        if first_day > today:
            raise ValueError("Date cannot be in the future")

        return (await self.get_usage(first_day, last_day))[0]

    async def get_usage(
        self, start_date: datetime, end_date: datetime
    ) -> list[UsageDatum]:
        """Query monthly usage stats for given range"""

        formatted_start_date = start_date.strftime("%Y-%m-%d")
        formatted_end_date = end_date.strftime("%Y-%m-%d")

        url = f"{API_BASE_URL}/usage/v2/{self.contract_id}?ba={self.account_id}&interval=monthly&from={formatted_start_date}&to={formatted_end_date}"
        monthly_stats = await self._try_fetch_data(url, "post")
        return sorted(
            [UsageDatum(item) for item in monthly_stats],
            key=lambda x: x.date,
            reverse=True,
        )
