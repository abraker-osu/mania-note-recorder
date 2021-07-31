import pyqtgraph
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data

from .plots.num_plot import NumPlotItem


class MapDisplay():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Map display'),
        )

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Time', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'column', units='', unitPrefix='')
        self.graphs[self.__id]['widget'].getPlotItem().getViewBox().setMouseEnabled(x=False)

        self.__note_num_plot = self.graphs[self.__id]['widget'].plot()

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam=0.5)
        self.graphs[self.__id]['widget'].addItem(self.__error_bar_graph)

        self.__note_column = None
        self.__note_timings = None


    def _plot_data(self, data):
        MapDisplay.__plot_notes(self, data)


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
        self.graphs[self.__id]['plot'].setData(self.__note_column, self.__note_timings, pen=None, symbol=symbol, symbolPen=None, symbolSize=20, symbolBrush=(100, 100, 255, 200))
        self.graphs[self.__id]['widget'].setXRange(max(self.__note_column)*(0.5 - 1.5), max(self.__note_column)*(0.5 + 1.5))

        def create_text(i):
            f = QFont()
            f.setPointSize(48)
            symbol = QtGui.QPainterPath()
            symbol.addText(0, 0, f, str(i))
            br = symbol.boundingRect()
            scale = min(1. / br.width(), 1. / br.height())
   
            tr = QTransform()
            tr.scale(scale, scale)
            tr.translate(-br.x() - br.width() / 2., -br.y() - br.height() / 2.)
            
            return tr.map(symbol)

        symbols = [ create_text(i) for i in range(len(self.__note_timings)) ]
        #self.__note_num_plot.setData(self.__note_column, self.__note_timings, pen=None, symbol=symbols, symbolPen=None, symbolSize=20, symbolBrush=(200, 200, 200, 200))


    def _plot_stddevs(self, data):
        if type(self.__note_column) == type(None) or \
           type(self.__note_timings) == type(None):
            return

        means, stddevs = data
        self.__error_bar_graph.setData(x=self.__note_column, y=self.__note_timings + means, top=2*stddevs, bottom=2*stddevs, pen=(200, 200, 200, 100))
