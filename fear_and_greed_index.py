import requests
import pandas as pd
import plotly.express as px
import openpyxl
import json
import plotly.io as pio
import plotly.graph_objects as go
import pandas_ta as ta
from plotly.subplots import make_subplots


'''берём данные API по Биткоину с сайта blockchain.com:'''

response2 = requests.get("https://api.blockchain.info/charts/market-price?timespan=13year&start=2018-02-01&format=json")
data = response2.json()
df2 = pd.DataFrame(data["values"])

'''преобразуем дату UNIX в нормальную дату'''

df2['x'] = pd.to_datetime(df2['x'],unit='s')

btc=px.line(df2, x = 'x', y = 'y')

'''преобразуем график в логарифмический'''

# btc.update_yaxes(type="log")

'''добавляем легенду BTC'''

btc['data'][0]['showlegend']=True
btc['data'][0]['name']='BTC'

'''берём данные API с сайта индекса страха и жадности:'''

response = requests.get("https://api.alternative.me/fng/?limit=10000&format=json&date_format=us")

data = response.json()
df = pd.DataFrame(data["data"])

'''сортируем по индексу первого столбца в обратном порядке:'''

sorted_df = df.sort_index(ascending = False)

'''записываем файл excel:'''

writer = pd.ExcelWriter('output1.xlsx')
sorted_df.to_excel(writer)
writer._save()

'''задаём тему графику:'''

pio.templates["plotly_dark_custom"] = pio.templates["plotly_white"]
pio.templates.default = "plotly_dark_custom"

'''создаём график из таблицы'''

df = pd.read_excel('output1.xlsx')

'''меняем значения x и y в таблице'''

df.rename(columns = {'timestamp':'Дата'}, inplace = True)
df.rename(columns = {'value':'Значение индекса'}, inplace = True)

'''преобразуем дату сначала к формату даты в pandas, а потом если надо к нужному формату (через / или другой знак):'''

df['Дата'] = pd.to_datetime(df.Дата)
# df['Дата'] = df['Дата'].dt.strftime('%m/%d/%Y')

gg=px.line(df, x = 'Дата', y = 'Значение индекса')

'''задаём цвет и толщину линии индекса страха и жадности'''

gg.update_traces(line=dict(color="#B8B8B8", width=1))

'''добавляем легенду Индекс'''

gg['data'][0]['showlegend']=True
gg['data'][0]['name']='Индекс'

'''создаём скользящую ma100 (в таблицу добавляется новый столбец) и сглаживаем её (SMA)'''

df['Значение индекса2'] = df['Значение индекса'].rolling(100).mean()
df['Значение индекса2'] = df['Значение индекса2'].rolling(20).mean()
gg2=px.line(df, x = 'Дата', y = 'Значение индекса2')

'''задаём цвет и толщину кривой линии (скользящей стредней)'''

gg2.update_traces(line=dict(color="blue", width=2))

'''добавляем легенду MA100'''

gg2['data'][0]['showlegend']=True
gg2['data'][0]['name']='MA100'

'''создаём скользящую ma200 (в таблицу добавляется новый столбец) и сглаживаем её (SMA)'''

df['Значение индекса3'] = df['Значение индекса'].rolling(180).mean()
df['Значение индекса3'] = df['Значение индекса3'].rolling(20).mean()
gg3=px.line(df, x = 'Дата', y = 'Значение индекса3')

'''задаём цвет и толщину кривой линии (скользящей стредней)'''

gg3.update_traces(line=dict(color="red", width=2))

'''добавляем легенду MA180'''

gg3['data'][0]['showlegend']=True
gg3['data'][0]['name']='MA180'

'''разбиваем экран на два поля с графиками + добавляем заголовки:'''

gg5 = make_subplots(rows=2, cols=1, vertical_spacing=0.12, subplot_titles=(False, "Индекс страха и жадности"))
gg5.add_trace(btc['data'][0], row=1, col=1)
gg5.add_trace(gg['data'][0], row=2, col=1)
gg5.add_trace(gg2['data'][0], row=2, col=1)
gg5.add_trace(gg3['data'][0], row=2, col=1)

'''добавляем подписи осей x и y на график Биткоина'''

# gg5.update_xaxes(title_text="Дата", row=1, col=1)
gg5.update_yaxes(title_text="Цена", row=1, col=1)

'''меняем шаг сетки по оси x и оси y на графике Биткоина'''

gg5.update_yaxes (tick0=0.1, dtick=0.1, row=1, col=1)
gg5.update_xaxes(nticks=50, row=1, col=1)

'''округляем значения по оси x на графике Биткоина'''

gg5.update_yaxes(tickformat=".0f", row=1, col=1)

'''добавляем подписи осей x и y на график индекса страха и жадности'''

gg5.update_xaxes(title_text="Дата", row=2, col=1)
gg5.update_yaxes(title_text="Значение индекса", row=2, col=1)

'''меняем шаг сетки по оси x и оси y на графике Биткоина'''

gg5.update_yaxes (tick0=10, dtick=10, row=2, col=1)
gg5.update_xaxes(nticks=50, row=2, col=1)

'''делаем первый график логарифмическим:'''

gg5.update_yaxes(type="log", row=1, col=1)

'''делаем интерактивный курсор и указываем к нему все параметры'''

gg5.update_yaxes(spikecolor='darkgray', spikedash='dot', spikemode='across', spikesnap='cursor', spikethickness=1)
gg5.update_xaxes(spikecolor='darkgray', spikedash='dot', spikemode='across', spikesnap='cursor', spikethickness=1)

'''привязываем курсор по оси x к обоим полям (subplots)'''

gg5.update_traces(xaxis="x2")

'''принудительно добавляем под график Биткоина ось x (и указываем данные оси y), так как после предыдущего изменения
данные под осью x исчезли. Также скрываем дополнительную появившуюся легенду'''

gg5.add_trace(go.Scatter(x=df2['x'], y=df2['y'],  showlegend=False), row=1, col=1)

'''принудительно добавляем под график значение "title_text", так как после комманды update_traces данные под осью x исчезли'''

gg5['layout']['xaxis1'].update(title_text='Дата')

'''добавляем линии и заливку (нижнюю зелёную):'''

gg5.add_hline(y=11, line_color="green", row=2, col=1)
gg5.add_hrect(y0=0, y1=11, line_width=0, fillcolor="green", opacity=0.2, row=2, col=1)

'''добавляем линии и заливку (верхнюю красную):'''

gg5.add_hline(y=94, line_color="red", row=2, col=1)
gg5.add_hrect(y0=94, y1=100, line_width=0, fillcolor="red", opacity=0.2, row=2, col=1)

'''добавляем поля title (сверху), меняем цвет шрифта, добавляем названия осей x и y'''

gg5.update_layout(title="Индекс страха и жадности + график Биткоина", title_font_color="blue")

'''делаем сигналы на пересечении кривых (пока не уверен, что это оптимальный способ)'''

a = df['Дата']
b = df['Значение индекса3'].round(1)
c = df['Значение индекса2'].round(1)

df_nums = pd.DataFrame({"A": a, "B": b, "C": c})

rslt_df = df_nums.loc[c==b]

writer = pd.ExcelWriter('test.xlsx')
rslt_df.to_excel(writer)
writer._save()

'''добавляем на график сигналы в виде точек:'''

gg5.add_trace(go.Scatter(x=rslt_df['A'], y=rslt_df['B'], name='Сигнал', mode='markers+text',
                         marker_color='green', marker_size=10, text="Сигнал!", textposition='top center',
                         textfont=dict(size=12, color="LightSeaGreen")), row=2, col=1)

'''строка, которая меняет порядок графиков в plotly в режиме "subplots":'''

# gg5.data = (gg5.data[5],gg5.data[2],gg5.data[4],gg5.data[0],gg5.data[3],gg5.data[1])

gg5.show()

# print(df)