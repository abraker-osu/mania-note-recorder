import pyqtgraph
import numpy as np

from osu_analysis import ManiaScoreData

from graph_mgr import GraphManager
from note_recorder import Data

from plots.miss_plot import MissPlotItem



class HitOffsetGraph():

    def __init__(self, graph_mgr: GraphManager, pos, relative_to=None):
        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title='Hit offsets')
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
        self.__widget.setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.__widget.setLabel('bottom', 'Time', units='ms', unitPrefix='')
        self.__widget.setLimits(yMin=-200, yMax=200)

        self.__miss_plot = MissPlotItem()
        self.__widget.addItem(self.__miss_plot)

        self.__widget.addLine(x=None, y=0, pen=pyqtgraph.mkPen((0, 150, 0, 255), width=1))

        self.__offset_avg_line = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 255, 0, 150), width=1))
        self.__widget.addItem(self.__offset_avg_line)

        self.__offset_std_line_pos = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.__offset_std_line_neg = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))

        self.__widget.addItem(self.__offset_std_line_pos)
        self.__widget.addItem(self.__offset_std_line_neg)

        self.__offset_avg_plot = self.__widget.plot()

        self.__offset_std_pos = self.__widget.plot()
        self.__offset_std_neg = self.__widget.plot()
        self.__widget.addItem(pyqtgraph.FillBetweenItem(self.__offset_std_pos, self.__offset_std_neg, (100, 100, 255, 50)))


    def plot_data(self, data):
        self.__plot_misses(data)
        self.__plot_hit_offsets(data)
        self.__plot_avg_global(data)
        self.__plot_avg_local(data)


    def __plot_hit_offsets(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)
        data = data[data_filter]

        # Extract timings and hit_offsets
        hit_timings = data[:, Data.TIMINGS]
        hit_offsets = data[:, Data.OFFSETS]

        # Set plot data
        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            hit_timings, hit_offsets,
            pen = None, symbol = 'o', symbolPen = None, symbolSize = 2, symbolBrush = (100, 100, 255, 200)
        )

        # Calculate view
        xMin = min(hit_timings) - 100
        xMax = max(hit_timings) + 100

        self.__widget.setLimits(xMin = xMin, xMax = xMax)


    def __plot_misses(self, data):
        # Determine what was the latest play
        data_filter = \
            (data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP])) & \
            (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISSP)
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
