import streamlit as st
import pandas as pd
import yfinance as yf
import numerize.numerize as num
from sklearn.linear_model import LinearRegression
import numpy as np

df = pd.read_csv('magicData.csv', index_col = 'ticker', usecols=[1,2,3,4,5,6,7])
df.dropna(axis=0, inplace=True)
df.sort_values('pe', inplace=True)
df['pe_rank'] = df['pe'].rank(na_option='bottom')
df['roa_rank'] = df['roa'].rank(ascending=False, na_option='bottom')
df['rank'] = df['pe_rank'] + df['roa_rank']
df.sort_values('rank', inplace=True)

st.subheader('Top 20 Undervalued Stocks of Good Companies')
st.dataframe(df[['name', 'sub-industry', 'pe', 'roa', 'price']][:20])

ticker = st.selectbox('Select a stock:', df.index)


obj = yf.Ticker(ticker)
data = obj.info

hist = obj.history(start="2020-01-01", end="2022-01-01", interval="1d")

tempdf = hist[['Close']]
tempdf.reset_index(drop=True, inplace=True)
temp = np.array(tempdf.index.array).reshape((-1,1))

reg = LinearRegression().fit(X=temp, y=hist['Close'].to_numpy())
hist['lr'] = reg.predict(temp)

logoCol, nameCol = st.columns(2)

with st.container():
    with nameCol:
        st.metric('',data['shortName'])
        
    with logoCol:
        st.image(data['logo_url'], use_column_width='auto')
    

st.line_chart(hist[['Close', 'lr']])

col1, col2, col3 = st.columns(3)

with st.container():
    with col1:
        st.metric('Current Price', data['currentPrice'])
        st.metric('52-Week High', data['fiftyTwoWeekHigh'])
        st.metric('52-Week Low', data['fiftyTwoWeekLow'])
        
    with col2:
        st.metric('Market Cap', num.numerize(data['marketCap'], 2))
        st.metric('Dividend Yield', data['dividendYield'])
        st.metric('EPS (TTM)', num.numerize(data['trailingEps'], 2))

    with col3:
        st.metric('PE (TTM)', num.numerize(data['trailingPE'], 2))
        st.metric('PB', data['priceToBook'])
        try:
            st.metric('PEG (TTM)', data['trailingPegRatio'])
        except:
            st.metric('PEG (TTM)', 'NA')
        #st.metric('Beta', num.numerize(data['beta'], 2))
        
st.write(data['longBusinessSummary'])
