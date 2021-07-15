import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from .plots.miss_plot import MissPlotItem


class HitOffsetGraph():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Hit offsets'),
        )

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Time', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(yMin=-200, yMax=200)

        self.__miss_plot = MissPlotItem()
        self.graphs[self.__id]['widget'].addItem(self.__miss_plot)

        self.graphs[self.__id]['widget'].addLine(x=None, y=0, pen=pyqtgraph.mkPen((0, 150, 0, 255), width=1))

        self.__offset_avg_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 255, 0, 150), width=1))
        self.graphs[self.__id]['widget'].addItem(self.__offset_avg_line)

        self.__offset_std_line_pos = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.__offset_std_line_neg = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))

        self.graphs[self.__id]['widget'].addItem(self.__offset_std_line_pos)
        self.graphs[self.__id]['widget'].addItem(self.__offset_std_line_neg)

        self.__offset_avg_plot = self.graphs[self.__id]['widget'].plot()

        self.__offset_std_pos = self.graphs[self.__id]['widget'].plot()
        self.__offset_std_neg = self.graphs[self.__id]['widget'].plot()
        self.graphs[self.__id]['widget'].addItem(pyqtgraph.FillBetweenItem(self.__offset_std_pos, self.__offset_std_neg, (100, 100, 255, 50)))


    def _plot_data(self, data):
        HitOffsetGraph.__plot_misses(self, data)
        HitOffsetGraph.__plot_hit_offsets(self, data)
        HitOffsetGraph.__plot_avg_global(self, data)
        HitOffsetGraph.__plot_avg_local(self, data)


    def __plot_hit_offsets(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)
        data = data[data_filter]

        # Extract timings and hit_offsets
        hit_timings = data[:, Data.TIMINGS]
        hit_offsets = data[:, Data.OFFSETS]

        # Calculate view
        xMin = min(hit_timings) - 100
        xMax = max(hit_timings) + 100

        # Set plot data
        self.graphs[self.__id]['plot'].setData(hit_timings, hit_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, xMax=xMax)


    def __plot_misses(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISS)
        data = data[data_filter]

        # Extract data and plot
        hit_timings = data[:, Data.TIMINGS]
        self.__miss_plot.setData(hit_timings)


    def __plot_avg_global(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)
        data = data[data_filter]

        # Extract timings and hit_offsets
        hit_offsets = data[:, Data.OFFSETS]
        mean_offset = np.mean(hit_offsets)
        std_offset = np.std(hit_offsets)

        # Set plot data
        self.__offset_avg_line.setValue(mean_offset)
        self.__offset_std_line_pos.setValue(std_offset*2 + mean_offset)
        self.__offset_std_line_neg.setValue(-std_offset*2 + mean_offset)

        print(f'mean = {mean_offset:.2f} ms    std = {std_offset:.2f} ms')


    def __plot_avg_local(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)

        # Extract timings and hit_offsets
        hit_timings = data[:, Data.TIMINGS][data_filter]
        hit_offsets = data[:, Data.OFFSETS][data_filter]

        # Calculate view
        xMin = min(hit_timings)
        xMax = max(hit_timings)
        
        bin_width = 500
        num_bins = (xMax - xMin)/bin_width
        
        bins = np.linspace(xMin, xMax, int(num_bins), endpoint=True)  # Create bin ranges
        idxs = np.digitize(hit_timings, bins)    # Get indices for each bin range (start with 1)

        offset_avgs = np.asarray([ hit_offsets[idxs == i].mean() if len(hit_offsets[idxs == i]) > 0 else 0 for i in range(1, len(bins)) ])
        offset_stds = np.asarray([ hit_offsets[idxs == i].std() if len(hit_offsets[idxs == i]) > 0 else 0 for i in range(1, len(bins)) ])

        self.__offset_avg_plot.setData(bins[:-1] + bin_width/2, offset_avgs, pen=pyqtgraph.mkPen((255, 255, 0, 50)))
        self.__offset_std_pos.setData(bins[:-1] + bin_width/2, offset_stds*2 + offset_avgs, pen=pyqtgraph.mkPen((0, 0, 0, 0)))
        self.__offset_std_neg.setData(bins[:-1] + bin_width/2, -offset_stds*2 + offset_avgs, pen=pyqtgraph.mkPen((0, 0, 0, 0)))