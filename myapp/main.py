from bokeh.io import curdoc
from bokeh.palettes import Spectral6
from bokeh.plotting import figure
from bokeh.models.widgets import Tabs, Panel, CheckboxGroup, Slider, RangeSlider
from bokeh.models import Range1d, LinearAxis, ColumnDataSource, HoverTool
from bokeh.application.handlers import FunctionHandler
from bokeh.layouts import gridplot, layout
import pandas as pd
import gspread
import math
import numpy as np
from oauth2client.service_account import ServiceAccountCredentials
import scipy.ndimage.filters as filters

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

temperature_fig = plot_temperature()
humidity_fig = plot_humidity()
temp_and_hum_fig = plot_temp_and_humidity()
load_cell_voltages_fig = plot_loadcell_voltages()
load_cell_voltages_ac_fig = plot_loadcell_voltages_ac()
voltages_temperature_means_fig = plot_loadcell_voltages_and_temperature_means()
weight_fig = plot_weight()
CO2_fig = plot_CO2()



load_cell_cols = [col for col in df.columns if 'Load_Cell' in col]
print('load cell column names:', load_cell_cols)

tidy_load_cells = df.melt(value_vars=load_cell_cols)
print(tidy_load_cells.head())

# Available load cell list
available_load_cells = list(tidy_load_cells['variable'].unique())

# Sort the list in-place (alphabetical order)
available_load_cells.sort()
print('available_load_cells:', available_load_cells)
print('length of available_load_cells:', len(available_load_cells))

def style(p):
    p.title.align = 'center'
    p.title.text_font_size = '18pt'
    p.xaxis.axis_label_text_font_size = '12pt'
    p.xaxis.major_label_text_font_size = '12pt'
    p.yaxis.axis_label_text_font_size = '12pt'
    p.yaxis.major_label_text_font_size = '12pt'

    return p

def make_dataset(tidy_data, range_start, range_end, bin_width):
    by_loadcell = pd.DataFrame(columns=['count', 'left', 'right',
                                       'v_count', 'v_interval', 'color'])
    print('by_loadcell is:', by_loadcell)
    print('tidy_data is:', tidy_data)

    print(range_start)
    print(range_end)
    print(bin_width)

    for i, j in enumerate(tidy_data['variable'].unique()):
        x_min = (math.ceil(min(tidy_data[tidy_data['variable'] == j]['value']) * 1000) - 1) / 1000
        x_max = (math.ceil(max(tidy_data[tidy_data['variable'] == j]['value']) * 1000) + 1) / 1000

        range_extent = x_max - x_min

        print('x_min:', x_min)
        print('x_max:', x_max)
        #print(tidy_data['variable']==i)
        # Check to make sure the start is less than the end!
        assert x_min < x_max, "Start must be less than end!"

        tidy_data_hist, edges = np.histogram(tidy_data[tidy_data['variable'] == j]['value'], bins=int(range_extent / bin_width), range=[range_start, range_end])
        # Put the information in a dataframe
        by_load_cell_df = pd.DataFrame({'count': tidy_data_hist,
                                     j: tidy_data_hist,
                                     'left': edges[:-1],
                                     'right': edges[1:]})
        by_load_cell_df['v_count'] = ['%d hits' % count for count in by_load_cell_df['count']]
        by_load_cell_df['v_interval'] = ['%f to %f V' % (left, right) for left, right in zip(by_load_cell_df['left'], by_load_cell_df['right'])]
        # Color each loadcell differently
        by_load_cell_df['color'] = Spectral6[i]

        print('by_load_cell columns:', by_load_cell_df.columns)

        by_loadcell = by_loadcell.append(by_load_cell_df)

    return ColumnDataSource(by_loadcell)

def make_plot(src, col):
    # Blank plot with correct labels
    p = figure(plot_width=700,
               plot_height=700,
               title='Histogram of Voltages',
               x_axis_label='Voltage (V)',
               y_axis_label='Number of Readings')

    for i in col:
        # Quad glyphs to create a histogram
        p.quad(source=src,
               bottom=0,
               top='count',
               left='left',
               right='right',
               fill_color='color',
               line_color='black',
               fill_alpha=0.75,
               legend=i,
               hover_fill_alpha=1.0,
               hover_fill_color='red')

    # Hover tool with vline mode
    hover = HoverTool(tooltips=[('# of Voltages', '@v_count'),
                                ('Bin', '@v_interval')],
                      mode='vline')

    p.add_tools(hover)

    p.legend.click_policy = 'hide'

    # Styling
    p = style(p)

    #show(p)

    return p

# Update the plot based on selections
def update(attr, old, new):
    # print(f'Inside Updater {range_select.value} || {binwidth_select.value}')
    loadcells_to_plot = [loadcell_selection.labels[i] for i in loadcell_selection.active]

    #new_src = make_dataset(loadcells_to_plot,
    # Range select indexing changed
    new_src=make_dataset(tidy_load_cells,
                           range_start=range_select.value[0],
                           range_end=range_select.value[1],
                           bin_width=binwidth_select.value)

    src.data.update(new_src.data)

# CheckboxGroup to select loadcell to display
loadcell_selection = CheckboxGroup(labels=available_load_cells, active=[0, 1, 2, 3])
loadcell_selection.on_change('active', update)

# Slider to select width of bin
binwidth_select = Slider(start=0.005, end=0.1,
                         step=0.005, value=0.005,
                         title='Bin Width (V)')
binwidth_select.on_change('value', update)

# RangeSlider control to select start and end of plotted delays
range_select = RangeSlider(start=0.45, end=2, value=(0.45, 2),
                           step=0.01, title='Voltage Range (V)')
range_select.on_change('value', update)

# Find the initially selected loadcells
initial_loadcells = [loadcell_selection.labels[i] for i in loadcell_selection.active]

#src = make_dataset(initial_loadcells)
src = make_dataset(tidy_load_cells, 0.45, 2, 0.005)
p = make_plot(src, initial_loadcells)

# Put controls in a single element
controls = WidgetBox(loadcell_selection, binwidth_select, range_select)

# Create a row layout
layout = row(controls, p)

# Make a tab with the layout
tab3 = Panel(child=layout, title='Delay Histogram')




#l1 = layout([[temperature_fig, load_cell_voltages_fig]], sizing_mode='stretch_both')
l1 = layout([[temperature_fig, humidity_fig], [temp_and_hum_fig, CO2_fig]], sizing_mode='fixed')
l2 = layout([[load_cell_voltages_fig, weight_fig], [load_cell_voltages_ac_fig, voltages_temperature_means_fig]], sizing_mode='fixed')

#l1 = gridplot([[temperature_fig, humidity_fig], [temp_and_hum_fig, CO2_fig]], sizing_mode='stretch_both')
#l2 = gridplot([[load_cell_voltages_fig, weight_fig], [load_cell_voltages_ac_fig, voltages_temperature_means_fig]], sizing_mode='stretch_both')

tab1 = Panel(child=l1,title="Air Quality")
tab2 = Panel(child=l2,title="Metrics")
tabs = Tabs(tabs=[ tab1, tab2, tab3 ])

curdoc().title = "Hello, world!"
curdoc().add_root(tabs)
