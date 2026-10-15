import difflib
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title='Portfolio Analysis', page_icon='📈', layout='wide')
st.title('Portfolio Analysis')
st.caption('Build and explore your investment portfolios online')

STOCKS = {
    'Apple': 'AAPL', 'Microsoft': 'MSFT', 'Amazon': 'AMZN', 'Alphabet (Google)': 'GOOGL',
    'Meta Platforms': 'META', 'NVIDIA': 'NVDA', 'Tesla': 'TSLA', 'Berkshire Hathaway': 'BRK-B',
    'JPMorgan Chase': 'JPM', 'Visa': 'V', 'Johnson & Johnson': 'JNJ', 'Coca-Cola': 'KO',
    "McDonald's": 'MCD', 'Walmart': 'WMT', 'Netflix': 'NFLX', 'Adobe': 'ADBE',
    'SAP': 'SAP.DE', 'Siemens': 'SIE.DE', 'Allianz': 'ALV.DE', 'BASF': 'BAS.DE',
    'BMW': 'BMW.DE', 'Mercedes-Benz': 'MBG.DE', 'Volkswagen': 'VOW3.DE', 'Airbus': 'AIR.DE',
    'Deutsche Bank': 'DBK.DE', 'Deutsche Telekom': 'DTE.DE', 'Adidas': 'ADS.DE',
    'LVMH': 'MC.PA', 'ASML': 'ASML.AS', 'Novo Nordisk': 'NOVO-B.CO', 'Shell': 'SHEL.L'
}

if 'holdings' not in st.session_state:
    st.session_state.holdings = [{'name': 'Apple', 'weight': 50.0}, {'name': 'Microsoft', 'weight': 50.0}]
if 'portfolios' not in st.session_state:
    st.session_state.portfolios = {}

with st.sidebar:
    st.header('Portfolio setup')
    portfolio_name = st.text_input('Portfolio name', 'My Portfolio')
    st.caption('Search by company name. Suggestions also tolerate small spelling mistakes.')
    for i, holding in enumerate(st.session_state.holdings):
        st.markdown(f'**Stock {i + 1}**')
        search = st.text_input('Type a stock name', value=holding['name'], key=f'search_{i}')
        names = list(STOCKS.keys())
        matches = difflib.get_close_matches(search, names, n=5, cutoff=0.25) if search else names[:5]
        partial = [n for n in names if search.lower() in n.lower()]
        options = list(dict.fromkeys(partial + matches + names))
        selected = st.selectbox('Select stock', options, index=options.index(holding['name']) if holding['name'] in options else 0, key=f'select_{i}')
        holding['name'] = selected
        holding['weight'] = st.number_input('Weight (%)', min_value=0.0, max_value=100.0, value=float(holding['weight']), step=1.0, key=f'weight_{i}')
    add_col, remove_col = st.columns(2)
    with add_col:
        if st.button('Add stock'):
            st.session_state.holdings.append({'name': 'Apple', 'weight': 0.0})
            st.rerun()
    with remove_col:
        if len(st.session_state.holdings) > 2 and st.button('Remove last'):
            st.session_state.holdings.pop()
            st.rerun()
    total_weight = sum(h['weight'] for h in st.session_state.holdings)
    st.metric('Total portfolio weight', f'{total_weight:.1f}%')
    start = st.date_input('Start date', pd.Timestamp('2020-01-01'), min_value=pd.Timestamp('1900-01-01'), max_value=pd.Timestamp.today())
    end = st.date_input('End date', pd.Timestamp.today())
    benchmark = st.text_input('Benchmark symbol', '^GSPC')
    analyze = st.button('Analyze portfolio', type='primary')
    st.divider()
    st.subheader('Saved portfolios')
    st.write(', '.join(st.session_state.portfolios.keys()) if st.session_state.portfolios else 'No saved portfolios yet')

if analyze:
    total_weight = sum(h['weight'] for h in st.session_state.holdings)
    if abs(total_weight - 100.0) > 0.01:
        st.error(f'Weights must add up to exactly 100%. Current total: {total_weight:.1f}%.')
        st.stop()
    if len({h['name'] for h in st.session_state.holdings}) < 2:
        st.error('Please add at least two different stocks.')
        st.stop()
    selected_names = [h['name'] for h in st.session_state.holdings]
    tickers = [STOCKS[n] for n in selected_names]
    weights = np.array([h['weight'] for h in st.session_state.holdings]) / 100
    with st.spinner('Downloading market data...'):
        prices = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)['Close']
        if isinstance(prices, pd.Series): prices = prices.to_frame(name=tickers[0])
        prices = prices.dropna(how='all').ffill().dropna()
        returns = prices.pct_change().dropna()
    if returns.empty:
        st.error('No data was returned. Check the selected stocks and dates.')
        st.stop()
    portfolio_returns = returns.dot(weights)
    annual_return = portfolio_returns.mean() * 252
    annual_vol = portfolio_returns.std() * np.sqrt(252)
    sharpe = annual_return / annual_vol if annual_vol else np.nan
    st.session_state.portfolios[portfolio_name] = {'stocks': selected_names, 'weights': weights.tolist()}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Annual return', f'{annual_return:.2%}')
    c2.metric('Annual volatility', f'{annual_vol:.2%}')
    c3.metric('Sharpe ratio', f'{sharpe:.2f}')
    c4.metric('Stocks', len(tickers))
    st.subheader('Portfolio composition')
    st.dataframe(pd.DataFrame({'Stock': selected_names, 'Ticker': tickers, 'Weight': weights}).style.format({'Weight': '{:.1%}'}), hide_index=True)
    st.subheader('Portfolio growth')
    st.line_chart((1 + portfolio_returns).cumprod())
    st.subheader('Annualized stock risk and return')
    summary = pd.DataFrame({'Annual return': returns.mean() * 252, 'Annual volatility': returns.std() * np.sqrt(252)}).dropna()
    st.dataframe(summary.style.format('{:.2%}'))
    chart_data = summary.reset_index().rename(columns={'index': 'Ticker'})
    fig = px.scatter(chart_data, x='Annual volatility', y='Annual return', text='Ticker', title='Risk-return comparison')
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('Add stocks, set their weights to total 100%, then click Analyze portfolio.')
