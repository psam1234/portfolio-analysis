import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title='Portfolio Analysis', page_icon='📈', layout='wide')
st.title('Portfolio Analysis')
st.caption('Build and explore your investment portfolios online')

if 'portfolios' not in st.session_state:
    st.session_state.portfolios = {}

with st.sidebar:
    st.header('Portfolio setup')
    name = st.text_input('Portfolio name', 'My Portfolio')
    tickers_text = st.text_input('Stock symbols', 'AAPL, MSFT, SAP.DE, SIE.DE')
    start = st.date_input('Start date', pd.Timestamp('2020-01-01'))
    end = st.date_input('End date', pd.Timestamp.today())
    benchmark = st.text_input('Benchmark symbol', '^GSPC')
    analyze = st.button('Analyze portfolio', type='primary')
    st.divider()
    st.subheader('Saved portfolios')
    if st.session_state.portfolios:
        st.write(', '.join(st.session_state.portfolios.keys()))
    else:
        st.caption('No saved portfolios yet')

if analyze:
    tickers = [x.strip().upper() for x in tickers_text.split(',') if x.strip()]
    if len(tickers) < 2:
        st.error('Please enter at least two stock symbols.')
        st.stop()
    with st.spinner('Downloading market data...'):
        prices = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)['Close']
        if isinstance(prices, pd.Series): prices = prices.to_frame(name=tickers[0])
        prices = prices.dropna(how='all').ffill().dropna()
        returns = prices.pct_change().dropna()
    if returns.empty:
        st.error('No data was returned. Check the symbols and dates.')
        st.stop()
    weights = np.repeat(1 / len(tickers), len(tickers))
    portfolio_returns = returns.dot(weights)
    annual_return = portfolio_returns.mean() * 252
    annual_vol = portfolio_returns.std() * np.sqrt(252)
    sharpe = annual_return / annual_vol if annual_vol else np.nan
    st.session_state.portfolios[name] = {'tickers': tickers, 'weights': weights.tolist()}
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Annual return', f'{annual_return:.2%}')
    c2.metric('Annual volatility', f'{annual_vol:.2%}')
    c3.metric('Sharpe ratio', f'{sharpe:.2f}')
    c4.metric('Stocks', len(tickers))
    st.subheader('Portfolio growth')
    growth = (1 + portfolio_returns).cumprod()
    st.line_chart(growth)
    st.subheader('Annualized stock risk and return')
    summary = pd.DataFrame({'Annual return': returns.mean()*252, 'Annual volatility': returns.std()*np.sqrt(252)}).dropna()
    st.dataframe(summary.style.format('{:.2%}'))
    fig = px.scatter(summary.reset_index(), x='Annual volatility', y='Annual return', text='index', title='Risk-return comparison')
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)
    st.info('This first version uses equal weights. Portfolio optimization, multiple benchmarks, CAPM, ESG data, and report exports will be added next.')
else:
    st.info('Choose stock symbols in the sidebar and click Analyze portfolio to begin.')
