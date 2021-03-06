from bokeh.io import curdoc
from bokeh.palettes import Spectral6
from bokeh.plotting import figure
from bokeh.models.widgets import Tabs, Panel, CheckboxGroup, Slider, RangeSlider
from bokeh.models import Range1d, LinearAxis, ColumnDataSource, HoverTool
from bokeh.application.handlers import FunctionHandler
from bokeh.layouts import gridplot, layout, row, WidgetBox
import pandas as pd
import gspread
import math
import os
import json
import numpy as np
import random
import socketio
import logging
import enum 
import threading
#import multiprocessing
from multiprocessing import Process, Queue, Value, Array, Pool

from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import scipy.ndimage.filters as filters

print("Start Time");

q = Queue()

timeA = datetime.now()
# Enumeration for GSheet Columns 
class GSheetRow(enum.Enum): 
    Timestamp = 0
    Temperature = 1
    Humidity = 2
    RTD_Temperature = 3
    CO2 = 4
    Weight1 = 5
    Weight2 = 6
    Weight3 = 7
    Weight4 = 8
    Load_Cell1 = 9
    Load_Cell2 = 10
    Load_Cell3 = 11
    Load_Cell4 = 12
    VUSB = 13
    Weight_Code = 14
    
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

tools = 'pan', 'wheel_zoom', 'box_zoom', 'reset'

print("Start Time Before Sheets Load");
timeB = datetime.now()
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_creds = os.getenv("GOOGLE_SHEETS_CREDS_JSON")

creds_dict = json.loads(json_creds)
creds_dict["private_key"] = creds_dict["private_key"].replace("\\\\n", "\n")
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope) # Your json file here
gc = gspread.authorize(credentials)
wks = gc.open('MyHiveDataSheet').sheet1
gsheetRows = wks.get_all_values()
headers = gsheetRows.pop(0) 

df = pd.DataFrame(gsheetRows, columns=headers)
print("Start Time After Sheets Load");
timeC = datetime.now()
print(timeC - timeB)

sio = socketio.Client()
sio.connect('https://modified-sheets-stream.herokuapp.com/')

testData = []
    
@sio.on('data')
def print_message(data):
    global testData
    print("New Streamed Data");
    
    if isinstance(data, dict):
        pushedDict = data['results']    
        initialLoadLength = len(pushedDict)
        testData = pushedDict[initialLoadLength - 1]
        
    if isinstance(data, list):
        testData = data[0]
        
df.columns = [c.replace(" ","_") for c in df.columns]
skinned_headers = df.dtypes.index

startRange = datetime.now() - timedelta(hours=1)
endRange = datetime.now() + timedelta(hours=5)

source = ColumnDataSource({'x': [], 'y': [], 'color': []})
testsource = ColumnDataSource({'Timestamp': [], 'Temperature': []})

newfig = figure(title='Streaming Circle Plot!', sizing_mode='scale_width', x_range=[0, 1], y_range=[0, 1])
newfig.circle(source=source, x='x', y='y', color='color', size=10)
  
temperature_fig_test = figure(title="Temperature Realtime", title_location="above", x_axis_type='datetime', 
                              tools=tools, toolbar_location="above", x_range=[startRange, endRange], y_range=[0, 30])
temperature_fig_test.line(x='Timestamp', y='Temperature', source=testsource, color='magenta', legend='Temp')

temperature_fig_test.plot_height = 600
temperature_fig_test.plot_width = 800
temperature_fig_test.xaxis.axis_label = 'Time'
temperature_fig_test.yaxis.axis_label = 'Temperature (°C)'

def update():
    global testData
    print("Periodic Update")
    
    if (len(testData) > 0):    
        testArray = testData
        dateStr = testArray[GSheetRow.Timestamp.value]
        formattedDttm = datetime.strptime(dateStr, '%d/%m/%Y %H:%M:%S')
        formattedTemp = float(testArray[GSheetRow.Temperature.value])
        nuData = {'Timestamp': [formattedDttm],
           'Temperature': [formattedTemp]}
        testsource.stream(nuData)
        new = {'x': [random.random()],
               'y': [random.random()],
               'color': [random.choice(['red', 'blue', 'green'])]}
        source.stream(new)
        testData = []
        print("Finished Update")
    
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
#print(non_z_weights.head())

# todo: add grid to plot
time = df['Timestamp']
temperature = df['Temperature']
rtd_temperature = df['RTD_Temperature']
humidity = df['Humidity']
time_for_weight = non_z_weights['Timestamp'] # drop times where weight is recoded as zero

print("Time to load dataframes");
timeD = datetime.now()
print(timeD - timeC)

def plot_temperature():
    p = figure(title="Temperature", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    p.line(time, str_temperature, color='magenta', legend='Temperature')
    p.line(time, str_rtd_temperature, color='green', legend='RTD_Temperature')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Temperature (°C)'

    return p

def plot_CO2():
    p = figure(title="CO2 ppm", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    p.line(time, df['CO2'].astype(int), color='blue')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'CO2 (ppm)'

    return p

voltage1_fx = filters.gaussian_filter1d(df['Load_Cell1'], sigma=100)
voltage2_fx = filters.gaussian_filter1d(df['Load_Cell2'], sigma=100)
voltage3_fx = filters.gaussian_filter1d(df['Load_Cell3'], sigma=100)
voltage4_fx = filters.gaussian_filter1d(df['Load_Cell4'], sigma=100)

def plot_loadcell_voltages():
    p = figure(title="Load Cell Voltages", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    p.line(time, df['Load_Cell1'], color='blue')#, legend='Load Cell 1')
    p.line(time, df['Load_Cell2'], color='red')#, legend='Load Cell 2')
    p.line(time, df['Load_Cell3'], color='green')#, legend='Load Cell 3')
    p.line(time, df['Load_Cell4'], color='orange')#, legend='Load Cell 4')
    p.line(time, voltage1_fx, color='black')
    p.line(time, voltage2_fx, color='black')
    p.line(time, voltage3_fx, color='black')
    p.line(time, voltage4_fx, color='black')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Voltage (V)'

    return p

def plot_voltages_smooth():
    p = figure(title="Voltages Smooth", title_location="above", x_axis_type='datetime', tools=tools,
               toolbar_location="above")
    p.line(time, voltage1_fx, color='blue', legend='Voltage 1 Smooth')
    p.line(time, voltage2_fx, color='red', legend='Voltage 2 Smooth')
    p.line(time, voltage3_fx, color='green', legend='Voltage 3 Smooth')
    p.line(time, voltage4_fx, color='orange', legend='Voltage 4 Smooth')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Voltage (V)'

    return p

loadcell1_fx = filters.gaussian_filter1d(df['Load_Cell1']-df['Load_Cell1'].mean(), sigma=100)
loadcell2_fx = filters.gaussian_filter1d(df['Load_Cell2']-df['Load_Cell2'].mean(), sigma=100)
loadcell3_fx = filters.gaussian_filter1d(df['Load_Cell3']-df['Load_Cell3'].mean(), sigma=100)
loadcell4_fx = filters.gaussian_filter1d(df['Load_Cell4']-df['Load_Cell4'].mean(), sigma=100)
usb_fx = filters.gaussian_filter1d(df['VUSB'] - df['VUSB'].mean(), sigma=100)

def plot_loadcell_voltages_ac():
    p = figure(title="Load Cell Voltages AC Only", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    #p.line(time, df['Load_Cell1']-df['Load_Cell1'].mean(), color='blue')#, legend='Load Cell 1')
    #p.line(time, df['Load_Cell2']-df['Load_Cell2'].mean(), color='red')#, legend='Load Cell 2')
    #p.line(time, df['Load_Cell3']-df['Load_Cell3'].mean(), color='green')#, legend='Load Cell 3')
    #p.line(time, df['Load_Cell4']-df['Load_Cell4'].mean(), color='orange')#, legend='Load Cell 4')
    p.line(time, loadcell1_fx, color='blue')
    p.line(time, loadcell2_fx, color='red')
    p.line(time, loadcell3_fx, color='green')
    p.line(time, loadcell4_fx, color='orange')
    #p.line(time, df['VUSB'] - df['VUSB'].mean(), color='black')#, legend='VUSB')
    p.line(time, usb_fx, color='black')  # , legend='VUSB')
    #p.line(time, df['Temperature'] - df['Temperature'].mean(), color='magenta')#, legend='Temperature')


    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Voltage (V)'

    return p

def plot_loadcell_voltages_and_temperature_means():
    p = figure(title="Load Cell Voltages & Temperature Variation", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    p.line(time, df['Load_Cell1'] - df['Load_Cell1'].mean(), color='blue')  # , legend='Load Cell 1')
    p.line(time, df['Load_Cell2'] - df['Load_Cell2'].mean(), color='red')  # , legend='Load Cell 2')
    p.line(time, df['Load_Cell3'] - df['Load_Cell3'].mean(), color='green')  # , legend='Load Cell 3')
    p.line(time, df['Load_Cell4'] - df['Load_Cell4'].mean(), color='orange')  # , legend='Load Cell 4')
    p.line(time, df['VUSB'] - df['VUSB'].mean(), color='black')  # , legend='VUSB')

    p.yaxis.axis_label = 'Voltage (V)'
    lc1 = df['Load_Cell1'] - df['Load_Cell1'].mean()
    lc2 = df['Load_Cell2'] - df['Load_Cell2'].mean()
    lc3 = df['Load_Cell3'] - df['Load_Cell3'].mean()
    lc4 = df['Load_Cell4'] - df['Load_Cell4'].mean()

    #p.y_range = Range1d((df['Load_Cell1'] - df['Load_Cell1'].mean()).min(), (df['Load_Cell1'] - df['Load_Cell1'].mean()).max())  # SECOND AXIS, y_range is temperature_range, fixed attribute
    p.y_range = Range1d(pd.DataFrame([lc1, lc2, lc3, lc4]).values.min()*1.1, pd.DataFrame([lc1, lc2, lc3, lc4]).values.max()*1.1)  # SECOND AXIS, y_range is temperature_range, fixed attribute
    temperature_range = 'blah'
    a = df['Temperature'] - df['Temperature'].mean()
    p.extra_y_ranges = {
        temperature_range: Range1d(a.min()*1.1, a.max()*1.1)
    }
    p.add_layout(LinearAxis(y_range_name=temperature_range, axis_label='Temperature (°C)'), 'right')

    p.line(time, a, y_range_name=temperature_range, color="magenta")#, legend='Temperature')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    #p.legend.location = 'bottom_right'

    return p

def plot_humidity():
    p = figure(title="Humidity", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    p.line(time, str_humidity, color='cyan', legend='Humidity')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Humidity (%)'

    return p

def plot_temp_and_humidity():
    p = figure(title="Temperature & Humidity", title_location="above", x_axis_type='datetime', tools=tools, toolbar_location="above")
    p.line(time, str_temperature,  color="magenta", legend='Temperature')
    p.line(time, str_rtd_temperature, color='green', legend='RTD_Temperature')

    p.yaxis.axis_label = 'Temperature (°C)'
    p.y_range = Range1d(temperature.min()-0.1, temperature.max()+0.1)  # SECOND AXIS, y_range is temperature_range, fixed attribute
    humidity_range = 'blah'
    p.extra_y_ranges = {
        humidity_range: Range1d(humidity.min()*0.975, humidity.max()*1.025)
    }
    p.add_layout(LinearAxis(y_range_name=humidity_range, axis_label='Humidity (%)'), 'right')

    p.line(time, str_humidity, y_range_name=humidity_range, color="cyan", legend='Humidity')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.legend.location = 'bottom_right'

    return p

weights = ['Weight1', 'Weight2', 'Weight3', 'Weight4']

def plot_4weight_bar():
    p = figure(title="Load Cell Weights", title_location="above", x_range=weights, plot_height=250)
    p.vbar(x=weights, top=[5, 3, 4, 2, 4, 6], width=0.9)

    p.xgrid.grid_line_color = None
    p.y_range.start = 0

    return p

def plot_weight():
    p = figure(title='Weight', title_location="above", x_axis_type='datetime', tools=tools, toolbar_location='above')
    offset = 15421626
    slope = 8.01888E-07

    weight = []
    for w in df['Weight_Code']:
        value = (w - offset) * slope * 1000
        weight.append(value)

    weight_fx = filters.gaussian_filter1d(weight, sigma=50)

    p.line(time, weight, color='red', legend='Weight')
    p.line(time, weight_fx, color='black', legend='Weight Smooth')

    p.plot_height = 600
    p.plot_width = 800
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Weight (Kg)'

    return p

print("Before calling plot functions");
timeE = datetime.now()

temperature_fig = None
humidity_fig = None
temp_and_hum_fig = None
load_cell_voltages_fig = None
load_cell_voltages_ac_fig = None
voltages_temperature_means_fig = None
weight_fig = None
CO2_fig = None

def thread_function1(name):
    global temperature_fig, humidity_fig, temp_and_hum_fig, CO2_fig
    print("thread_function1 Type temperature_fig");
    print(type(temperature_fig)) 
    print("thread_function1 Type humidity_fig");
    print(type(humidity_fig)) 
    print("thread_function1 Type temp_and_hum_fig");
    print(type(temp_and_hum_fig)) 
    
    timeT1 = datetime.now()
    print("Thread1 starting");
    print(timeT1);
    temperature_fig = plot_temperature()
    humidity_fig = plot_humidity()
    temp_and_hum_fig = plot_temp_and_humidity()
    CO2_fig = plot_CO2()
    
    print("After thread_function1 Type temperature_fig");
    print(type(temperature_fig)) 
    print("After thread_function1 Type humidity_fig");
    print(type(humidity_fig)) 
    print("After thread_function1 Type temp_and_hum_fig");
    print(type(temp_and_hum_fig)) 
    #q.put(temperature_fig)
    q.put(temperature_fig)
    q.put(humidity_fig)
    q.put(temp_and_hum_fig)
    q.put(CO2_fig)
    print("Thread1 finishing");    
    print(datetime.now() - timeT1)
   
def thread_function2(name):
    #global load_cell_voltages_fig
    timeT1 = datetime.now()
    print("Thread2 starting");
    print(timeT1);
    load_cell_voltages_fig = plot_loadcell_voltages()
    print("Thread2 finishing");    
    print(datetime.now() - timeT1)
    return load_cell_voltages_fig
  
def thread_function3(name):
    #global load_cell_voltages_ac_fig
    timeT1 = datetime.now()
    print("Thread3 starting");
    print(timeT1);
    load_cell_voltages_ac_fig = plot_loadcell_voltages_ac()
    print("Thread3 finishing");    
    print(datetime.now() - timeT1)
    return load_cell_voltages_ac_fig

def thread_function4(name):
    #global voltages_temperature_means_fig
    timeT1 = datetime.now()
    print("Thread4 starting");
    print(timeT1);
    voltages_temperature_means_fig = plot_loadcell_voltages_and_temperature_means()
    print("Thread4 finishing");    
    print(datetime.now() - timeT1)
    return voltages_temperature_means_fig

def thread_function5(name):
    #global weight_fig
    timeT1 = datetime.now()
    print("Thread5 starting");
    print(timeT1);
    weight_fig = plot_weight()
    print("Thread5 finishing");    
    print(datetime.now() - timeT1)
    return weight_fig
    
#num = Value('d', 0.0)
#arr = Array('i', range(10))    
#p = Process(target=f, args=(num, arr))

p = Pool(4)
result1 = p.apply_async(thread_function2, ("Thread-1",))
result2 = p.apply_async(thread_function3, ("Thread-2",))
result3 = p.apply_async(thread_function4, ("Thread-3",))
result4 = p.apply_async(thread_function5, ("Thread-4",))
p.close()
p.join()

new_load_cell_voltages_fig = result1.get()
new_load_cell_voltages_ac_fig = result2.get()
new_voltages_temperature_means_fig = result3.get()
new_weight_fig = result4.get()

#print(result.get(timeout=1))
#thread1 = Process(target=thread_function1, args=("Thread-1", ))
#thread2 = Process(target=thread_function2, args=("Thread-2", ))
#thread3 = Process(target=thread_function3, args=("Thread-3", ))
#thread4 = Process(target=thread_function4, args=("Thread-4", ))
#thread5 = Process(target=thread_function5, args=("Thread-5", ))

#thread1.start()
#thread2.start()
#thread3.start()
#thread4.start()
#thread5.start()
#thread1.join()
#thread2.join()
#thread3.join()
#thread4.join()
#thread5.join()

print("After calling plot functions");
timeF = datetime.now()
print(timeF - timeE)

print("Type temperature_fig");
print(type(temperature_fig)) 

print("Type new_temperature_fig");
#new_temperature_fig = q.get()
#new_humidity_fig = q.get()
#new_temp_and_hum_fig = q.get()
#new_CO2_fig = q.get()
#print(type(new_temperature_fig)) 

print("Type new_load_cell_voltages_fig");
print(type(new_load_cell_voltages_fig)) 
print("Type new_load_cell_voltages_ac_fig");
print(type(new_load_cell_voltages_ac_fig)) 
print("Type new_voltages_temperature_means_fig");
print(type(new_voltages_temperature_means_fig)) 

#l1 = layout([[new_temperature_fig, new_humidity_fig], [new_temp_and_hum_fig, new_CO2_fig]], sizing_mode='fixed')
l1 = layout([[new_load_cell_voltages_fig, new_weight_fig], [new_load_cell_voltages_ac_fig, new_voltages_temperature_means_fig]], sizing_mode='fixed')

#l1 = layout([[temperature_fig]], sizing_mode='fixed')
l2 = layout([[newfig]], sizing_mode='fixed')
l3 = layout([[temperature_fig_test]], sizing_mode='fixed')

print("After building layouts");
timeG = datetime.now()
print(timeG - timeF)

tab1 = Panel(child=l1,title="Air Quality")
tab2 = Panel(child=l2,title="Metrics")
tab3 = Panel(child=l3,title="Streaming")

# Make a tab with the layout
tabs = Tabs(tabs=[ tab1, tab2, tab3 ])

print("After building tabs");
timeH = datetime.now()
print(timeH - timeG)

curdoc().add_periodic_callback(update, 30000)
curdoc().title = "Hello, world!"

print("Before Rendering tabs");
timeI = datetime.now()

curdoc().add_root(tabs)

print("After Rendering tabs");
timeJ = datetime.now()
print(timeJ - timeI)
