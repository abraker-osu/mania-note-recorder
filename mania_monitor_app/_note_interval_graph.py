import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from ._utils import Utils


class NoteIntervalGraph():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Intervals'),
        )

        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Number of notes hit', units='', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Note interval', units='ms', unitPrefix='')

        self.__miss_plot = self.graphs[self.__id]['widget'].plot()
        #self.region_plot = pyqtgraph.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='r')
        #self.region_plot.sigRegionChanged.connect(self.__region_changed)
        #self.graphs[self.__id]['widget'].addItem(self.region_plot)

        self.graphs[self.__id]['widget'].setLimits(yMin=-1)
        

    #def __region_changed(self):
    #    self.__update_hit_distr_graphs(self.hit_note_intervals, self.hit_offsets)


    def _plot_data(self, data):
        NoteIntervalGraph.__plot_intervals_hits(self, data)
        NoteIntervalGraph.__plot_intervals_misses(self, data)
        

    def __plot_intervals_hits(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)
        data = data[data_filter]

        # Get intervals for notes on the specific columns they occur at
        note_intervals = data[:, [Data.COL1, Data.COL2, Data.COL3, Data.COL4]]
        note_intervals = note_intervals[np.arange(note_intervals.shape[0]), data[:, Data.KEYS].astype(int)]
        note_intervals = note_intervals[np.isfinite(note_intervals)]

        # Plot note interval distribution
        interv_freqs = Utils.get_freq_hist(note_intervals)
        self.graphs[self.__id]['plot'].setData(note_intervals, interv_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

        #self.region_plot.setRegion((min(note_intervals), max(note_intervals)))
        #self.region_plot.setBounds((min(note_intervals) - 10, max(note_intervals) + 10))

        # Calculate view
        xMin = min(note_intervals) - 100
        xMax = max(note_intervals) + 100
        yMax = max(interv_freqs) + 10

        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, xMax=xMax, yMax=yMax)


    def __plot_intervals_misses(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISS)
        data = data[data_filter]

        # Get intervals for notes on the specific columns they occur at
        note_intervals = data[:, [Data.COL1, Data.COL2, Data.COL3, Data.COL4]]
        note_intervals = note_intervals[np.arange(note_intervals.shape[0]), data[:, Data.KEYS].astype(int)]
        note_intervals = note_intervals[np.isfinite(note_intervals)]

        # Plot note interval distribution
        interv_freqs = Utils.get_freq_hist(note_intervals)
        self.__miss_plot.setData(note_intervals, interv_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(100,100,100,150), symbolBrush=(255, 0,0,150))

        #self.region_plot.setRegion((min(note_intervals), max(note_intervals)))
        #self.region_plot.setBounds((min(note_intervals) - 10, max(note_intervals) + 10))


