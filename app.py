import difflib
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title='Portfolio Analysis', page_icon='📈', layout='wide')
st.title('Portfolio Analysis')
st.caption('Build and explore your investment portfolios online')

PAGES = [
    'Portfolio Builder',
    'Portfolio Overview',
    'Historical Data',
    'Performance Analysis',
    'Risk & KPI Analysis',
    'Stock Details',
    'Saved Portfolios'
]
page = st.sidebar.radio('Navigate', PAGES, index=1)

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
    st.session_state.holdings = [{'name': 'Apple', 'weight': 100.0}]
if 'portfolios' not in st.session_state:
    st.session_state.portfolios = {}
if 'active_portfolio_name' not in st.session_state:
    st.session_state.active_portfolio_name = 'My Portfolio'
if 'active_start' not in st.session_state:
    st.session_state.active_start = pd.Timestamp('2020-01-01').date()
if 'active_end' not in st.session_state:
    st.session_state.active_end = pd.Timestamp.today().date()
if 'active_benchmark' not in st.session_state:
    st.session_state.active_benchmark = '^GSPC'

with st.sidebar:
    st.header('Portfolio setup')
    portfolio_name = st.text_input('Portfolio name', key='active_portfolio_name')
    st.caption('Select a company from the list. Add more stocks when needed.')
    for i, holding in enumerate(st.session_state.holdings):
        st.markdown(f'**Stock {i + 1}**')
        names = list(STOCKS.keys())
        selected = st.selectbox('Select stock', names, index=names.index(holding['name']) if holding['name'] in names else 0, key=f'select_{i}')
        holding['name'] = selected
        holding['weight'] = st.number_input('Weight (%)', min_value=0.0, max_value=100.0, value=float(holding['weight']), step=1.0, key=f'weight_{i}')
    add_col, remove_col = st.columns([2, 1])
    with add_col:
        if st.button('Add another stock'):
            st.session_state.holdings.append({'name': 'Apple', 'weight': 0.0})
            st.rerun()
    with remove_col:
        if len(st.session_state.holdings) > 2 and st.button('Remove last'):
            st.session_state.holdings.pop()
            st.rerun()
    total_weight = sum(h['weight'] for h in st.session_state.holdings)
    st.metric('Total portfolio weight', f'{total_weight:.1f}%')
    start = st.date_input('Start date', min_value=pd.Timestamp('1900-01-01'), max_value=pd.Timestamp.today(), key='active_start')
    end = st.date_input('End date', min_value=pd.Timestamp('1900-01-01'), max_value=pd.Timestamp.today(), key='active_end')
    benchmark = st.text_input('Benchmark symbol', key='active_benchmark')
    analyze = st.button('Analyze portfolio', type='primary')
    st.divider()
    st.subheader('Saved portfolios')
    if st.session_state.portfolios:
        st.write(', '.join(st.session_state.portfolios.keys()))
    else:
        st.write('No saved portfolios yet')

if page == 'Portfolio Builder':
    st.info('Use the sidebar controls to build your portfolio, then choose Portfolio Overview to run the analysis.')
elif page not in ('Portfolio Overview', 'Performance Analysis', 'Historical Data', 'Risk & KPI Analysis', 'Stock Details'):
    st.info(f'{page} will be added in the next step.')

if page == 'Portfolio Overview' and analyze:
    total_weight = sum(h['weight'] for h in st.session_state.holdings)
    if abs(total_weight - 100.0) > 0.01:
        st.error(f'Weights must add up to exactly 100%. Current total: {total_weight:.1f}%.')
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
    if portfolio_name.strip() in st.session_state.portfolios:
        st.warning(f'A portfolio named {portfolio_name.strip()} already exists. Choose a different name to avoid overwriting it.')
        st.stop()
    st.session_state.portfolios[portfolio_name.strip()] = {'stocks': selected_names, 'weights': weights.tolist(), 'benchmark': benchmark, 'start_date': str(start), 'end_date': str(end)}
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
elif page == 'Portfolio Overview':
    st.info('Add stocks, set their weights to total 100%, then click Analyze portfolio.')
elif page == 'Performance Analysis':
    st.subheader('Performance Analysis')
    st.caption('Compare your portfolio performance with the selected benchmark over time.')
    selected_names = [h['name'] for h in st.session_state.holdings]
    tickers = [STOCKS[n] for n in selected_names]
    weights = np.array([h['weight'] for h in st.session_state.holdings]) / 100
    with st.spinner('Downloading performance data...'):
        raw = yf.download(tickers + [benchmark], start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        st.warning('No performance data was returned for the selected portfolio and date range.')
    else:
        close = raw['Adj Close'] if 'Adj Close' in raw else raw['Close']
        if isinstance(close, pd.Series):
            close = close.to_frame(name=(tickers + [benchmark])[0])
        close = close.dropna(how='all').ffill().dropna(how='all')
        portfolio_prices = close[[t for t in tickers if t in close.columns]]
        missing_stocks = [n for n, t in zip(selected_names, tickers) if t not in portfolio_prices.columns]
        if missing_stocks:
            st.warning('No benchmark-period data was available for: ' + ', '.join(missing_stocks))
        usable = [t for t in tickers if t in portfolio_prices.columns]
        if not usable:
            st.error('No usable stock price data is available.')
        else:
            usable_weights = np.array([weights[tickers.index(t)] for t in usable])
            stock_returns = portfolio_prices[usable].pct_change()
            portfolio_returns = stock_returns.fillna(0).dot(usable_weights).rename('Portfolio')
            benchmark_series = close[benchmark].dropna() if benchmark in close.columns else pd.Series(dtype=float)
            if benchmark_series.empty:
                st.warning(f'Benchmark data for {benchmark} was not available. Portfolio analysis is shown without benchmark comparison.')
                benchmark_returns = pd.Series(index=portfolio_returns.index, dtype=float, name='Benchmark')
            else:
                benchmark_returns = benchmark_series.pct_change().reindex(portfolio_returns.index).rename('Benchmark')
            performance = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna(subset=['Portfolio'])
            data_start = performance.index.min().date()
            data_end = performance.index.max().date()
            f1, f2 = st.columns(2)
            with f1:
                perf_start = st.date_input('Analysis start date', data_start, min_value=data_start, max_value=data_end, key='performance_start')
            with f2:
                perf_end = st.date_input('Analysis end date', data_end, min_value=data_start, max_value=data_end, key='performance_end')
            if perf_start > perf_end:
                st.error('Analysis start date must be before or equal to the end date.')
                st.stop()
            period = performance.loc[(performance.index.date >= perf_start) & (performance.index.date <= perf_end)].copy()
            if period.empty:
                st.warning('No data is available for the selected analysis dates.')
            else:
                portfolio_total = (1 + period['Portfolio']).prod() - 1
                benchmark_total = (1 + period['Benchmark']).prod() - 1 if period['Benchmark'].notna().any() else np.nan
                annualized = (1 + portfolio_total) ** (252 / max(len(period), 1)) - 1
                difference = portfolio_total - benchmark_total if pd.notna(benchmark_total) else np.nan
                c1, c2, c3, c4 = st.columns(4)
                c1.metric('Total portfolio return', f'{portfolio_total:.2%}')
                c2.metric('Annualized return', f'{annualized:.2%}')
                c3.metric('Benchmark return', f'{benchmark_total:.2%}' if pd.notna(benchmark_total) else 'Unavailable')
                c4.metric('Difference vs benchmark', f'{difference:.2%}' if pd.notna(difference) else 'Unavailable')
                if pd.notna(difference):
                    st.success('Outperformed the benchmark.' if difference >= 0 else 'Underperformed the benchmark.')
                st.info('Returns show how much the portfolio changed during the selected period. Annualized return estimates the equivalent one-year rate.')
                cumulative = pd.DataFrame(index=period.index)
                cumulative['Portfolio'] = (1 + period['Portfolio']).cumprod()
                if period['Benchmark'].notna().any():
                    cumulative['Benchmark'] = (1 + period['Benchmark'].fillna(0)).cumprod()
                st.markdown('### Cumulative return')
                st.line_chart((cumulative - 1) * 100)
                st.markdown('### Portfolio versus benchmark growth')
                st.line_chart(cumulative * 100)
                monthly = period[['Portfolio', 'Benchmark']].resample('ME').apply(lambda x: (1 + x).prod() - 1)
                monthly.index = monthly.index.to_period('M').astype(str)
                yearly = period[['Portfolio', 'Benchmark']].resample('YE').apply(lambda x: (1 + x).prod() - 1)
                yearly.index = yearly.index.year
                st.markdown('### Monthly returns')
                st.dataframe(monthly.style.format('{:.2%}'), use_container_width=True)
                st.download_button('Download monthly returns CSV', monthly.to_csv().encode('utf-8'), 'monthly_returns.csv', 'text/csv')
                st.markdown('### Yearly returns')
                st.dataframe(yearly.style.format('{:.2%}'), use_container_width=True)
                st.download_button('Download yearly returns CSV', yearly.to_csv().encode('utf-8'), 'yearly_returns.csv', 'text/csv')
                rolling = pd.DataFrame(index=period.index)
                rolling['Portfolio 30-day'] = (1 + period['Portfolio']).rolling(30).apply(np.prod, raw=True) - 1
                rolling['Portfolio 1-year'] = (1 + period['Portfolio']).rolling(252).apply(np.prod, raw=True) - 1
                st.markdown('### Rolling returns')
                st.line_chart(rolling * 100)
                st.download_button('Download daily returns CSV', period.to_csv().encode('utf-8'), 'daily_returns.csv', 'text/csv')
                st.download_button('Download portfolio versus benchmark CSV', cumulative.to_csv().encode('utf-8'), 'portfolio_vs_benchmark.csv', 'text/csv')

elif page == 'Risk & KPI Analysis':
    st.subheader('Risk & KPI Analysis')
    st.caption("Understand the portfolio's risk using historical daily returns.")
    selected_names = [h['name'] for h in st.session_state.holdings]
    tickers = [STOCKS[n] for n in selected_names]
    weights = np.array([h['weight'] for h in st.session_state.holdings]) / 100
    with st.spinner('Downloading risk data...'):
        raw = yf.download(tickers + [benchmark], start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        st.warning('No risk data was returned for the selected portfolio and date range.')
    else:
        close = raw['Adj Close'] if 'Adj Close' in raw else raw['Close']
        if isinstance(close, pd.Series): close = close.to_frame(name=(tickers + [benchmark])[0])
        close = close.dropna(how='all').ffill().dropna(how='all')
        usable = [t for t in tickers if t in close.columns and close[t].notna().any()]
        missing = [n for n, t in zip(selected_names, tickers) if t not in usable]
        if missing: st.warning('No data was available for: ' + ', '.join(missing))
        if not usable:
            st.error('No usable stock data is available.')
        else:
            stock_returns = close[usable].pct_change().dropna(how='all')
            usable_weights = np.array([weights[tickers.index(t)] for t in usable])
            portfolio_returns = stock_returns[usable].fillna(0).dot(usable_weights).dropna()
            benchmark_returns = close[benchmark].pct_change().reindex(portfolio_returns.index) if benchmark in close.columns else pd.Series(dtype=float)
            data_start, data_end = portfolio_returns.index.min().date(), portfolio_returns.index.max().date()
            r1, r2 = st.columns(2)
            with r1: risk_start = st.date_input('Risk start date', data_start, min_value=data_start, max_value=data_end, key='risk_start')
            with r2: risk_end = st.date_input('Risk end date', data_end, min_value=data_start, max_value=data_end, key='risk_end')
            if risk_start > risk_end:
                st.error('Risk start date must be before or equal to the end date.')
                st.stop()
            mask = (portfolio_returns.index.date >= risk_start) & (portfolio_returns.index.date <= risk_end)
            pr = portfolio_returns.loc[mask]
            br = benchmark_returns.loc[mask].dropna() if not benchmark_returns.empty else pd.Series(dtype=float)
            if pr.empty:
                st.warning('No data is available for the selected risk dates.')
            else:
                ann = 252
                vol = pr.std() * np.sqrt(ann)
                downside = pr[pr < 0].std() * np.sqrt(ann)
                sharpe = (pr.mean() * ann) / vol if vol else np.nan
                sortino = (pr.mean() * ann) / downside if downside and not np.isnan(downside) else np.nan
                wealth = (1 + pr).cumprod()
                drawdown = wealth / wealth.cummax() - 1
                max_dd = drawdown.min()
                annual_return = (1 + pr).prod() ** (ann / len(pr)) - 1
                calmar = annual_return / abs(max_dd) if max_dd else np.nan
                var95 = pr.quantile(0.05)
                cvar95 = pr[pr <= var95].mean()
                beta = alpha = np.nan
                if len(br) > 1:
                    aligned = pd.concat([pr.rename('p'), br.rename('b')], axis=1).dropna()
                    if len(aligned) > 1 and aligned['b'].var() != 0:
                        beta = aligned['p'].cov(aligned['b']) / aligned['b'].var()
                        alpha = (aligned['p'].mean() - beta * aligned['b'].mean()) * ann
                diversification = 1 - abs(weights[:len(usable)].dot(stock_returns[usable].corr().fillna(0).values).dot(weights[:len(usable)])) if len(usable) > 1 else 0.0
                metrics = pd.DataFrame({'Value': [vol, sharpe, sortino, beta, alpha, max_dd, calmar, var95, cvar95, downside, diversification]}, index=['Annualized volatility','Sharpe ratio','Sortino ratio','Beta','Alpha','Maximum drawdown','Calmar ratio','VaR (95%)','CVaR (95%)','Downside deviation','Diversification score'])
                st.dataframe(metrics.style.format('{:.2%}'), use_container_width=True)
                st.caption('Volatility measures fluctuation. Sharpe and Sortino compare return with risk. Beta measures sensitivity to the benchmark. Alpha is estimated excess return. Drawdown is the fall from a previous peak. VaR and CVaR estimate bad-day losses. The diversification score is a simple correlation-based indicator.')
                st.markdown('### Drawdown over time')
                st.line_chart(drawdown * 100)
                st.markdown('### Portfolio versus benchmark risk comparison')
                comparison = pd.DataFrame({'Portfolio': pr})
                if not br.empty: comparison['Benchmark'] = br
                st.dataframe(comparison.describe().T, use_container_width=True)
                st.markdown('### Correlation matrix')
                st.dataframe(stock_returns[usable].corr().style.format('{:.2f}'), use_container_width=True)

elif page == 'Stock Details':
    st.subheader('Stock Details')
    st.caption('Explore one selected stock in detail using historical market data.')
    selected_names = [h['name'] for h in st.session_state.holdings]
    stock_name = st.selectbox('Select a stock', selected_names, key='detail_stock')
    ticker = STOCKS[stock_name]
    with st.spinner('Downloading stock data...'):
        stock_raw = yf.download([ticker, benchmark], start=start, end=end, auto_adjust=False, progress=False)
    if stock_raw.empty:
        st.warning(f'No data was returned for {stock_name} ({ticker}) in the selected period.')
    else:
        stock_close = stock_raw['Adj Close'] if 'Adj Close' in stock_raw else stock_raw['Close']
        stock_volume = stock_raw['Volume'] if 'Volume' in stock_raw else pd.DataFrame(index=stock_close.index)
        if isinstance(stock_close, pd.Series): stock_close = stock_close.to_frame(name=ticker)
        if isinstance(stock_volume, pd.Series): stock_volume = stock_volume.to_frame(name=ticker)
        if ticker not in stock_close.columns or stock_close[ticker].dropna().empty:
            st.warning(f'No historical data was available for {stock_name} ({ticker}) in the selected period.')
        else:
            prices = stock_close[[ticker]].dropna()
            returns = prices[ticker].pct_change().dropna().rename('Daily return')
            volumes = stock_volume[[ticker]].reindex(prices.index).dropna(how='all') if ticker in stock_volume.columns else pd.DataFrame(index=prices.index)
            detail_start, detail_end = prices.index.min().date(), prices.index.max().date()
            d1, d2 = st.columns(2)
            with d1: detail_from = st.date_input('Stock start date', detail_start, min_value=detail_start, max_value=detail_end, key='detail_start')
            with d2: detail_to = st.date_input('Stock end date', detail_end, min_value=detail_start, max_value=detail_end, key='detail_end')
            if detail_from > detail_to:
                st.error('Stock start date must be before or equal to the end date.')
                st.stop()
            price_period = prices.loc[(prices.index.date >= detail_from) & (prices.index.date <= detail_to)]
            return_period = returns.loc[(returns.index.date >= detail_from) & (returns.index.date <= detail_to)]
            volume_period = volumes.loc[(volumes.index.date >= detail_from) & (volumes.index.date <= detail_to)]
            bench = stock_close[benchmark].pct_change().reindex(return_period.index).dropna() if benchmark in stock_close.columns else pd.Series(dtype=float)
            ann = 252
            annual_return = (1 + return_period).prod() ** (ann / max(len(return_period), 1)) - 1 if not return_period.empty else np.nan
            annual_vol = return_period.std() * np.sqrt(ann) if not return_period.empty else np.nan
            sharpe = (return_period.mean() * ann) / annual_vol if annual_vol and not np.isnan(annual_vol) else np.nan
            wealth = (1 + return_period).cumprod() if not return_period.empty else pd.Series(dtype=float)
            drawdown = wealth / wealth.cummax() - 1 if not wealth.empty else pd.Series(dtype=float)
            max_dd = drawdown.min() if not drawdown.empty else np.nan
            beta = np.nan
            if not bench.empty:
                aligned = pd.concat([return_period.rename('stock'), bench.rename('benchmark')], axis=1).dropna()
                if len(aligned) > 1 and aligned['benchmark'].var() != 0:
                    beta = aligned['stock'].cov(aligned['benchmark']) / aligned['benchmark'].var()
            st.markdown(f'### {stock_name} ({ticker})')
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Annual return', f'{annual_return:.2%}' if pd.notna(annual_return) else 'Unavailable')
            c2.metric('Annualized volatility', f'{annual_vol:.2%}' if pd.notna(annual_vol) else 'Unavailable')
            c3.metric('Beta vs benchmark', f'{beta:.2f}' if pd.notna(beta) else 'Unavailable')
            c4.metric('Sharpe ratio', f'{sharpe:.2f}' if pd.notna(sharpe) else 'Unavailable')
            c5, c6, c7, c8 = st.columns(4)
            c5.metric('Maximum drawdown', f'{max_dd:.2%}' if pd.notna(max_dd) else 'Unavailable')
            c6.metric('Best day', f'{return_period.max():.2%}' if not return_period.empty else 'Unavailable')
            c7.metric('Worst day', f'{return_period.min():.2%}' if not return_period.empty else 'Unavailable')
            c8.metric('Ticker', ticker)
            if bench.empty:
                st.warning(f'Benchmark data for {benchmark} was unavailable. Beta cannot be calculated.')
            st.info('Annual return estimates the yearly growth rate. Volatility measures price fluctuation. Beta shows sensitivity to the benchmark. Sharpe compares return with risk. Maximum drawdown is the largest fall from a previous peak.')
            st.markdown('### Historical adjusted price')
            st.line_chart(price_period)
            st.markdown('### Daily returns')
            st.line_chart(return_period * 100)
            st.markdown('### Historical price data')
            st.dataframe(price_period.style.format('{:.2f}'), use_container_width=True)
            st.download_button('Download historical prices CSV', price_period.to_csv().encode('utf-8'), 'stock_prices.csv', 'text/csv')
            st.markdown('### Daily return data')
            return_table = return_period.to_frame()
            st.dataframe(return_table.style.format('{:.2%}'), use_container_width=True)
            st.download_button('Download daily returns CSV', return_table.to_csv().encode('utf-8'), 'stock_daily_returns.csv', 'text/csv')
            st.markdown('### Trading volume')
            if volume_period.empty:
                st.info('Trading volume is not available for this data source and period.')
            else:
                st.dataframe(volume_period, use_container_width=True)
                st.download_button('Download trading volume CSV', volume_period.to_csv().encode('utf-8'), 'stock_volume.csv', 'text/csv')
            st.markdown('### Dividend information')
            try:
                dividends = yf.Ticker(ticker).dividends
                dividends = dividends.loc[(dividends.index.date >= detail_from) & (dividends.index.date <= detail_to)]
            except Exception:
                dividends = pd.Series(dtype=float)
            if dividends.empty:
                st.info('No dividend information was provided for this stock and period.')
            else:
                dividend_table = dividends.rename('Dividend').to_frame()
                st.dataframe(dividend_table, use_container_width=True)
                st.download_button('Download dividend data CSV', dividend_table.to_csv().encode('utf-8'), 'stock_dividends.csv', 'text/csv')

elif page == 'Saved Portfolios':
    st.subheader('Saved Portfolios')
    st.caption('Load, review, and manage portfolios saved in this browser session.')
    if not st.session_state.portfolios:
        st.info('No saved portfolios yet. Build a portfolio and click Analyze portfolio to save it.')
    else:
        portfolio_names = list(st.session_state.portfolios.keys())
        selected_saved = st.selectbox('Select a saved portfolio', portfolio_names, key='saved_portfolio_select')
        saved = st.session_state.portfolios[selected_saved]
        saved_stocks = saved.get('stocks', [])
        saved_weights = saved.get('weights', [])
        saved_tickers = [STOCKS.get(name, '') for name in saved_stocks]
        st.markdown(f'### {selected_saved}')
        details = pd.DataFrame({'Stock': saved_stocks, 'Ticker': saved_tickers, 'Weight': saved_weights})
        if not details.empty:
            st.dataframe(details.style.format({'Weight': '{:.1%}'}), hide_index=True, use_container_width=True)
        d1, d2, d3 = st.columns(3)
        d1.metric('Benchmark', saved.get('benchmark', '^GSPC'))
        d2.metric('Start date', str(saved.get('start_date', 'Not recorded')))
        d3.metric('End date', str(saved.get('end_date', 'Not recorded')))
        if st.button('Load selected portfolio', type='primary'):
            st.session_state.holdings = [{'name': name, 'weight': float(weight) * 100 if float(weight) <= 1 else float(weight)} for name, weight in zip(saved_stocks, saved_weights)]
            st.session_state.active_portfolio_name = selected_saved
            st.session_state.active_benchmark = saved.get('benchmark', '^GSPC')
            st.session_state.active_start = pd.Timestamp(saved.get('start_date', '2020-01-01')).date()
            st.session_state.active_end = pd.Timestamp(saved.get('end_date', pd.Timestamp.today())).date()
            st.success(f'Loaded {selected_saved}. Go to Portfolio Overview and click Analyze portfolio.')
            st.rerun()
        st.divider()
        st.markdown('### Delete portfolio')
        delete_confirm = st.checkbox(f'I understand that deleting {selected_saved} cannot be undone.', key='delete_confirm')
        if st.button('Delete selected portfolio', disabled=not delete_confirm):
            del st.session_state.portfolios[selected_saved]
            st.success(f'Deleted {selected_saved}.')
            st.rerun()
        st.caption('Saved portfolios use Streamlit session state in the free setup, so they may reset when the app session restarts.')

elif page == 'Historical Data':
    st.subheader('Historical Data')
    selected_names = [h['name'] for h in st.session_state.holdings]
    tickers = [STOCKS[n] for n in selected_names]
    weights = np.array([h['weight'] for h in st.session_state.holdings]) / 100
    with st.spinner('Downloading historical data...'):
        raw = yf.download(tickers, start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        st.warning('No historical data was returned for this portfolio and date range.')
    else:
        close = raw['Adj Close'] if 'Adj Close' in raw else raw['Close']
        volume = raw['Volume'] if 'Volume' in raw else pd.DataFrame(index=close.index)
        if isinstance(close, pd.Series): close = close.to_frame(name=tickers[0])
        if isinstance(volume, pd.Series): volume = volume.to_frame(name=tickers[0])
        close.columns = tickers[:len(close.columns)]
        volume.columns = tickers[:len(volume.columns)]
        close = close.dropna(how='all').ffill().dropna(how='all')
        missing = [name for name, ticker in zip(selected_names, tickers) if ticker not in close.columns or close[ticker].dropna().empty]
        if missing:
            st.warning('No data was available for: ' + ', '.join(missing))
        if close.empty:
            st.error('No usable price data is available for the selected stocks.')
        else:
            returns = close.pct_change().dropna(how='all')
            usable = [ticker for ticker in tickers if ticker in returns.columns]
            usable_weights = np.array([weights[tickers.index(ticker)] for ticker in usable])
            portfolio_returns = returns[usable].fillna(0).dot(usable_weights)
            portfolio_value = (1 + portfolio_returns).cumprod() * 100
            min_date = close.index.min().date()
            max_date = close.index.max().date()
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                data_start = st.date_input('Data start date', min_date, min_value=min_date, max_value=max_date, key='historical_start')
            with filter_col2:
                data_end = st.date_input('Data end date', max_date, min_value=min_date, max_value=max_date, key='historical_end')
            if data_start > data_end:
                st.error('Data start date must be before or equal to data end date.')
                st.stop()
            search_filter = st.text_input('Filter table columns or stock names', key='historical_filter')
            mask = (close.index.date >= data_start) & (close.index.date <= data_end)
            filtered_close = close.loc[mask]
            filtered_returns = returns.loc[returns.index.map(lambda x: data_start <= x.date() <= data_end)]
            filtered_portfolio_returns = portfolio_returns.loc[portfolio_returns.index.map(lambda x: data_start <= x.date() <= data_end)]
            filtered_portfolio_value = portfolio_value.loc[portfolio_value.index.map(lambda x: data_start <= x.date() <= data_end)]
            filtered_volume = volume.loc[volume.index.map(lambda x: data_start <= x.date() <= data_end)]
            if search_filter:
                wanted = [c for c in filtered_close.columns if search_filter.lower() in str(c).lower()]
                filtered_close = filtered_close[wanted]
                filtered_returns = filtered_returns[[c for c in filtered_returns.columns if c in wanted]]
                filtered_volume = filtered_volume[[c for c in filtered_volume.columns if c in wanted]]
            def show_download(label, frame, key):
                st.download_button(label, frame.to_csv().encode('utf-8'), file_name=key + '.csv', mime='text/csv', key='download_' + key)
            st.markdown('### Adjusted closing prices')
            st.dataframe(filtered_close, use_container_width=True)
            show_download('Download adjusted prices CSV', filtered_close, 'adjusted_prices')
            st.markdown('### Daily stock returns')
            st.dataframe(filtered_returns.style.format('{:.2%}'), use_container_width=True)
            show_download('Download stock returns CSV', filtered_returns, 'stock_returns')
            st.markdown('### Portfolio daily returns')
            portfolio_returns_table = filtered_portfolio_returns.rename('Portfolio daily return').to_frame()
            st.dataframe(portfolio_returns_table.style.format('{:.2%}'), use_container_width=True)
            show_download('Download portfolio returns CSV', portfolio_returns_table, 'portfolio_returns')
            st.markdown('### Portfolio value by date')
            portfolio_value_table = filtered_portfolio_value.rename('Portfolio value').to_frame()
            st.dataframe(portfolio_value_table.style.format('{:.2f}'), use_container_width=True)
            show_download('Download portfolio value CSV', portfolio_value_table, 'portfolio_value')
            st.markdown('### Trading volume')
            st.dataframe(filtered_volume, use_container_width=True)
            show_download('Download trading volume CSV', filtered_volume, 'trading_volume')
