import pyqtgraph
import numpy as np

from osu_analysis import ManiaScoreData

from graph_mgr import GraphManager
from note_recorder import Data

from misc._utils import Utils



class NoteDistrGraph():

    def __init__(self, graph_mgr: GraphManager, pos, relative_to = None):
        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title = 'Note Distribution')
        self.__graph_mgr = graph_mgr

        self.__graph_mgr.create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = self.__widget,
        )

        plot_item = self.__widget.getPlotItem()
        assert isinstance(plot_item, pyqtgraph.PlotItem)

        plot_item.getAxis('left').enableAutoSIPrefix(False)
        plot_item.getAxis('bottom').enableAutoSIPrefix(False)
        self.__widget.setLabel('left', '# Hits', units = '', unitPrefix = '')
        self.__widget.setLabel('bottom', 'Offset', units = 'ms', unitPrefix = '')
        self.__widget.setLimits(xMin = -200, yMin = -1, xMax = 200)

        self.__widget.addLine(
            x = 0, y = None,
            pen = pyqtgraph.mkPen((0, 150, 0, 255), width = 1)
        )

        self.__distr_avg_line = pyqtgraph.InfiniteLine(angle = 90, pen=pyqtgraph.mkPen((255, 255, 0, 150), width = 1))
        self.__widget.addItem(self.__distr_avg_line)

        self.__distr_std_line_pos = pyqtgraph.InfiniteLine(angle = 90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width = 1))
        self.__widget.addItem(self.__distr_std_line_pos)

        self.__distr_std_line_neg = pyqtgraph.InfiniteLine(angle = 90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width = 1))
        self.__widget.addItem(self.__distr_std_line_neg)

        self.__model_plot = self.__widget.plot()


    def plot_data(self, data: np.ndarray, note_range: tuple[int, int] | None):
        self.__plot_hit_distr(data, note_range)
        self.__plot_stats(data, note_range)


    def __plot_hit_distr(self, data: np.ndarray, note_range: tuple[int, int] | None):
        if isinstance(note_range, type(None)):
            return

        start, end = note_range
        if start == end:
            end += 1

        # Determine what was the latest play
        data_filter = (
            ( data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP )
        )

        # Extract timings and hit_offsets
        plays = np.unique(data[:, Data.TIMESTAMP])
        hit_offsets = data[:, Data.OFFSETS]
        num = np.tile(np.arange(int(hit_offsets.shape[0]/plays.shape[0])), plays.shape[0])

        num_filter = (start <= num) & (num <= end) & data_filter
        hit_offsets = hit_offsets[num_filter]
        num = num[num_filter]

        # Get a histogram of offsets for each ms
        hit_freqs = Utils.get_freq_hist(hit_offsets)

        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            hit_offsets, hit_freqs,
            pen = None, symbol = 'o', symbolSize = 5, symbolPen = (255,255,255,150), symbolBrush = (0,0,255,150)
        )

        # Calculate view
        if len(hit_freqs) > 0:
            yMax = max(hit_freqs) + 10
            self.__widget.setLimits(yMax = yMax)


    def __plot_stats(self, data, note_range):
        if type(note_range) == type(None):
            return

        start, end = note_range
        if start == end:
            end += 1

        # Determine what was the latest play
        data_filter = \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)

        # Extract timings and hit_offsets
        plays       = np.unique(data[:, Data.TIMESTAMP])
        hit_offsets = data[:, Data.OFFSETS]
        num         = np.tile(np.arange(int(hit_offsets.shape[0] / plays.shape[0])), plays.shape[0])

        num_filter  = (start <= num) & (num <= end) & data_filter
        hit_offsets = hit_offsets[num_filter]
        num         = num[num_filter]

        mean_offset = np.mean(hit_offsets)
        std_offset  = np.std(hit_offsets)

        # Set plot data
        self.__distr_avg_line.setValue(mean_offset)
        self.__distr_std_line_pos.setValue(mean_offset + std_offset*2)
        self.__distr_std_line_neg.setValue(mean_offset - std_offset*2)

        # Special case if standard deviation is point-like
        # Then there is no model to display
        if std_offset == 0:
            self.__model_plot.setData([], [], pen = 'y')
        else:
            # Plotting model of offset distribution (normal distribution)
            x = np.arange(-ManiaScoreData.neg_hit_range, ManiaScoreData.pos_hit_range)

            # Calculate normal distribution
            pdf = np.vectorize(Utils.normal_distr)(x, mean_offset, std_offset)
            self.__model_plot.setData(x, pdf*len(hit_offsets), pen = 'y')
