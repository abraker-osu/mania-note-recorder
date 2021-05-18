import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data


class ReleaseOffsetGraph():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Release offsets'),
        )

        # rel_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Time', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(yMin=-200, yMax=200)

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
        ReleaseOffsetGraph.__plot_rel_offsets(self, data)
        ReleaseOffsetGraph.__plot_avg_global(self, data)
        ReleaseOffsetGraph.__plot_avg_local(self, data)


    def __plot_rel_offsets(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITR)

        # Extract timings and rel_offsets
        rel_timings = data[:, Data.TIMINGS][data_filter]
        rel_offsets = data[:, Data.OFFSETS][data_filter]

        # Calculate view
        try: 
            xMin = min(rel_timings) - 100
            xMax = max(rel_timings) + 100
        except:
            # There were no releases
            self.graphs[self.__id]['plot'].setData([], [])
            return

        # Set plot data
        self.graphs[self.__id]['plot'].setData(rel_timings, rel_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, xMax=xMax)


    def __plot_avg_global(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITR)

        # Extract timings and rel_offsets
        rel_offsets = data[:, Data.OFFSETS][data_filter]
        if rel_offsets.shape[0] == 0:
            self.__offset_avg_line.hide()
            self.__offset_std_line_pos.hide()
            self.__offset_std_line_neg.hide()
            return
        else:
            self.__offset_avg_line.show()
            self.__offset_std_line_pos.show()
            self.__offset_std_line_neg.show()

        mean_offset = np.mean(rel_offsets)
        std_offset = np.std(rel_offsets)

        # Set plot data
        self.__offset_avg_line.setValue(mean_offset)
        self.__offset_std_line_pos.setValue(std_offset*2 + mean_offset)
        self.__offset_std_line_neg.setValue(-std_offset*2 + mean_offset)


    def __plot_avg_local(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITR)

        # Extract timings and rel_offsets
        rel_timings = data[:, Data.TIMINGS][data_filter]
        rel_offsets = data[:, Data.OFFSETS][data_filter]

        # Calculate view
        try: 
            xMin = min(rel_timings) - 100
            xMax = max(rel_timings) + 100
        except:
            # There were no releases
            self.__offset_avg_plot.clear()
            self.__offset_std_pos.clear()
            self.__offset_std_neg.clear()
            return
        
        bin_width = 500
        num_bins = (xMax - xMin)/bin_width
        
        bins = np.linspace(xMin, xMax, int(num_bins), endpoint=True)  # Create bin ranges
        idxs = np.digitize(rel_timings, bins)    # Get indices for each bin range (start with 1)

        offset_avgs = np.asarray([ rel_offsets[idxs == i].mean() if len(rel_offsets[idxs == i]) > 0 else 0 for i in range(1, len(bins)) ])
        offset_stds = np.asarray([ rel_offsets[idxs == i].std() if len(rel_offsets[idxs == i]) > 0 else 0 for i in range(1, len(bins)) ])

        self.__offset_avg_plot.setData(bins[:-1] + bin_width/2, offset_avgs, pen=pyqtgraph.mkPen((255, 255, 0, 50)))
        self.__offset_std_pos.setData(bins[:-1] + bin_width/2, offset_stds*2 + offset_avgs, pen=pyqtgraph.mkPen((0, 0, 0, 0)))
        self.__offset_std_neg.setData(bins[:-1] + bin_width/2, -offset_stds*2 + offset_avgs, pen=pyqtgraph.mkPen((0, 0, 0, 0)))