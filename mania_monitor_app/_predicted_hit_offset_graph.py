import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from .plots.miss_plot import MissPlotItem
from ._utils import Utils


class PredictedHitOffsetGraph():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Predicted Hit offsets'),
        )

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Time', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(yMin=-200, yMax=200)


    def _plot_data(self, data, event_data):
        PredictedHitOffsetGraph.__plot_hit_offsets(self, data, event_data)


    def __plot_hit_offsets(self, data, event_data):
        r, t_min, y = event_data

        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            ((data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP) | (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISS))
        data_slice = data[data_filter]

        # Get intervals for notes on the specific columns they occur at
        note_intervals = data_slice[:, [Data.COL1, Data.COL2, Data.COL3, Data.COL4]]
        note_intervals = note_intervals[np.arange(note_intervals.shape[0]), data_slice[:, Data.KEYS].astype(int)]
        note_inf_filter = np.isfinite(note_intervals)
        note_intervals = note_intervals[note_inf_filter]

        # Get hit timings, and filter out to match note interval size
        hit_timings = data_slice[:, Data.TIMINGS]
        hit_timings = hit_timings[note_inf_filter]

        predicted_offsets = Utils.softplus_func(note_intervals, r, t_min, y)

        # Calculate view
        xMin = min(hit_timings) - 100
        xMax = max(hit_timings) + 100

        # Set plot data
        self.graphs[self.__id]['plot'].setData(hit_timings, predicted_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, xMax=xMax)