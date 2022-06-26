import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from bokeh.models import HoverTool
from bokeh.plotting import figure

from CurrencyExchangeAPIRetriever import CurrencyExchangeAPIRetriever


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
            st.session_state.all_symbols = retriever.get_all_available_symbols()
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
                latest_rates = retriever.get_latest_exchange_rates(base=base_currency_l,
                                                                   symbols=','.join(selected_symbols_list_l))
            st.text(f"Rates last updated at "
                    f"{datetime.fromtimestamp(latest_rates['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            for symbol, value in latest_rates["rates"].items():
                st.metric(label=f"{latest_rates['base']} -> {symbol}", value=value)
        else:
            st.warning("No target currency symbols have been selected. Please select at least one.")
    st.text("--------------------------------------------------------------------------------------------------------")

    # retrieve timeseries of exchange rates
    st.header("Exchange Rates Timeseries")
    base_currency_t = st.selectbox("Base currency symbol", st.session_state.all_symbols.keys(),
                                   index=list(st.session_state.all_symbols.keys()).index("GBP"), key="timeseries_sb")
    selected_symbols_list_t = st.multiselect("Currency symbols to limit output currencies",
                                             st.session_state.all_symbols.keys(), default=None, key="timeseries_msb")
    end_date = st.date_input("End date of timeseries",
                             value=datetime.today(),
                             max_value=datetime.today(),
                             help="Must be later than start date, but no more than 365 days.")
    start_date = st.date_input("Start date of timeseries",
                               value=end_date - timedelta(days=1),
                               min_value=end_date - timedelta(days=365),
                               max_value=end_date - timedelta(days=1),
                               help="Must be earlier than end date, but no more than 365 days.")
    if st.button("Finished selection, retrieve timeseries"):
        if base_currency_t and selected_symbols_list_t:
            with st.spinner('Retrieving..'):
                timeseries_dict = retriever.get_timeseries_of_exchange_rates(start_date=start_date.strftime("%Y-%m-%d"),
                                                                             end_date=end_date.strftime("%Y-%m-%d"),
                                                                             base=base_currency_t,
                                                                             symbols=','.join(selected_symbols_list_t))
            for symbol in selected_symbols_list_t:
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
        else:
            st.warning("No target currency symbols have been selected. Please select at least one.")


if __name__ == '__main__':
    run_dashboard()
