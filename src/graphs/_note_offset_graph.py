import pyqtgraph
import numpy as np

from osu_analysis import ManiaScoreData

from note_recorder import Data
from graph_mgr import GraphManager

from misc._callback import callback


np.set_printoptions(suppress=True)


class NoteOffsetGraph():

    @callback
    class region_changed_event(): pass

    def __init__(self, graph_mgr: GraphManager, pos, relative_to = None):
        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title = 'Note offsets')
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
        self.__widget.setLabel('left', 'Hit offset', units = 'ms', unitPrefix = '')
        self.__widget.setLabel('bottom', 'Note', units = '#', unitPrefix = '')
        self.__widget.setLimits(yMin = -200, yMax = 200)

        self.__widget.addLine(
            x = None, y = 0,
            pen = pyqtgraph.mkPen((0, 150, 0, 255), width=1)
        )

        self.__region_plot = pyqtgraph.LinearRegionItem([0, 10], 'vertical', swapMode='block', pen='r')
        self.__region_plot.sigRegionChangeFinished.connect(lambda: NoteOffsetGraph.__region_changed(self))
        self.__widget.addItem(self.__region_plot)


    def plot_data(self, data: np.ndarray):
        self.__plot_hit_offsets(data)


    def __plot_hit_offsets(self, data: np.ndarray):
        # Gets hit presses and misses throuhout all plays
        score_filter = (
              ( data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP )
            | ( data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISSP )
        )
        data = data[score_filter]

        # Determine the number of plays there are, and number of notes in each play
        plays = np.unique(data[:, Data.TIMESTAMP])
        num_notes_total = data.shape[0]
        num_notes = int(num_notes_total/plays.shape[0])

        print(f'Num plays: {plays.shape[0]}     num notes: {num_notes_total/plays.shape[0]}   total: {num_notes_total}')

        #num_notes1 = int(data.shape[0]/plays.shape[0])
        #num_notes_plays = [ data[data[:, Data.TIMESTAMP] == play].shape[0] for play in plays ]
        #print(num_notes1, num_notes_plays)

        # Build note indexing data
        note_idxs = np.arange(num_notes)
        note_idxs = np.tile(note_idxs, plays.shape[0])

        miss_filter = (
            ( data[:, Data.HIT_TYPE] != ManiaScoreData.TYPE_MISSP )
        )

        hit_offsets = data[miss_filter, Data.OFFSETS]
        note_idxs = note_idxs[miss_filter]

        # Set plot data
        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            note_idxs, hit_offsets,
            pen = None, symbol = 'o', symbolSize = 2, symbolPen = None, symbolBrush = (100,100,255,150)
        )

        # Calculate view
        xMin = 0
        xMax = np.max(note_idxs)

        self.__widget.setLimits(xMin = xMin, xMax = xMax)


    def __region_changed(self):
        NoteOffsetGraph.region_changed_event.emit(self.__region_plot.getRegion())
