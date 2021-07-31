import pyqtgraph

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from .plots.miss_plot import MissPlotItem

from ._callback import callback

np.set_printoptions(suppress=True)


class NoteOffsetProcGraph():

    @callback
    class region_changed_event(): pass

    @callback
    class calc_done_event(): pass

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Note offsets (2σ)'),
        )

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Note', units='#', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(yMin=-200, yMax=200)

        self.graphs[self.__id]['widget'].addLine(x=None, y=0, pen=pyqtgraph.mkPen((0, 150, 0, 255), width=1))

        self.__region_plot = pyqtgraph.LinearRegionItem([0, 10], 'vertical', swapMode='block', pen='r')
        self.__region_plot.sigRegionChangeFinished.connect(lambda: NoteOffsetProcGraph.__region_changed(self))
        self.graphs[self.__id]['widget'].addItem(self.__region_plot)

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam=0.5)
        self.graphs[self.__id]['widget'].addItem(self.__error_bar_graph)


    def _plot_data(self, data):
        NoteOffsetProcGraph.__plot_hit_offsets(self, data)


    def __plot_hit_offsets(self, data):
        # Filter out everything but press releated scorings
        score_filter = (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP) | \
                       (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISSP)
        data = data[score_filter]

        # Extract timings and hit_offsets
        plays = np.unique(data[:, Data.TIMESTAMP])
        hit_offsets = data[:, Data.OFFSETS]

        note_idxs = np.arange(int(hit_offsets.shape[0]/plays.shape[0]))
        num = np.tile(note_idxs, plays.shape[0])

        means = np.zeros(note_idxs.shape[0])
        stddevs = np.zeros(note_idxs.shape[0])

        miss_filter = \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)

        for x in note_idxs:
            offsets = hit_offsets[(num == x) & miss_filter]
            if offsets.shape[0] == 0:
                continue

            means[x]   = np.mean(offsets)
            stddevs[x] = np.std(offsets)

        # Calculate view
        xMin = -1
        xMax = np.max(num) + 1
        yMax = np.max(means+3*stddevs)
        yMin = np.min(means-3*stddevs)

        # Set plot data
        self.graphs[self.__id]['plot'].setData(note_idxs, means, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))
        self.__error_bar_graph.setData(x=note_idxs, y=means, top=2*stddevs, bottom=2*stddevs)

        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

        NoteOffsetProcGraph.calc_done_event.emit((means, 2*stddevs))


    def __region_changed(self):
        NoteOffsetProcGraph.region_changed_event.emit(self.__region_plot.getRegion())