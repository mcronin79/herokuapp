from bokeh.io import curdoc
from bokeh.plotting import figure, ColumnDataSource

fig = figure(title='Line plot!', sizing_mode='scale_width')
fig.line(x=[1, 2, 3], y=[1, 4, 9])

curdoc().title = "Hello, world!"
curdoc().add_root(fig)
