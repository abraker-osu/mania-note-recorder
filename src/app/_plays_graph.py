import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui
from datetime import datetime

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from .plots.miss_plot import MissPlotItem

from ._callback import callback


class PlaysGraph():

    @callback
    class region_changed_event(): pass

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(axisItems={ 'bottom': pyqtgraph.DateAxisItem(orientation='bottom') }),
            dock_name   = ''
        )

        # Dock size
        self.graphs[self.__id]['dock'].setMaximumHeight(64)

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').hide()
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getViewBox().setMouseEnabled(y=False)
        self.graphs[self.__id]['widget'].setLimits(yMin=-200, yMax=200)

        # Interactive region item
        self.__region_plot = pyqtgraph.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='r')
        self.__region_plot.sigRegionChangeFinished.connect(lambda: PlaysGraph.__region_changed(self))
        self.graphs[self.__id]['widget'].addItem(self.__region_plot)


    def _plot_data(self, data):
        PlaysGraph.__plot_plays(self, data)


    def __plot_plays(self, data):
        hit_timestamps = np.unique(data[:, Data.TIMESTAMP])

        # Calculate view
        xMin = min(hit_timestamps) - 100
        xMax = max(hit_timestamps) + 86400  # + 1 day

        # Set plot data
        self.graphs[self.__id]['plot'].setData(hit_timestamps, np.zeros(hit_timestamps.shape[0]), pen=None, symbol='o', symbolPen=None, symbolSize=4, symbolBrush='y')
        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, xMax=xMax)

        # Update region item
        rBeg, _ = self.__region_plot.getRegion()

        self.__region_plot.setBounds((xMin, xMax))
        self.__region_plot.setRegion((max(xMin, rBeg), xMax))


    def __region_changed(self):
        PlaysGraph.region_changed_event.emit(self.__region_plot.getRegion())