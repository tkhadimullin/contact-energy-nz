import datetime

from attr import dataclass

class UsageDatum:
    """Helper class for data manipulation"""

    def __init__(self, json_item) -> None:
        """Construct class out of json dictionary"""
        self.currency = json_item["currency"]
        self.date = datetime.datetime.strptime(
            json_item["date"], "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        self.value = float(json_item["value"])

        try:
            self.dollar_value = float(json_item["dollarValue"])
        except (TypeError, ValueError):
            self.dollar_value = None

        try:
            self.offpeak_value = float(json_item["offpeakValue"])
        except (TypeError, ValueError):
            self.offpeak_value = None

        try:
            self.uncharged_value = float(json_item["unchargedValue"])
        except (TypeError, ValueError):
            self.uncharged_value = None

        try:
            self.offpeak_dollar_value = float(json_item["offpeakDollarValue"])
        except (TypeError, ValueError):
            self.offpeak_dollar_value = None

        self.unit = json_item["unit"]

    def __str__(self) -> str:
        return f"{self.date}: value={self.value}, dollarValue={self.dollar_value}, uncharged_value={self.uncharged_value}, offpeak_value={self.offpeak_value}, offpeak_dollar_value={self.offpeak_dollar_value}\n"

    def __repr__(self) -> str:
        return str(self)