import requests
import pandas as pd
import plotly.express as px


response = requests.get("https://api.blockchain.info/charts/market-price?timespan=13year&format=json")
data = response.json()
df = pd.DataFrame(data["values"])

'''преобразуем дату UNIX в нормальную дату'''

df['x'] = pd.to_datetime(df['x'],unit='s')

'''преобразуем дату к нужному формату (через / или другой знак):'''

#df['x'] = df['x'].dt.strftime('%m/%d/%Y')

print(df)

gg=px.line(df, x = 'x', y = 'y', template = "plotly_dark")

gg.update_xaxes(title_text="Дата")
gg.update_yaxes(title_text="Цена")


'''преобразуем график в логарифмический'''

gg.update_yaxes(type="log")

'''меняем шаг сетки по оси x и оси y'''

gg.update_yaxes (tick0=0.2, dtick=0.2)
gg.update_xaxes(nticks=50)

'''округляем значения по оси x'''

gg.update_yaxes(tickformat=".1f")

'''форматируем дату'''

# gg.update_xaxes(tickformat="%B<br>%Y")

'''делаем интерактивный курсор'''

gg.update_yaxes(spikecolor='darkgray', spikedash='dot', spikemode='across', spikesnap='cursor', spikethickness=1)
gg.update_xaxes(spikecolor='darkgray', spikedash='dot', spikemode='across', spikesnap='cursor', spikethickness=1)

'''изменяем цвет фона'''

gg.update_layout(plot_bgcolor='white')

'''изменяем цвет сетки'''

gg.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
gg.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')

'''добавляем утолщение и цвет для оси x и оси y (а также зеркально дублируем (mirror=True))'''

gg.update_xaxes(showline=True, linewidth=2, linecolor='black', mirror=True)
gg.update_yaxes(showline=True, linewidth=2, linecolor='black', mirror=True)

gg.show()