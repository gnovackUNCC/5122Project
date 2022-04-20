import yfinance as yf
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import yahoo_fin.stock_info as si

sidebar = st.sidebar

stocks = st.sidebar.selectbox("Select Stocks", ["AAPL", "MSFT", "GOOG"])
period = sidebar.radio("Range", ("5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"))
interval = sidebar.radio("Interval", ("1d", "5d", "1wk", "1mo", "3mo"))

quarters = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]


if stocks:
    cur_stock = yf.Ticker(stocks)
    chart = cur_stock.history(period=period, interval=interval)
    chart = chart.reset_index()
    earnings = cur_stock.earnings
    earnings = earnings.reset_index()
    #earnings = pd.DataFrame.from_dict(si.get_earnings_history(stocks))
    shares = cur_stock.info["sharesOutstanding"]
    for index, row in earnings.iterrows():
        year = row['Year']
        chart.loc[chart['Date'].dt.year == year, "Earnings"] = row["Earnings"]
    chart["EPS"] = chart["Earnings"] / shares
    chart["P/E"] = chart["Close"] / (chart["EPS"])
    chart["Ticker"] = cur_stock.info["symbol"]
    print(chart.head(10))
    chart_nona = chart.dropna(subset=['Close', 'EPS'])
    rounded = round(chart_nona, 2)[["Date", "Ticker", "Close", "Earnings", "EPS", "P/E"]]

    single_pe = alt.selection_single(on="mouseover")
    single_cost = alt.selection_single(on="mouseover")
    color_pe = alt.condition(single_pe, alt.value("red"), alt.value("gray"))
    color_cost = alt.condition(single_cost, alt.value("blue"), alt.value("gray"))

    interval = alt.selection_interval(encodings=["x"])

    base = alt.Chart(rounded).encode(
        alt.X("Date:T", axis=alt.Axis(title=None))
    ).properties(
        width=800,
        height=400
    )

    range_base = base.properties(
        width=800,
        height=50
    )

    range_pe = range_base.mark_line(color="red").encode(
        y=alt.Y("P/E:Q", axis=alt.Axis(title="P/E"), scale=alt.Scale(zero=False))
    )

    range_cost = range_base.mark_line(color="blue").encode(
        y=alt.Y("Close:Q", axis=alt.Axis(title="Closing Cost ($USD)"))
    )

    chart_base = base.encode(
        alt.X("Date:T", axis=alt.Axis(title=None), scale=alt.Scale(domain=interval.ref()))
    )

    pe_line = chart_base.mark_line().encode(
        y=alt.Y("P/E:Q", axis=alt.Axis(title="P/E"))
    )

    cost_line = chart_base.mark_line().encode(
        y=alt.Y("Close:Q", axis=alt.Axis(title="Closing Cost ($USD)"))
    )

    pe_point = pe_line.mark_point().encode(
        tooltip=["Date:T", "P/E:Q"],
        color=color_pe
    ).add_selection(single_pe)

    cost_point = cost_line.mark_point().encode(
        tooltip=["Date:T", "Close:Q"],
        color=color_cost
    ).add_selection(single_cost)

    pe_chart = alt.layer(pe_line, pe_point)
    cost_chart = alt.layer(cost_line, cost_point)

    final_chart = alt.layer(pe_chart, cost_chart).resolve_scale(y='independent')
    final_range = range_pe.add_selection(interval)


    rounded
    st.write(alt.vconcat(final_chart, final_range))



