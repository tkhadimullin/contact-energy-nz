# API Connector to fetch power usage data from Contact Energy NZ utilities provider

This library wraps for accessing the Contact Energy API, allowing developers to programmatically interact with Contact Energy, utilities provider in New Zealand. 
This library supports a subset of operations: authenticate, get default account and retrieve energy-related usage data for that account.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Get accounts and contracts ](#get-accounts-and-contracts)
  - [Get usage data](#get-usage-data)
- [Contributing](#contributing)
- [License](#license)

## Installation

To install the Contact Energy Python API Library, you can use `pip`, the Python package manager:

```bash
pip install contact-energy-nz
```

## Usage

To get started, import API and main data types into code:

```python
from contact_energy_nz import AuthException, ContactEnergyApi
```

## Authentication

Before making API calls, you'll need to authenticate with Contact Energy and obtain a token. As far as I'm aware the only method to authenticate is to exchange user's email and password for an opaque access token. This becomes a `session` header on subsequent requests.

Library also needs an API key that presumably identifies the client to the backend. The value currently shipping with the library comes from `myaccount.contact.co.nz` website. It can be verified/updated by downloading the latest `https://myaccount.contact.co.nz/main.<hash>.esm.js` file (search for `x-api-key` in there). Since it's so easy to obtain I don't consider it to be very secret.

```python
import asyncio, async_timeout
from contact_energy_nz import AuthException, ContactEnergyApi

    try:
        async with async_timeout.timeout(TIMEOUT):
            connector = ContactEnergyApi.from_credentials(CONF_USERNAME, CONF_PASSWORD)
    except asyncio.TimeoutError as err:
        pass # handle timeout
    except AuthException as err:
        pass # handle auth errors
```

## API Endpoints
Currently we service just a couple of endpoints useful for HomeAssistant

### Get accounts and contracts 

```python
    try:
        await connector.account_summary()
    except Exception:
        pass # handle error
```

Call to `/accounts/v2?ba=` returns the following structure:

```json
{
    "accountsSummary": [
        {
            "id": "111111111",
            "nickname": "",
            "contracts": [
                {
                    "contractId": "111111111",
                    "premiseId": "111111111",
                    "address": "1 Queen Street / Auckland-Auckland Central 1010"
                }
            ]
        }
    ],
    "accountDetail": {
        "id": "111111111",
        "nickname": "",
        "correspondencePreference": "email",
        "paymentMethod": "Direct Debit",
        "isDirectDebit": true,
        "isSmoothPay": false,
        "isPrepay": false,
        "isControlpay": false,
        "isEligibleMonthOff": false,
        "directDebitAccount": "0001",
        "billingFrequency": "Monthly",
        "accountBalance": {
            "prepayDebtBalance": 0,
            "currentBalance": 0,
            "formattedCurrentBalance": "$0.00",
            "remainingDays": 0,
            "refundEligible": false,
            "refundMax": 0,
            "refundInProgress": 0
        },
        "invoice": {
            "amountPaid": 0,
            "amountDue": 888.88,
            "discountTotal": 0,
            "paymentDueDate": "1 Aug 2023",
            "daysTilOverdue": 0
        },
        "nextBill": {
            "date": "28 Aug 2023",
            "amount": 99.99,
            "ppd": 0
        },
        "monthOff": {},
        "payments": [
            {
                "amount": "$999.99",
                "date": "1 Aug 2023"
            },
            {
                "amount": "$999.99",
                "date": "1 Jul 2023"
            },
            {
                "amount": "$999.99",
                "date": "1 Jun 2023"
            }
        ],
        "contracts": [
            {
                "id": "111111111",
                "icp": "111111111",
                "meterType": "SMART METER",
                "promptPaymentDiscount": 0,
                "contractType": 1,
                "contractTypeLabel": "Electricity",
                "dualEnergy": false,
                "premise": {
                    "id": "111111111",
                    "supplyAddress": {
                        "houseNumber": "1",
                        "street": "Queen Street",
                        "city": "Auckland",
                        "postcode": 1010,
                        "shortForm": "1 Queen Street, Auckland Central, Auckland 1010"
                    },
                    "isEligibleForBroadband": true
                },
                "devices": [
                    {
                        "id": "111111111",
                        "serialNumber": "111111111",
                        "deviceProductTypeId": 1,
                        "nextMeterReadDate": "25 Aug 2023",
                        "nextReadingIsEstimate": false,
                        "meterLocationCode": "23",
                        "registers": [
                            {
                                "id": "001",
                                "registerType": "Load",
                                "previousMeterReading": "99999.00",
                                "readingUnit": "kWH",
                                "previousMeterReadingDate": "27 Jul 2023"
                            }
                        ],
                        "nonBillableRegisters": [
                            {
                                "id": "002",
                                "registerType": "Load",
                                "previousMeterReading": "0.00",
                                "readingUnit": "kWH",
                                "previousMeterReadingDate": "Invalid date"
                            }
                        ]
                    },
                    {
                        "id": "111111111",
                        "serialNumber": "111111111",
                        "deviceProductTypeId": 1,
                        "nextMeterReadDate": "25 Aug 2023",
                        "nextReadingIsEstimate": false,
                        "meterLocationCode": "00",
                        "registers": [],
                        "nonBillableRegisters": []
                    }
                ]
            }
        ],
        "hasMedicalDependant": false,
        "hasVulnerablePerson": false,
        "accountType": "RESI"
    },
    "statusCode": 2201,
    "xcsrfToken": "00000000"
}
```

### Get usage data

```python
    try:
        async with async_timeout.timeout(TIMEOUT):
            data = connector.get_latest_usage()
    except asyncio.TimeoutError as err:
        pass # handle timeout
    except Exception as err:
        pass # handle error
```

Call to `/usage/v2/{contract_id}?ba={account_id}&interval=monthly&from=YYY-MM-DD&to=YYYY-MM-DD` returns the following structure: 

```json
[
    {
        "currency": "NZD",
        "year": 2023,
        "month": 4,
        "day": 1,
        "hour": 0,
        "date": "2023-04-01T00:00:00.000+13:00",
        "value": "999.999",
        "dollarValue": "999.999",
        "offpeakValue": "99.999",
        "unchargedValue": "99.999",
        "offpeakDollarValue": "0.000",
        "unit": "kWh",
        "timeZone": "Pacific/Auckland",
        "percentage": 9.99
    },
    {
        "currency": "NZD",
        "year": 2023,
        "month": 5,
        "day": 1,
        "hour": 0,
        "date": "2023-05-01T00:00:00.000+12:00",
        "value": "999.999",
        "dollarValue": "999.999",
        "offpeakValue": "99.999",
        "unchargedValue": "99.999",
        "offpeakDollarValue": "0.000",
        "unit": "kWh",
        "timeZone": "Pacific/Auckland",
        "percentage": 9.99
    },
    {
        "currency": "NZD",
        "year": 2023,
        "month": 6,
        "day": 1,
        "hour": 0,
        "date": "2023-06-01T00:00:00.000+12:00",
        "value": "999.999",
        "dollarValue": "999.999",
        "offpeakValue": "99.999",
        "unchargedValue": "99.999",
        "offpeakDollarValue": "0.000",
        "unit": "kWh",
        "timeZone": "Pacific/Auckland",
        "percentage": 9.99
    },
    {
        "currency": "NZD",
        "year": 2023,
        "month": 7,
        "day": 1,
        "hour": 0,
        "date": "2023-07-01T00:00:00.000+12:00",
        "value": "999.999",
        "dollarValue": "999.999",
        "offpeakValue": "99.999",
        "unchargedValue": "99.999",
        "offpeakDollarValue": "0.000",
        "unit": "kWh",
        "timeZone": "Pacific/Auckland",
        "percentage": 9.99
    },
    {
        "currency": "NZD",
        "year": 2023,
        "month": 8,
        "day": 1,
        "hour": 0,
        "date": "2023-08-01T00:00:00.000+12:00",
        "value": "999.999",
        "dollarValue": "999.999",
        "offpeakValue": "99.999",
        "unchargedValue": "99.999",
        "offpeakDollarValue": "0.000",
        "unit": "kWh",
        "timeZone": "Pacific/Auckland",
        "percentage": 9.99
    }
]
```

## Contributing
Contributions are welcome and encouraged. If you want to add new features, please feel free to open PRs here.

## License
This library is provided under the MIT License.

---
    Disclaimer: This library is an independent project and is not affiliated with Contact Energy. While it provides access to certain API features, it does not cover all available functionalities. Please note that the upstream API can change unexpectedly, potentially leading to disruptions in functionality, as has occurred around May 2023. Use at your own discretion.
