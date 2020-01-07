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


df.columns = [c.replace(" ","_") for c in df.columns]
skinned_headers = df.dtypes.index

str_temperature = df['Temperature']
str_rtd_temperature = df['RTD_Temperature']
str_humidity = df['Humidity']
str_weight1 = df['Weight1']
str_weight2 = df['Weight2']
str_weight3 = df['Weight3']
str_weight4 = df['Weight4']
str_loadcell_1 = df['Load_Cell1']
str_loadcell_2 = df['Load_Cell2']
str_loadcell_3 = df['Load_Cell3']
str_loadcell_4 = df['Load_Cell4']
str_vusb = df['VUSB']
str_weight_code = df['Weight_Code']
str_CO2 = df['CO2']

df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d/%m/%Y %H:%M:%S')
df['Temperature'] = df['Temperature'].astype(float)
df['RTD_Temperature'] = df['RTD_Temperature'].astype(float)#.apply(lambda x: x - 0.15)
df['Humidity'] = df['Humidity'].astype(float)

df['O02'] = df['CO2'].astype(int)
df['Weight_Code'] = df['Weight_Code'].astype(int)

df['Load_Cell1'] = df['Load_Cell1'].astype(float)
df['Load_Cell2'] = df['Load_Cell2'].astype(float)
df['Load_Cell3'] = df['Load_Cell3'].astype(float)
df['Load_Cell4'] = df['Load_Cell4'].astype(float)

df['VUSB'] = df['VUSB'].astype(float)

non_z_weights = df.query('Load_Cell1 != 0 & Load_Cell2 != 0 & Load_Cell3 != 0 & Load_Cell4 != 0')
print(non_z_weights.head())

# todo: add grid to plot
time = df['Timestamp']
temperature = df['Temperature']
rtd_temperature = df['RTD_Temperature']
humidity = df['Humidity']
time_for_weight = non_z_weights['Timestamp'] # drop times where weight is recoded as zero


def plot_temperature():
    p = figure(title="Temperature", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    p.line(time, str_temperature, color='magenta', legend='Temperature')
    p.line(time, str_rtd_temperature, color='green', legend='RTD_Temperature')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Temperature (°C)'

    return p


temperature_fig = plot_temperature()

fig = figure(title='Line plot!', sizing_mode='scale_width')
fig.line(x=[1, 2, 3], y=[1, 4, 9])

#l1 = layout([[temperature_fig, load_cell_voltages_fig]], sizing_mode='stretch_both')
l1 = gridplot([[temperature_fig, fig], [temperature_fig, fig]], sizing_mode='stretch_both')
l2 = gridplot([[temperature_fig, fig], [temperature_fig, fig]], sizing_mode='stretch_both')

tab1 = Panel(child=l1,title="Air Quality")
tab2 = Panel(child=l2,title="Metrics")
tabs = Tabs(tabs=[ tab1, tab2 ])

curdoc().title = "Hello, world!"
curdoc().add_root(tabs)
