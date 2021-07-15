import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from ._utils import Utils


class NoteDistrGraph():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Note Distribution'),
        )

        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', '# Hits', units='', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(xMin=-200, yMin=-1, xMax=200)

        self.graphs[self.__id]['widget'].addLine(x=0, y=None, pen=pyqtgraph.mkPen((0, 150, 0, 255), width=1))

        self.__distr_avg_line = pyqtgraph.InfiniteLine(angle=90, pen=pyqtgraph.mkPen((255, 255, 0, 150), width=1))
        self.graphs[self.__id]['widget'].addItem(self.__distr_avg_line)

        self.__distr_std_line_pos = pyqtgraph.InfiniteLine(angle=90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.graphs[self.__id]['widget'].addItem(self.__distr_std_line_pos)

        self.__distr_std_line_neg = pyqtgraph.InfiniteLine(angle=90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.graphs[self.__id]['widget'].addItem(self.__distr_std_line_neg)

        self.__model_plot = self.graphs[self.__id]['widget'].plot()


    def _plot_data(self, data, note_range):
        NoteDistrGraph.__plot_hit_distr(self, data, note_range)
        NoteDistrGraph.__plot_stats(self, data, note_range)


    def __plot_hit_distr(self, data, note_range):
        if type(note_range) == type(None):
            return

        start, end = note_range
        if start == end: end += 1

        # Determine what was the latest play
        data_filter = \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)

        # Extract timings and hit_offsets
        plays = np.unique(data[:, Data.TIMESTAMP])
        hit_offsets = data[:, Data.OFFSETS]
        num = np.tile(np.arange(int(hit_offsets.shape[0]/plays.shape[0])), plays.shape[0])

        num_filter = (start <= num) & (num <= end) & data_filter
        hit_offsets = hit_offsets[num_filter]
        num = num[num_filter]

        # Get a histogram of offsets for each ms
        hit_freqs = Utils.get_freq_hist(hit_offsets)
        self.graphs[self.__id]['plot'].setData(hit_offsets, hit_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

        # Calculate view
        if len(hit_freqs) > 0:
            yMax = max(hit_freqs) + 10
            self.graphs[self.__id]['widget'].setLimits(yMax=yMax)


    def __plot_stats(self, data, note_range):
        if type(note_range) == type(None):
            return

        start, end = note_range
        if start == end: end += 1

        # Determine what was the latest play
        data_filter = \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)

        # Extract timings and hit_offsets
        plays = np.unique(data[:, Data.TIMESTAMP])
        hit_offsets = data[:, Data.OFFSETS]
        num = np.tile(np.arange(int(hit_offsets.shape[0]/plays.shape[0])), plays.shape[0])

        num_filter = (start <= num) & (num <= end) & data_filter
        hit_offsets = hit_offsets[num_filter]
        num = num[num_filter]

        mean_offset = np.mean(hit_offsets)
        std_offset  = np.std(hit_offsets)

        # Set plot data
        self.__distr_avg_line.setValue(mean_offset)
        self.__distr_std_line_pos.setValue(std_offset*2 + mean_offset)
        self.__distr_std_line_neg.setValue(-std_offset*2 + mean_offset)

        # Special case if standard deviation is point-like
        # Then there is no model to display
        if std_offset == 0:
            self.__model_plot.setData([], [], pen='y')
        else:
            # Plotting model of offset distribution (normal distribution)
            x = np.arange(-ManiaScoreData.neg_hit_range, ManiaScoreData.pos_hit_range)

            # Calculate normal distribution
            pdf = np.vectorize(Utils.normal_distr)(x, mean_offset, std_offset)
            self.__model_plot.setData(x, pdf*len(hit_offsets), pen='y')