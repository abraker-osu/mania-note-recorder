import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from .plots.miss_plot import MissPlotItem


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


    def _plot_data(self, data):
        MapDisplay.__plot_notes(self, data)


    def __plot_notes(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] != ManiaScoreData.TYPE_EMPTY)

        data = data[data_filter]

        # Extract timings and hit_offsets
        hit_timings = data[:, Data.TIMINGS]
        hit_offsets = data[:, Data.OFFSETS]
        note_column = data[:, Data.KEYS]

        note_timings = data[:, Data.TIMINGS] - data[:, Data.OFFSETS]

        # Calculate view
        xMin = -2
        xMax = max(note_column) + 2

        symbol = QtGui.QPainterPath()
        symbol.addRect(QtCore.QRectF(-0.5, -0.5, 1, 1))

        # Set plot data
        self.graphs[self.__id]['plot'].setData(note_column, note_timings, pen=None, symbol=symbol, symbolPen=None, symbolSize=20, symbolBrush=(100, 100, 255, 200))
        self.graphs[self.__id]['widget'].setXRange(max(note_column)*(0.5 - 1.5), max(note_column)*(0.5 + 1.5))

        
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

        symbols = [ create_text(i) for i in range(len(note_timings)) ]

        self.__note_num_plot.setData(note_column, note_timings, pen=None, symbol=symbols, symbolPen=None, symbolSize=20, symbolBrush=(200, 200, 200, 200))