import pyqtgraph
from pyqtgraph.functions import mkPen

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData



class IntervalOffsetGraph():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Note intervals vs Avg Note offset'),
        )

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Interval', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(xMin=-1, yMin=-200, yMax=200)

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam=0.5)
        self.graphs[self.__id]['widget'].addItem(self.__error_bar_graph)


    def _plot_data(self, data):
        IntervalOffsetGraph.__plot_graph(self, data)
        IntervalOffsetGraph.__plot_model(self, data)


    def __plot_graph(self, interval_data):
        miss_filter = interval_data[:, 3] == ManiaScoreData.TYPE_HITP
        interval_data = interval_data[miss_filter]

        self.graphs[self.__id]['plot'].setData(interval_data[:, 0], interval_data[:, 2], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))


    def __plot_model(self, interval_data):
        miss_filter = interval_data[:, 3] == ManiaScoreData.TYPE_HITP
        interval_data = interval_data[miss_filter]

        intervals = np.unique(interval_data[:, 0])

        means   = np.asarray([ np.mean(interval_data[np.abs(interval_data[:, 0] - interval) <= 1, 2]) for interval in intervals ])
        stddevs = np.asarray([ 2*np.std(interval_data[np.abs(interval_data[:, 0] - interval) <= 1, 2]) for interval in intervals ])

        self.__error_bar_graph.setData(x=intervals, y=means, top=2*stddevs, bottom=2*stddevs, pen=mkPen((200, 200, 200, 50)))


        