import pyqtgraph

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data
from .plots.miss_plot import MissPlotItem

from ._callback import callback

np.set_printoptions(suppress=True)


class NoteOffsetGraph():

    @callback
    class region_changed_event(): pass

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Note offsets'),
        )

        # hit_offsets graph
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Note', units='#', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(yMin=-200, yMax=200)

        self.graphs[self.__id]['widget'].addLine(x=None, y=0, pen=pyqtgraph.mkPen((0, 150, 0, 255), width=1))

        self.__region_plot = pyqtgraph.LinearRegionItem([0, 10], 'vertical', swapMode='block', pen='r')
        self.__region_plot.sigRegionChangeFinished.connect(lambda: NoteOffsetGraph.__region_changed(self))
        self.graphs[self.__id]['widget'].addItem(self.__region_plot)


    def _plot_data(self, data):
        NoteOffsetGraph.__plot_hit_offsets(self, data)


    def __plot_hit_offsets(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)

        empty_filter = (data[:, Data.HIT_TYPE] != ManiaScoreData.TYPE_EMPTY)
        data = data[empty_filter]

        # Extract timings and hit_offsets
        plays = np.unique(data[:, Data.TIMESTAMP])
        hit_offsets = data[:, Data.OFFSETS]

        print(f'Num plays: {plays.shape[0]}')

        note_idxs = np.arange(int(hit_offsets.shape[0]/plays.shape[0]))
        note_idxs = np.tile(note_idxs, plays.shape[0])

        hit_offsets = hit_offsets[data_filter]
        note_idxs = note_idxs[data_filter]

        # Calculate view
        xMin = 0
        xMax = np.max(note_idxs)

        # Set plot data
        self.graphs[self.__id]['plot'].setData(note_idxs, hit_offsets, pen=None, symbol='o', symbolSize=2, symbolPen=None, symbolBrush=(100,100,255,150))
        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, xMax=xMax)


    def __region_changed(self):
        NoteOffsetGraph.region_changed_event.emit(self.__region_plot.getRegion())