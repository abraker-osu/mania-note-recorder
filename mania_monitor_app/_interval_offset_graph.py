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
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Note interval', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(xMin=-1, xMax=1100, yMin=-200, yMax=200)

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam=0.5)
        self.graphs[self.__id]['widget'].addItem(self.__error_bar_graph)

        self.__model_plot = self.graphs[self.__id]['widget'].plot()


    def _plot_data(self, data):
        IntervalOffsetGraph.__plot_graph(self, data)
        IntervalOffsetGraph.__plot_model(self, data)


    def __plot_graph(self, interval_data):
        #miss_filter = interval_data[:, 3] == ManiaScoreData.TYPE_HITP
        #interval_data = interval_data[miss_filter]

        self.graphs[self.__id]['plot'].setData(interval_data[:, 0], interval_data[:, 2] - interval_data[:, 0], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))


    def __plot_model(self, interval_data):
        miss_filter = interval_data[:, 3] == ManiaScoreData.TYPE_HITP
        interval_data = interval_data[miss_filter]

        # Get list of existing intervals and filter out ones that are more than 1 second
        unique_intervals = np.unique(interval_data[:, 0])
        intervals = unique_intervals[unique_intervals <= 1000]

        means     = []
        stddevs   = []
        intervals = []

        for interval in unique_intervals:
            # Select all data point close to current interval
            data_select = (np.abs(interval_data[:, 0] - interval) <= 1)
            hittimings_d = interval_data[data_select, 2] - interval

            # Filter out outliers
            stddev = np.std(hittimings_d)
            mean   = np.mean(hittimings_d)

            outlier_filter = ((-1.5*stddev + mean) < hittimings_d) & (hittimings_d < (1.5*stddev + mean))
            hittimings_d = hittimings_d[outlier_filter]

            if hittimings_d.shape[0] < 10: 
                continue

            # Record processed data
            means.append(np.mean(hittimings_d))
            stddevs.append(2*np.std(hittimings_d))
            intervals.append(interval)

        means     = np.asarray(means)
        stddevs   = np.asarray(stddevs)
        intervals = np.asarray(intervals)

        self.__error_bar_graph.setData(x=intervals, y=means, top=2*stddevs, bottom=2*stddevs, pen=mkPen((200, 200, 200, 50)))
        self.__model_plot.setData(intervals, means, pen=mkPen((200, 200, 0, 150)))

        # Since the difference between note interval and player's tapping interval is
        # how much the player is slow by, we can determine the player's tapping speed.
        # And if we look at points that are sufficiently high enough, then we can determine
        # how fast the player can possibly tap. 
        # 
        # For example, note interval is 100 ms and player tapped 20 ms late on average. This means
        # player's tapping interval is 120 ms.
        if means.shape[0] < 1:
            return

        tapping_intervals = np.asarray([ (interval + mean + 2*stddev) for interval, mean, stddev in zip(intervals, means, stddevs) ])
        if tapping_intervals.shape[0] == 0:
            print('Unsufficient data to determine tapping rate')
            return

        best_idx = np.argmin(tapping_intervals)
        tapping_interval = tapping_intervals[best_idx]

        if means[best_idx] <= 16:
            print(f'Min average player tapping rate: > {1000/tapping_interval:.2f} nps (< {tapping_interval:.2f} ms)')
        else:
            print(f'Min average player tapping rate: {1000/tapping_interval:.2f} nps ({tapping_interval:.2f} ms)')

        