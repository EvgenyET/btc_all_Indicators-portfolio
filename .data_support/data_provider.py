"""Public data adapter for the four original chart scripts only.

Sources: Coin Metrics Community API (PriceUSD, SplyCur), OnChainLab SOPR.
Pi Cycle: SMA111 and 2*SMA350.
S2F alternative: trailing-year issuance; model cap = exp(14.6)*SF**3.3,
from https://medium.com/@100trillionUSD/modeling-bitcoins-value-with-scarcity-91fa0fc03e25
This is NOT the Glassnode series. Original chart files remain unchanged.
Remove btc_public_data.pth from .venv/Lib/site-packages to disconnect.
For a rebuilt environment, copy the adjacent btc_public_data.pth to its
Lib/site-packages folder. Keep .venv inside the project folder.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = {'btc.py', 'glassnode-py-cicle.py', 'glassnode-sopr.py',
           'glassnode-stock-to-flow.py'}


def install():
    import json
    import math
    import os
    import time
    import warnings
    from urllib.parse import urlsplit
    import pandas as pd
    import requests

    cache = Path(__file__).resolve().parent / 'cache'
    original_get = requests.get

    def fetch(name, url):
        cache.mkdir(exist_ok=True)
        file = cache / (name + '.json')
        if file.exists() and time.time() - file.stat().st_mtime < 86400:
            return json.loads(file.read_text(encoding='utf-8'))
        print('[data] Loading ' + name + '...', flush=True)
        # Windows may declare an HTTP proxy incorrectly as https://.
        proxies = requests.utils.get_environ_proxies(url)
        if proxies.get('https', '').startswith('https://127.0.0.1:'):
            proxies['https'] = proxies['https'].replace('https://', 'http://', 1)
        try:
            response = original_get(url, proxies=proxies, timeout=(8, 25))
            response.raise_for_status()
            data = response.json()
            rows = data.get('data' if name == 'market' else 'series')
            if not isinstance(rows, list) or not rows:
                raise ValueError('Empty or invalid public data: ' + name)
            if name == 'market' and data.get('next_page_url'):
                raise ValueError('Market history exceeds one page; update adapter')
            temp = file.with_suffix('.tmp')
            temp.write_text(json.dumps(data), encoding='utf-8')
            os.replace(temp, file)
            return data
        except (requests.RequestException, ValueError) as error:
            if file.exists():
                warnings.warn('Source unavailable; using cached ' + name +
                              ' from ' + time.strftime('%Y-%m-%d', time.localtime(file.stat().st_mtime)))
                return json.loads(file.read_text(encoding='utf-8'))
            raise RuntimeError('Could not load public data: ' + name + ' (' + type(error).__name__ + ')') from None

    def market():
        raw = fetch('market', 'https://community-api.coinmetrics.io/v4/timeseries/asset-metrics'
                    '?assets=btc&metrics=PriceUSD,SplyCur&frequency=1d&start_time=2009-01-01&page_size=10000')
        df = pd.DataFrame(raw['data'])
        df.index = pd.to_datetime(df['time'], utc=True)
        df = df[['PriceUSD', 'SplyCur']].apply(pd.to_numeric, errors='coerce').sort_index()
        if df.index.has_duplicates:
            raise ValueError('Duplicate market dates')
        return df.asfreq('D')

    def records(series, column='v'):
        return [{'t': int(date.timestamp()), column: float(value)}
                for date, value in series.dropna().items() if math.isfinite(value) and value > 0]

    def get(url, *args, **kwargs):
        parsed = urlsplit(url)
        payload = None
        if parsed.hostname == 'api.blockchain.info' and parsed.path == '/charts/market-price':
            series = market()['PriceUSD']
            series = series[series.index >= pd.Timestamp.now(tz='UTC') - pd.DateOffset(years=13)]
            payload = {'values': [{'x': r['t'], 'y': r['v']} for r in records(series)]}
        elif parsed.hostname == 'api.glassnode.com':
            metric = parsed.path.rsplit('/', 1)[-1]
            if metric == 'sopr':
                raw = fetch('sopr', 'https://onchainlab.net/data/series/sopr.json')
                series = pd.Series({pd.Timestamp(d, tz='UTC'): v for d, v in raw['series']}, dtype=float).sort_index()
                payload = records(series)
                print('[data] SOPR: OnChainLab (independent provider)', flush=True)
            elif metric == 'pi_cycle_top':
                price = market()['PriceUSD']
                lines = {'111DMA': price.rolling(111, min_periods=111).mean(),
                         '350DMA x 2': price.rolling(350, min_periods=350).mean() * 2}
                payload = [dict(row, series=label) for label, series in lines.items()
                           for row in records(series, 'o')]
            elif metric == 'stock_to_flow_deflection':
                df = market()
                supply = df['SplyCur']
                flow = supply - supply.shift(365)
                sf = (supply / flow).where(flow > 0)
                model_price = math.exp(14.6) * sf.pow(3.3) / supply
                payload = records(df['PriceUSD'] / model_price)
                print('[data] S2F Deflection: alternative PlanB 2019 calculation, not Glassnode.', flush=True)
        if payload is None:
            return original_get(url, *args, **kwargs)
        if not payload:
            raise RuntimeError('No chart data available')
        result = requests.Response()
        result.status_code = 200
        result.encoding = 'utf-8'
        result.headers['Content-Type'] = 'application/json'
        result._content = json.dumps(payload, allow_nan=False).encode('utf-8')
        result.url = url
        return result

    requests.get = get
    if Path(sys.argv[0]).name == 'glassnode-py-cicle.py':
        # Original y='o' cannot plot Glassnode's nested object as two lines.
        # Keep the original file intact and adapt only this chart at runtime.
        import plotly.express as px
        original_line = px.line

        def line(data_frame=None, *args, **kwargs):
            if data_frame is not None and 'series' in data_frame.columns and kwargs.get('y') == 'o':
                kwargs.setdefault('color', 'series')
                kwargs.setdefault('log_y', True)
            return original_line(data_frame, *args, **kwargs)
        px.line = line


if sys.argv and Path(sys.argv[0]).name in TARGETS and Path(sys.argv[0]).resolve().parent == ROOT:
    install()
