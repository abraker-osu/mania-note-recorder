import pyqtgraph
from pyqtgraph.functions import mkPen

import numpy as np

from osu_analysis import ManiaScoreData

from graph_mgr import GraphManager

from misc._callback import callback


class IntervalOffsetGraph():

    @callback
    class calc_done_event(): pass

    def __init__(self, graph_mgr: GraphManager, pos, relative_to=None):
        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title='Note intervals vs Delta hit timings')
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
        self.__widget.setLabel('left', 'Delta hit timing', units = 'ms', unitPrefix = '')
        self.__widget.setLabel('bottom', 'Note interval', units = 'ms', unitPrefix = '')
        self.__widget.setLimits(xMin = -1, xMax = 1100, yMin = -200, yMax = 200)

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam = 0.5)
        self.__widget.addItem(self.__error_bar_graph)

        self.__model_plot = self.__widget.plot()


    def plot_data(self, data: np.ndarray):
        self.__plot_graph(data)
        self.__plot_model(data)


    def __plot_graph(self, interval_data: np.ndarray):
        #miss_filter = interval_data[:, 3] == ManiaScoreData.TYPE_HITP
        #interval_data = interval_data[miss_filter]

        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            interval_data[:, 0], interval_data[:, 2] - interval_data[:, 0],
            pen = None, symbol = 'o', symbolPen = None, symbolSize = 2, symbolBrush = (100, 100, 255, 200)
        )


    def __plot_model(self, interval_data: np.ndarray):
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

        self.__error_bar_graph.setData(
            x = intervals, y = means, top = 2*stddevs, bottom = 2*stddevs,
            pen = mkPen((200, 200, 200, 50))
        )
        self.__model_plot.setData(
            intervals, means,
            pen = mkPen((200, 200, 0, 150))
        )

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

        IntervalOffsetGraph.calc_done_event.emit((means[best_idx] <= 16, 1000/tapping_interval))

