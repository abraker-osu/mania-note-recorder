import pyqtgraph
from pyqtgraph.functions import mkPen

import numpy as np

from osu_analysis import ManiaScoreData

from note_recorder import Data
from graph_mgr import GraphManager

from misc._callback import callback


class NoteIntervalGraph():

    @callback
    class calc_done_event():
        pass

    def __init__(self, graph_mgr: GraphManager, pos, relative_to=None):

        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title='Note intervals freq')
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
        self.__widget.setLabel('left', 'Freq', units = '#', unitPrefix = '')
        self.__widget.setLabel('bottom', 'Interval', units = 'ms', unitPrefix = '')
        self.__widget.setLimits(yMin = -1, yMax = 1000)

        self.__error_bar_graph = pyqtgraph.ErrorBarItem(beam=0)
        self.__widget.addItem(self.__error_bar_graph)


    def plot_data(self, data):
        self.__plot_note_intervals(data)


    def __plot_note_intervals(self, data):
        # Gets hit presses and misses for the latest play
        score_filter = (
              ( data[:, Data.TIMESTAMP] == max(data[:, Data.TIMESTAMP]) )
            & (
                ( data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP )
              | ( data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_MISSP )
            )
        )
        data = data[score_filter]

        # Extract timings and hit_offsets
        note_columns = data[:, Data.KEYS]
        note_timings = data[:, Data.TIMINGS] - data[:, Data.OFFSETS]

        # num_interval size = note timings size - num columns because delta is taken per column
        num_columns = np.unique(note_columns).shape[0]
        num_intervals = note_timings.shape[0] - num_columns

        # Data for each column is put after the other, so `offset` will keep track where to insert it
        interval_data = np.zeros((num_intervals, 4))
        offset = 0

        for column in np.unique(note_columns):
            column_filter = data[:, Data.KEYS] == column

            note_intervals = np.diff(note_timings[column_filter])
            hit_timings_d  = np.diff(data[column_filter, Data.TIMINGS])
            hit_types      = data[column_filter, Data.HIT_TYPE]

            # Set the block of data
            interval_data[offset : note_intervals.shape[0] + offset, 0] = note_intervals
            interval_data[offset : note_intervals.shape[0] + offset, 1] = column
            interval_data[offset : note_intervals.shape[0] + offset, 2] = hit_timings_d
            interval_data[offset : note_intervals.shape[0] + offset, 3] = hit_types[1:]

            # Set offset to the the start of next data block
            offset += note_intervals.shape[0]

        # Process interval data for graphing
        interval_data = interval_data.astype(int)
        y = np.bincount(interval_data[:, 0])

        zero_filter = y != 0
        y = y[zero_filter]

        x = np.arange(np.max(interval_data[:, 0]) + 1)
        x = x[zero_filter]

        # Calculate view
        xMin = -100
        xMax = x[-1] + 100

        # Set plot data
        self.__error_bar_graph.setData(
            x = x, y = y/2, top = y/2, bottom = y/2,
            pen = mkPen((200, 200, 200, 200), width = 5)
        )
        self.__widget.setLimits(xMin = xMin, xMax = xMax)

        NoteIntervalGraph.calc_done_event.emit(interval_data)
