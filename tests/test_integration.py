import asyncio
import datetime
import os
import pytest
import pytest_asyncio
from contact_energy_nz import ContactEnergyApi, AuthException
from dotenv import load_dotenv
import logging

load_dotenv()
_LOGGER = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_authentication_fails(api_client):
    with pytest.raises(AuthException) as _:
        api = await ContactEnergyApi.from_credentials(os.environ["CONTACT_USERNAME"], "invalid password")

@pytest_asyncio.fixture(scope="session")
async def api_client() -> ContactEnergyApi: 
    api = await ContactEnergyApi.from_credentials(os.environ["CONTACT_USERNAME"], os.environ["CONTACT_PASSWORD"])
    await api.account_summary()
    return api

def test_should_be_able_to_login_with_credentials(api_client):
    # we should get the token
    assert api_client.token 

def test_should_be_able_to_get_contract_info_after_login(api_client):
    assert api_client.account_id
    assert api_client.contract_id

@pytest.mark.asyncio
async def test_should_be_able_to_get_monthly_usage_for_current_month(api_client):
    current_month = datetime.date.today().month
    results = await api_client.get_latest_usage()
    
    assert results
    assert results.date.month == current_month

@pytest.mark.asyncio
async def test_should_be_able_to_get_hourly_usage(api_client):
    # Timedelta as hourly usage doesn't get updated for a few days
    day_to_test = datetime.date.today() - datetime.timedelta(weeks=1)
    results = await api_client.get_hourly_usage(day_to_test)

    assert results
    assert results[0].date.day == day_to_test.day
    assert results[0].date.hour == 0
