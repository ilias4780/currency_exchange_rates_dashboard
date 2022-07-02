import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from bokeh.models import DatetimeTickFormatter, HoverTool
from bokeh.plotting import figure
from calendar import month_name
from dateutil.relativedelta import relativedelta

from CurrencyExchangeAPIRetriever import CurrencyExchangeAPIRetriever


def calculate_best_months(timeseries_dict, symbol):
    """
    Calculates the best months to exchange your base currency to your target currency. Results are based on
    the best average rates per month of the requested period.

    :param timeseries_dict: Dictionary containing the retrieved timeseries
    :type timeseries_dict: dict
    :param symbol: Currency symbols
    :type symbol: str
    :return: pd.Dataframes
    """
    df = pd.DataFrame(
        list(zip(timeseries_dict["rates"].keys(),
                 [item[symbol] for item in timeseries_dict["rates"].values()])),
        columns=["Datetime", "Rate"])
    # convert type of datetime column to datetime
    df["Datetime"] = pd.to_datetime(df["Datetime"], format="%Y-%m-%d")
    # group by and find the average per month
    df = df.groupby(pd.Grouper(freq='M', key="Datetime")).mean().reset_index()
    # convert type of datetime index to string again using only the month
    df["Datetime"] = df["Datetime"].dt.strftime('%B')
    df = df.rename(columns={'Datetime': 'Month'})
    # group by and find the average per month in total
    df = df.groupby(by="Month").mean().reset_index()
    # sort based on months
    months = list(month_name)
    df['Month'] = pd.Categorical(df['Month'], categories=months, ordered=True)
    df.sort_values(by="Month", inplace=True)
    return df


def plot_charts(base_currency_t, selected_symbols_list_t, timeseries_dict):
    """
    Plots the timeseries and best months charts for all target currency symbols.

    :param base_currency_t: Base three-letter currency code of your preferred base currency.
    :type base_currency_t: str
    :param selected_symbols_list_t: Currency target symbols
    :type selected_symbols_list_t: list
    :param timeseries_dict: Dictionary containing the retrieved timeseries
    :type timeseries_dict: dict
    """
    for symbol in selected_symbols_list_t:
        # timeseries chart
        p = figure(
            title=f"Line chart showing the timeseries currency exchange rates of {base_currency_t} to the "
                  f"requested currency: {symbol}.",
            x_axis_label="Date",
            x_axis_type="datetime",
            y_axis_label=f"{base_currency_t} -> {symbol} rate"
        )
        p.line([datetime.strptime(date, "%Y-%m-%d") for date in timeseries_dict["rates"].keys()],
               [item[symbol] for item in timeseries_dict["rates"].values()], legend_label='Trend', line_width=2)
        p.add_tools(HoverTool(tooltips=[("Rate", "@y"), ("Date", "@x{%Y-%m-%d}")],
                              formatters={"@x": "datetime"}, mode="vline"))
        st.bokeh_chart(p, use_container_width=True)

        # best month chart
        best_months_df = calculate_best_months(timeseries_dict, symbol)
        p2 = figure(
            title=f"Line chart showing the best months to trade in average by using "
                  f"data for the selected time interval.",
            x_axis_label="Month",
            x_axis_type="datetime",
            y_axis_label=f"{base_currency_t} -> {symbol} rate"
        )
        p2.line([datetime.strptime(item, "%B") for item in best_months_df["Month"].to_list()],
                list(map(float, best_months_df["Rate"].to_list())),
                legend_label='Trend', line_width=2)
        p2.xaxis[0].formatter = DatetimeTickFormatter(months="%B")
        p2.add_tools(HoverTool(tooltips=[("Rate", "@y"), ("Date", "@x{%B}")],
                               formatters={"@x": "datetime"}, mode="vline"))
        st.bokeh_chart(p2, use_container_width=True)


def run_dashboard():
    # load the api key from the config file
    with open("configuration.json") as f:
        api_key = json.load(f)["api_key"]

    # create the dashboard
    st.set_page_config(layout="wide")
    st.title("Currency Exchange API Retriever App")
    st.text("--------------------------------------------------------------------------------------------------------")

    # create a retriever instance
    retriever = CurrencyExchangeAPIRetriever(api_key)

    # retrieve all symbols
    st.header("Currency Symbols and long names")
    if "all_symbols" not in st.session_state:
        with st.spinner('Retrieving..'):
            st.session_state.all_symbols = retriever.retrieve_all_available_symbols()
        st.session_state.all_symbols_df = pd.DataFrame(list(zip(st.session_state.all_symbols.keys(),
                                                                st.session_state.all_symbols.values())),
                                                       columns=["Symbol", "Long Name"])
    st.dataframe(st.session_state.all_symbols_df)
    st.text("--------------------------------------------------------------------------------------------------------")

    # retrieve latest exchange rates
    st.header("Latest Exchange Rates")
    base_currency_l = st.selectbox("Base currency symbol", st.session_state.all_symbols.keys(),
                                   index=list(st.session_state.all_symbols.keys()).index("GBP"), key="latest_sb")
    selected_symbols_list_l = st.multiselect("Currency symbols to limit output currencies",
                                             st.session_state.all_symbols.keys(), default=None, key="latest_msb")
    if st.button("Finished selection, retrieve rates"):
        if base_currency_l and selected_symbols_list_l:
            with st.spinner('Retrieving..'):
                latest_rates = retriever.retrieve_latest_exchange_rates(base=base_currency_l,
                                                                        symbols=','.join(selected_symbols_list_l))
            st.text(f"Rates last updated at "
                    f"{datetime.fromtimestamp(latest_rates['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            for symbol, value in latest_rates["rates"].items():
                st.metric(label=f"{latest_rates['base']} -> {symbol}", value=value)
        else:
            st.warning("No target currency symbols have been selected. Please select at least one.")
    st.text("--------------------------------------------------------------------------------------------------------")

    # retrieve timeseries of exchange rates
    st.header("Exchange Rates Timeseries and Best Months to Trade charts")
    base_currency_t = st.selectbox("Base currency symbol", st.session_state.all_symbols.keys(),
                                   index=list(st.session_state.all_symbols.keys()).index("GBP"), key="timeseries_sb")
    selected_symbols_list_t = st.multiselect("Currency symbols to limit output currencies",
                                             st.session_state.all_symbols.keys(), default=None, key="timeseries_msb")
    st.markdown("""
    Please select either a `Time period` from below or a `Start date` and an `End date`. If you select both, then the 
    `Time period` will be used, and not the `Start date` and `End date`.
    
    N.B. Fixer API allows to retrieve a timeseries of only one year. If you have selected a time period or dates that
    span longer than a year, then multiple requests will be made. Please be cautious around the number of requests
    you have available via your API subscription.
    """)
    time_period = st.selectbox("Time period", CurrencyExchangeAPIRetriever.valid_periods)
    end_date = st.date_input("End date of timeseries",
                             value=datetime.today(),
                             max_value=datetime.today(),
                             help="Must be later than start date.")
    start_date = st.date_input("Start date of timeseries",
                               value=end_date - timedelta(days=1),
                               min_value=end_date - relativedelta(years=5),
                               max_value=end_date - timedelta(days=1),
                               help="Must be earlier than end date.")
    if st.button("Finished selection, retrieve timeseries"):
        if selected_symbols_list_t:
            if (start_date and end_date) or time_period:
                with st.spinner('Retrieving..'):
                    if time_period:
                        if (base_currency_t, selected_symbols_list_t, time_period) not in st.session_state:
                            st.session_state[(base_currency_t, selected_symbols_list_t, time_period)] = \
                                retriever.get_timeseries_of_exchange_rates(
                                    period=time_period,
                                    base=base_currency_t,
                                    symbols=','.join(selected_symbols_list_t))
                        plot_charts(base_currency_t, selected_symbols_list_t,
                                    st.session_state[(base_currency_t, selected_symbols_list_t, time_period)])
                    else:
                        if (base_currency_t, selected_symbols_list_t, start_date, end_date) not in st.session_state:
                            st.session_state[(base_currency_t, selected_symbols_list_t, start_date, end_date)] = \
                                retriever.get_timeseries_of_exchange_rates(
                                        start_date=start_date.strftime("%Y-%m-%d"),
                                        end_date=end_date.strftime("%Y-%m-%d"),
                                        base=base_currency_t,
                                        symbols=','.join(selected_symbols_list_t))
                        plot_charts(base_currency_t, selected_symbols_list_t,
                                    st.session_state[(base_currency_t, selected_symbols_list_t, start_date, end_date)])
        else:
            st.error("No target currency symbols have been selected. Please select at least one.")


if __name__ == '__main__':
    run_dashboard()
