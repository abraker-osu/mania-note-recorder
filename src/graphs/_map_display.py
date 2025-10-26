import pyqtgraph

from PyQt6 import QtCore
from PyQt6 import QtGui

from osu_analysis import ManiaScoreData

from note_recorder import Data
from graph_mgr import GraphManager
from plots.num_plot import NumPlotItem


class MapDisplay():

    def __init__(self, graph_mgr: GraphManager, pos, relative_to = None):
        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title = 'Map display')
        self.__graph_mgr = graph_mgr

        self.__graph_mgr.create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = self.__widget,
        )

        # hit_offsets graph
        plot_item = self.__widget.getPlotItem()
        assert isinstance(plot_item, pyqtgraph.PlotItem)

        plot_item.getAxis('left').enableAutoSIPrefix(False)
        plot_item.getAxis('bottom').enableAutoSIPrefix(False)
        self.__widget.setLabel('left', 'Time', units = 'ms', unitPrefix = '')
        self.__widget.setLabel('bottom', 'column', units = '', unitPrefix = '')

        view_box = plot_item.getViewBox()
        assert isinstance(view_box, pyqtgraph.ViewBox)

        view_box.setMouseEnabled(x = False)

        self.__note_num_plot = self.__widget.plot()

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam=0.5)
        self.__widget.addItem(self.__error_bar_graph)

        self.__note_column  = None
        self.__note_timings = None


    def plot_data(self, data):
        self.__plot_notes(data)


    def __plot_notes(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == min(data[:, Data.TIMESTAMP])) & \
            ((data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP) | \
             (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISSP))

        data = data[data_filter]

        # Extract timings and hit_offsets
        self.__note_column  = data[:, Data.KEYS]
        self.__note_timings = data[:, Data.TIMINGS] - data[:, Data.OFFSETS]

        # Calculate view
        xMin = -2
        xMax = max(self.__note_column) + 2

        symbol = QtGui.QPainterPath()
        symbol.addRect(QtCore.QRectF(-0.5, -0.5, 1, 1))

        # Set plot data
        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            self.__note_column, self.__note_timings,
            pen = None, symbol = symbol, symbolPen = None, symbolSize = 20, symbolBrush = (100, 100, 255, 200)
        )
        self.__widget.setXRange(max(self.__note_column)*(0.5 - 1.5), max(self.__note_column)*(0.5 + 1.5))


    def plot_stddevs(self, data):
        if type(self.__note_column) == type(None) or \
           type(self.__note_timings) == type(None):
            return

        means, stddevs = data
        #print(means.shape, stddevs.shape, self.__note_column.shape, self.__note_timings.shape)
        self.__error_bar_graph.setData(
            x = self.__note_column, y = self.__note_timings + means, top = 2*stddevs, bottom = 2*stddevs,
            pen = (200, 200, 200, 100)
        )
