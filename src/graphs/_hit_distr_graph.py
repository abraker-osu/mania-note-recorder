import pyqtgraph
import numpy as np

from osu_analysis import ManiaScoreData

from note_recorder import Data
from graph_mgr import GraphManager

from misc._utils import Utils



class HitDistrGraph():

    def __init__(self, graph_mgr: GraphManager, pos, relative_to = None):

        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title = 'Hit Distribution')
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

        self.__widget.addLine(x = 0, y = None, pen = pyqtgraph.mkPen((0, 150, 0, 255), width = 1))

        self.__distr_avg_line = pyqtgraph.InfiniteLine(angle = 90, pen=pyqtgraph.mkPen((255, 255, 0, 150), width = 1))
        self.__widget.addItem(self.__distr_avg_line)

        self.__distr_std_line_pos = pyqtgraph.InfiniteLine(angle = 90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width = 1))
        self.__widget.addItem(self.__distr_std_line_pos)

        self.__distr_std_line_neg = pyqtgraph.InfiniteLine(angle = 90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width = 1))
        self.__widget.addItem(self.__distr_std_line_neg)

        self.__model_plot = self.__widget.plot()


    def plot_data(self, data: np.ndarray):
        self.__plot_hit_distr(data)
        self.__plot_stats(data)


    def __plot_hit_distr(self, data: np.ndarray):
        # Determine what was the latest play
        data_filter = \
            ( data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP]) ) & \
            ( data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP )

        # Extract timings and hit_offsets
        hit_offsets = data[:, Data.OFFSETS][data_filter]

        # Get a histogram of offsets for each ms
        hit_freqs = Utils.get_freq_hist(hit_offsets)

        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            hit_offsets, hit_freqs,
            pen = None, symbol = 'o', symbolSize = 5, symbolPen = (255,255,255,150), symbolBrush = (0,0,255,150)
        )

        # Calculate view
        yMax = max(hit_freqs)*1.1
        self.__widget.setLimits(yMax = yMax)


    def __plot_stats(self, data: np.ndarray):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)

        # Extract timings and hit_offsets
        hit_offsets = data[:, Data.OFFSETS][data_filter]
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
