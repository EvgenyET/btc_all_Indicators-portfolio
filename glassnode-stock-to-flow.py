import json
import requests
import pandas as pd
import plotly.express as px

# insert your API key here
API_KEY = 'YOUR_API_KEY'

# make API request
res = requests.get('https://api.glassnode.com/v1/metrics/indicators/stock_to_flow_deflection',
    params={'a': 'BTC', 'api_key': API_KEY})

# convert to pandas dataframe
df = pd.read_json(res.text, convert_dates=['t'])

gg=px.line(df, x = 't', y = 'v')

# gg.update_yaxes(type="log")

print(df)

gg.show()