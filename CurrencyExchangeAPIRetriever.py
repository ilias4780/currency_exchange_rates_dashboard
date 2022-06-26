import datetime

import requests


class CurrencyExchangeAPIRetriever(object):
    """
    Class that retrieves the currency exchange data from Fixer API.

    :param api_key: API unique key, required to authenticate for the requests.
    :type api_key: str
    """
    def __init__(self, api_key):
        self.api_key = api_key

    def get_all_available_symbols(self):
        """
        Retrieves all available currency exchange symbols and their long names, and
        returns them in a dictionary format.

        :return: dict
        """
        url = "https://api.apilayer.com/fixer/symbols"
        headers = {"apikey": self.api_key}
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve all available symbols, with error status: {response.status_code}.")

        return response.json()["symbols"]

    def get_latest_exchange_rates(self, base=None, symbols=None):
        """
        Retieves real-time exchange rate data updated every 60 minutes, every 10 minutes or every 60 seconds.
        Returns a dictionary containing all data.

        :param base: Base three-letter currency code of your preferred base currency.
        :type base: str
        :param symbols: String of comma-separated currency codes to limit output currencies
        :type symbols: str
        :return: dict
        """
        if all([symbols, base]):
            url = f"https://api.apilayer.com/fixer/latest?symbols={symbols}&base={base}"
            headers = {"apikey": self.api_key}
            response = requests.request("GET", url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve latest exchange rates, with error status: {response.status_code}.")
            return response.json()
        else:
            print("Either base or symbols argument was None. Please pass both arguments.")

    def get_timeseries_of_exchange_rates(self, start_date=None, end_date=None, base=None, symbols=None):
        """
        Retrieves a timeseries of exchange rates between the base currency and the symbols. Start and end date should
        not be more than 365 days different.

        :param start_date: Start date for the timeseries retrieval. Should follow YYYY-MM-DD format.
        :type start_date: str
        :param end_date: End date for the timeseries retrieval. Should follow YYYY-MM-DD format.
        :type end_date: str
        :param base: Base three-letter currency code of your preferred base currency.
        :type base: str
        :param symbols: String of comma-separated currency codes to limit output currencies
        :type symbols: str
        :return: dict
        """
        if all([start_date, end_date, base, symbols]):
            if datetime.datetime.strptime(end_date, "%Y-%m-%d") - datetime.datetime.strptime(start_date, "%Y-%m-%d") > \
              datetime.timedelta(days=365):
                print("Days between end date and start date is larger than 365 days. Please select valid dates.")
            else:
                url = f"https://api.apilayer.com/fixer/timeseries?symbols={symbols}&base={base}" \
                      f"&start_date={start_date}&end_date={end_date}"
                headers = {"apikey": self.api_key}
                response = requests.request("GET", url, headers=headers)
                if response.status_code != 200:
                    raise Exception(f"Failed to retrieve latest exchange rates, with error status: {response.status_code}.")
                return response.json()
        else:
            print("At least one of the arguments was None. Please provide all arguments.")
