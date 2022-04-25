import yfinance as yf
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import yahoo_fin.stock_info as si
from os.path import exists
import numerize.numerize as num

def pe_price_chart(stocks, period, interval):
    success = False
    if stocks:
        cur_stock = yf.Ticker(stocks)
        chart = cur_stock.history(period=period, interval=interval)
        shares = cur_stock.info["sharesOutstanding"]
        try:
            if exists(f'yahoo_fin_earnings_{stocks}.csv'):
                earnings = pd.read_csv(f'yahoo_fin_earnings_{stocks}.csv')
            else:
                earnings = pd.DataFrame.from_dict(si.get_earnings_history(stocks))
            earnings_per_year = {}
            for index, row in earnings.iterrows():
                date_string = str(row['startdatetime'])
                parts = date_string.split("-")
                year = int(parts[0])
                month = int(parts[1])
                quarter = int(month / 3.1)
                if year in earnings_per_year:
                    if quarter in earnings_per_year[year]:
                        earnings_per_year[year][quarter] = row['epsactual']
                if not np.isnan(row['epsactual']):
                    if year in earnings_per_year:
                        earnings_per_year[year][quarter] = row['epsactual']
                    else:
                        earnings_per_year[year] = {quarter: row['epsactual']}
                elif not np.isnan(row['epsestimate']):
                    if year in earnings_per_year:
                        earnings_per_year[year][quarter] = row['epsestimate']
                    else:
                        earnings_per_year[year] = {quarter: row['epsestimate']}
            for y in earnings_per_year:
                cur_year_chart = chart.loc[chart.index.year == y].copy()
                for index, row in cur_year_chart.iterrows():
                    month = index.month
                    quarter = int(month / 3.1)
                    if y-1 in earnings_per_year:
                        if quarter == 0 or (quarter == 1 and quarter not in earnings_per_year):
                            cur_year_chart.loc[index, "EPS"] = earnings_per_year[y][0] + earnings_per_year[y - 1][3] + earnings_per_year[y - 1][2] + earnings_per_year[y - 1][1]
                            cur_year_chart.loc[index, "EPS_q"] = earnings_per_year[y][quarter]
                        elif quarter == 1 or (quarter == 2 and quarter not in earnings_per_year):
                            cur_year_chart.loc[index, "EPS"] = earnings_per_year[y][1] + earnings_per_year[y][0] + earnings_per_year[y - 1][3] + earnings_per_year[y - 1][2]
                            cur_year_chart.loc[index, "EPS_q"] = earnings_per_year[y][quarter]
                        elif quarter == 2 or (quarter == 3 and quarter not in earnings_per_year):
                            cur_year_chart.loc[index, "EPS"] = earnings_per_year[y][2] + earnings_per_year[y][1] + earnings_per_year[y][0] + earnings_per_year[y - 1][3]
                            cur_year_chart.loc[index, "EPS_q"] = earnings_per_year[y][quarter]
                        else:
                            cur_year_chart.loc[index, "EPS"] = earnings_per_year[y][3] + earnings_per_year[y][2] + earnings_per_year[y][1] + earnings_per_year[y][0]
                            cur_year_chart.loc[index, "EPS_q"] = earnings_per_year[y][quarter]
                if cur_year_chart.size != 0:
                    chart = chart.combine_first(cur_year_chart)
                    success = True
            earnings.to_csv(f'yahoo_fin_earnings_{stocks}.csv')
        except IndexError as e:
            print(e)
            chart = chart.reset_index()
            earnings = cur_stock.earnings
            earnings = earnings.reset_index()
            for index, row in earnings.iterrows():
                year = row['Year']
                chart.loc[chart['Date'].dt.year == year, "Earnings"] = row["Earnings"]
                chart["EPS"] = chart["Earnings"] / shares
        if success:
            chart = chart.reset_index()
        chart["P/E"] = chart["Close"] / chart["EPS"]
        chart["Ticker"] = cur_stock.info["symbol"]
        chart_nona = chart.dropna(subset=['Close'])
        rounded = round(chart_nona, 2)[["Date", "Ticker", "Close", "EPS", "EPS_q", "P/E"]]


        single_pe = alt.selection_single(on="mouseover")
        single_cost = alt.selection_single(on="mouseover")
        color_pe = alt.condition(single_pe, alt.value("red"), alt.value("gray"))
        color_cost = alt.condition(single_cost, alt.value("lightblue"), alt.value("gray"))

        interval = alt.selection_interval(encodings=["x"])

        base = alt.Chart(rounded).encode(
            alt.X("Date:T", axis=alt.Axis(title=None))
        ).properties(
            width=1000,
            height=300
        )

        range_base = base.properties(
            height=50
        )

        range_pe = range_base.mark_line().encode(
            y=alt.Y("P/E:Q", axis=alt.Axis(title="P/E"), scale=alt.Scale(zero=False))
        )

        range_cost = range_base.mark_line().encode(
            y=alt.Y("Close:Q", axis=alt.Axis(title="Closing Price ($USD)"))
        )

        chart_base = base.encode(
            alt.X("Date:T", axis=alt.Axis(title=None), scale=alt.Scale(domain=interval.ref()))
        )

        pe_line = chart_base.mark_line(color="red").encode(
            y=alt.Y("P/E:Q", axis=alt.Axis(title="P/E", titleColor="red"), scale=alt.Scale(zero=False))
        )

        cost_line = chart_base.mark_line(color="lightblue").encode(
            y=alt.Y("Close:Q", axis=alt.Axis(title="Closing Price ($USD)", titleColor="lightblue"), scale=alt.Scale(zero=False))
        )

        pe_point = pe_line.mark_point(filled=True, size=45).encode(
            tooltip=["Date:T", "P/E:Q"],
            color=color_pe
        ).add_selection(single_pe)

        cost_point = cost_line.mark_point(filled=True, size=45).encode(
            tooltip=["Date:T", "Close:Q"],
        )

        cost_reg = cost_point.encode(y=alt.Y("Close:Q")).transform_regression("Date", "Close").mark_line()
        reg_text = cost_reg.mark_text(
            align='right',
            baseline='middle',
            dx=-3,
            text="Stock Price Line of Best Fit",

        )

        eps_line = chart_base.mark_line(color="green").encode(y=alt.Y("EPS_q:Q", axis=alt.Axis(title="EPS", titleColor="green")))

        pe_chart = alt.layer(pe_line, pe_point)
        cost_chart = alt.layer(cost_line, cost_point.encode(color=color_cost).add_selection(single_cost), cost_reg, reg_text)

        full_chart = alt.layer(cost_chart, pe_chart).resolve_scale(y='independent')

        cost_and_reg = alt.layer(cost_chart, eps_line).resolve_scale(y='independent')
        final_range = range_cost.add_selection(interval)

        return full_chart, final_range, cost_and_reg

def stock_info(ticker):
    obj = yf.Ticker(ticker)
    data = obj.info

    return data

def scatter_plot(df):
    scatter = alt.Chart(df).mark_image(
        width=50,
        height=50
    ).encode(
        x='pe',
        y='roa',
        color='sector',
        tooltip=['ticker:N', 'name:N', 'pe:Q', 'roa:Q', 'price:Q'],
        url='img',
    ).properties(
        width=1000,
        height=500
    ).interactive()

    return scatter



if __name__ == '__main__':
    scatter_df = pd.read_csv('scatterData.csv')

    df = pd.read_csv('magicData.csv', index_col='ticker', usecols=[1, 2, 3, 4, 5, 6, 7])
    df.dropna(axis=0, inplace=True)
    df.sort_values('pe', inplace=True)
    df['pe_rank'] = df['pe'].rank(na_option='bottom')
    df['roa_rank'] = df['roa'].rank(ascending=False, na_option='bottom')
    df['rank'] = df['pe_rank'] + df['roa_rank']
    df.sort_values('rank', inplace=True)

    available_stocks = si.tickers_sp500()

    st.subheader('Top 20 Undervalued Stocks of Good Companies')
    df = df.rename(columns={'name': 'Name', 'sub-industry': 'Sub-Industry', 'pe':'P/E (Price to Earnings)', 'roa': 'ROA (Return on Assets)', 'price': 'Price'})
    st.dataframe(df[['Name', 'Sub-Industry', 'P/E (Price to Earnings)', 'ROA (Return on Assets)', 'Price']][:20]
                 .style.format(subset=['P/E (Price to Earnings)', 'ROA (Return on Assets)', 'Price'], formatter="{:.2f}"))

    st.write(scatter_plot(scatter_df))

    ticker = st.selectbox('Select a stock:', df.index.sort_values())

    stock_data = stock_info(ticker)

    logoCol, nameCol = st.columns([1, 9])

    with st.container():
        with nameCol:
            st.header(stock_data['shortName'])

        with logoCol:
            st.image(stock_data['logo_url'], use_column_width='auto')



    chart_col1, chart_col2 = st.columns([1, 9])
    with chart_col1:
        period = st.radio("Range", ("5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"))
        interval = st.radio("Interval", ("1d", "1wk", "1mo"))
    with chart_col2:
        final_chart, final_range, cost_reg = pe_price_chart(ticker, period, interval)
        st.write(alt.vconcat(final_chart, cost_reg, final_range))

    col1, col2, col3 = st.columns(3)

    with st.container():
        with col1:
            st.metric('Current Price', stock_data['currentPrice'])
            st.metric('52-Week High', stock_data['fiftyTwoWeekHigh'])
            st.metric('52-Week Low', stock_data['fiftyTwoWeekLow'])

        with col2:
            st.metric('Market Cap', num.numerize(stock_data['marketCap'], 2))
            st.metric('Dividend Yield', stock_data['dividendYield'])
            st.metric('EPS (TTM)', num.numerize(stock_data['trailingEps'], 2))

        with col3:
            st.metric('PE (TTM)', num.numerize(stock_data['trailingPE'], 2))
            st.metric('PB', stock_data['priceToBook'])
            try:
                st.metric('PEG (TTM)', stock_data['trailingPegRatio'])
            except:
                st.metric('PEG (TTM)', 'NA')

    st.write(stock_data['longBusinessSummary'])




