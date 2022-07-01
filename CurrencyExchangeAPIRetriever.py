import datetime

import requests
from dateutil.relativedelta import relativedelta


class CurrencyExchangeAPIRetriever(object):
    """
    Class that retrieves the currency exchange data from Fixer API.

    :param api_key: API unique key, required to authenticate for the requests.
    :type api_key: str
    """

    valid_periods = [None, "1y", "2y", "3y", "5y"]

    def __init__(self, api_key):
        self.api_key = api_key

    def retrieve_all_available_symbols(self):
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

    def retrieve_latest_exchange_rates(self, base=None, symbols=None):
        """
        Retrieves real-time exchange rate data updated every 60 minutes, every 10 minutes or every 60 seconds.
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
            raise Exception("Either base or symbols argument was None. Please pass both arguments.")

    def _retrieve_timeseries_of_exchange_rates(self, start_date=None, end_date=None, base=None, symbols=None):
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
        url = f"https://api.apilayer.com/fixer/timeseries?symbols={symbols}&base={base}" \
              f"&start_date={start_date}&end_date={end_date}"
        headers = {"apikey": self.api_key}
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve latest exchange rates, with error status: {response.status_code}.")
        return response.json()

    def get_timeseries_of_exchange_rates(self, start_date=None, end_date=None, period=None, base=None, symbols=None):
        """
        Get a timeseries of exchange rates of the base currency against the symbols, between the start and end
        date, or for the period specified. Returns a dict containing the results.

        :param start_date: Start date for the timeseries retrieval. Should follow YYYY-MM-DD format.
        :type start_date: str
        :param end_date: End date for the timeseries retrieval. Should follow YYYY-MM-DD format.
        :type end_date: str
        :param period: Time period for retrieving data. Valid periods: ["1y", "2y", "3y", "5y"]
        :type period: str
        :param base: Base three-letter currency code of your preferred base currency.
        :type base: str
        :param symbols: String of comma-separated currency codes to limit output currencies
        :type symbols: str
        :return: dict
        """
        # check how many requests are needed based on the number of years of the time period requested
        if period:
            number_of_years = int(period[0])
        elif start_date and end_date:
            number_of_years = relativedelta(datetime.datetime.strptime(end_date, "%Y-%m-%d"),
                                            datetime.datetime.strptime(start_date, "%Y-%m-%d")).years + 1
        else:
            raise Exception("Please provide valid arguments. Provide a period or both start and end date.")

        # based on the number of years, make the necessary amount of requests
        if number_of_years <= 1:
            if period:
                date_today = datetime.datetime.today()
                return self._retrieve_timeseries_of_exchange_rates(
                    (date_today - relativedelta(years=1)).strftime("%Y-%m-%d"), date_today.strftime("%Y-%m-%d"),
                    base, symbols
                )
            else:
                return self._retrieve_timeseries_of_exchange_rates(start_date, end_date, base, symbols)
        else:
            data_retrieved = []
            date_today = datetime.datetime.today()
            for year in range(number_of_years):
                if period:
                    end_date_req = (date_today - relativedelta(years=year)).strftime("%Y-%m-%d")
                    start_date_req = (date_today - relativedelta(years=year + 1)).strftime("%Y-%m-%d")
                else:
                    end_date_req = (datetime.datetime.strptime(end_date, "%Y-%m-%d") -
                                    relativedelta(years=year)).strftime("%Y-%m-%d")
                    start_date_req = (datetime.datetime.strptime(end_date, "%Y-%m-%d") -
                                      relativedelta(years=year + 1)).strftime("%Y-%m-%d")
                    if start_date_req < start_date:
                        start_date_req = start_date
                data_retrieved.append(self._retrieve_timeseries_of_exchange_rates(
                    start_date_req, end_date_req, base, symbols))
            # post process the requests
            results_dict = dict()
            results_dict["start_date"] = data_retrieved[-1]["start_date"]
            results_dict["end_date"] = data_retrieved[0]["end_date"]
            for item in reversed(data_retrieved):
                if "rates" not in results_dict:
                    results_dict["rates"] = item["rates"]
                else:
                    results_dict["rates"].update(item["rates"])
            return results_dict
