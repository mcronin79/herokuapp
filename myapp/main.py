from bokeh.io import curdoc
from bokeh.plotting import figure, ColumnDataSource
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

tools = 'pan', 'wheel_zoom', 'box_zoom', 'reset'

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('myapp/data/sheets_token.json', scope) # Your json file here
gc = gspread.authorize(credentials)
wks = gc.open('MyHiveDataSheet').sheet1
data = wks.get_all_values()
headers = data.pop(0)
print(headers)

df = pd.DataFrame(data, columns=headers)

print(" ")
print("here")
print(" ")
print(df.shape)
print(len(df.index))

fig = figure(title='Line plot!', sizing_mode='scale_width')
fig.line(x=[1, 2, 3], y=[1, 4, 9])

curdoc().title = "Hello, world!"
curdoc().add_root(fig)
