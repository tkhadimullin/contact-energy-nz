"""
API Interface Module
"""
import datetime
from typing import Any
import aiohttp
import logging

from contact_energy_nz.usage_datum import UsageDatum
from contact_energy_nz.consts import API_BASE_URL, API_KEY

_LOGGER = logging.getLogger(__name__)


class AuthException(Exception):
    """Error to indicate we cannot authenticate to API."""

class ContactEnergyConnector:
    """Contact Energy auth and data poller."""

    def __init__(
        self, username: str = None, password: str = None, token: str = None
    ) -> None:
        self.username = username
        self.password = password
        self.token = token
        self.accounts = None
        self.usage = None
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
            url = f"{API_BASE_URL}/login"
            headers = {"x-api-key": API_KEY}
            data = {"username": self.username, "password": self.password}
            async with session.post(url, headers=headers, json=data) as response:
                response_json = await response.json()
                self.token = response_json["token"]
                return self.token

    def _set_headers(self) -> dict[str, str]:
        """Helper method to set required headers"""
        if self.token is None:
            raise ValueError("Authorisation token is empty")

        return {
            "x-api-key": API_KEY,
            "session": self.token,
            "authorization": self.token,
        }

    async def _try_fetch_data(self, url) -> Any:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self._set_headers()) as response:
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
        self.accounts = await self._try_fetch_data(f"{API_BASE_URL}/accounts?ba=")       

    async def get_usage(self) -> list[UsageDatum]:
        """Query latest available hourly usage stats. These are likely going to always be couple days old"""
        async with aiohttp.ClientSession() as session:
            today = datetime.date.today()
            first_day = today.replace(day=1)
            last_day = today.replace(
                day=(
                    datetime.date(today.year, today.month + 1, 1)
                    - datetime.timedelta(days=1)
                ).day
            )

            formatted_start_date = first_day.strftime("%Y-%m-%d")
            formatted_end_date = last_day.strftime("%Y-%m-%d")
            url = f"{API_BASE_URL}/usage/{self.contract_id}?ba={self.account_id}&interval=daily&from={formatted_start_date}&to={formatted_end_date}"
            async with session.post(url, headers=self._set_headers()) as response:
                if response.status == 401:
                    _LOGGER.warning("Unauthorized access: %s", response.reason)
                    raise AuthException(response.reason)
                elif response.status == 403:
                    _LOGGER.warning("Access forbidden: %s", response.reason)
                    raise AuthException(response.reason)
                else:
                    daily_stats = await response.json()

            sorted_daily_stats = sorted(
                daily_stats, key=lambda x: x["date"], reverse=True
            )
            last_available_day = datetime.datetime.strptime(
                sorted_daily_stats[0]["date"], "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            formatted_last_available_day = last_available_day.strftime("%Y-%m-%d")

            url = f"{API_BASE_URL}/usage/{self.contract_id}?ba={self.account_id}&interval=hourly&from={formatted_last_available_day}&to={formatted_last_available_day}"
            async with session.post(url, headers=self._set_headers()) as response:
                if response.status == 401:
                    _LOGGER.warning("Unauthorized access: %s", response.reason)
                    raise AuthException(response.reason)
                elif response.status == 403:
                    _LOGGER.warning("Access forbidden: %s", response.reason)
                    raise AuthException(response.reason)
                else:
                    usage_response = await response.json()
                    return sorted(
                        [UsageDatum(item) for item in usage_response],
                        key=lambda x: x.date,
                    )
