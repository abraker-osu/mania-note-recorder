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
            widget      = pyqtgraph.PlotWidget(title='Note intervals vs Delta hit timings'),
        )

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Delta hit timing', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Interval', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(xMin=-1, xMax=1100, yMin=-200, yMax=200)

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam=0.5)
        self.graphs[self.__id]['widget'].addItem(self.__error_bar_graph)

        self.__model_plot = self.graphs[self.__id]['widget'].plot()


    def _plot_data(self, data):
        IntervalOffsetGraph.__plot_graph(self, data)
        IntervalOffsetGraph.__plot_model(self, data)


    def __plot_graph(self, interval_data):
        miss_filter = interval_data[:, 3] == ManiaScoreData.TYPE_HITP
        interval_data = interval_data[miss_filter]

        self.graphs[self.__id]['plot'].setData(interval_data[:, 0], interval_data[:, 2] - interval_data[:, 0], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))


    def __plot_model(self, interval_data):
        miss_filter = interval_data[:, 3] == ManiaScoreData.TYPE_HITP
        interval_data = interval_data[miss_filter]

        # Get list of existing intervals and filter out ones that are more than 1 second
        intervals = np.unique(interval_data[:, 0])
        intervals = intervals[intervals <= 1000]

        _means     = []
        _stddevs   = []
        _intervals = []

        for interval in intervals:
            # Select all data point close to current interval
            data_select = (np.abs(interval_data[:, 0] - interval) <= 1)
            hittimings_d = interval_data[data_select, 2] - interval

            # Filter out outliers
            stddev = np.std(hittimings_d)
            mean   = np.mean(hittimings_d)

            outlier_filter = ((-1.5*stddev + mean) < hittimings_d) & (hittimings_d < (1.5*stddev + mean))
            hittimings_d = hittimings_d[outlier_filter]

            if hittimings_d.shape[0] < 5: 
                continue

            # Record processed data
            _means.append(np.mean(hittimings_d))
            _stddevs.append(2*np.std(hittimings_d))
            _intervals.append(interval)

        _means     = np.asarray(_means)
        _stddevs   = np.asarray(_stddevs)
        _intervals = np.asarray(_intervals)

        self.__error_bar_graph.setData(x=_intervals, y=_means, top=2*_stddevs, bottom=2*_stddevs, pen=mkPen((200, 200, 200, 50)))
        self.__model_plot.setData(_intervals, _means, pen=mkPen((200, 200, 0, 150)))

        