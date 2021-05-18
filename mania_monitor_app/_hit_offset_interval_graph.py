import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *
import numpy as np

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Data

from ._utils import Utils
from ._callback import callback


class HitOffsetIntervalGraph():

    @callback
    class model_updated_event(): pass

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Average Hit Offset for Intervals'),
        )

        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Avg hit offset', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Note interval', units='ms', unitPrefix='')

        self.__model_plot = self.graphs[self.__id]['widget'].plot()

        self.__model_std_line_x_pos = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.__model_std_line_x_neg = pyqtgraph.InfiniteLine(angle=0, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))

        self.__model_std_line_y_pos = pyqtgraph.InfiniteLine(angle=90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.__model_std_line_y_neg = pyqtgraph.InfiniteLine(angle=90, pen=pyqtgraph.mkPen((255, 150, 0, 150), width=1))
        self.__model_avg_line_x = pyqtgraph.InfiniteLine(angle=90, pen=pyqtgraph.mkPen((150, 255, 0, 150), width=1))

        self.graphs[self.__id]['widget'].addItem(self.__model_std_line_x_pos)
        self.graphs[self.__id]['widget'].addItem(self.__model_std_line_x_neg)
        #self.graphs[self.__id]['widget'].addItem(self.__model_std_line_y_pos)
        #self.graphs[self.__id]['widget'].addItem(self.__model_std_line_y_neg)
        #self.graphs[self.__id]['widget'].addItem(self.__model_avg_line_x)
        self.graphs[self.__id]['widget'].setLimits(yMin=-1)
        

    def _plot_data(self, data, time_range=None):
        HitOffsetIntervalGraph.__plot_offset_intervals(self, data, time_range)
        HitOffsetIntervalGraph.__plot_model(self, data)
        

    def __plot_offset_intervals(self, data, time_range=None):
        half_window_width = 10
        min_interval_peak = 100
        unique_timestamps = np.unique(data[:, Data.TIMESTAMP])

        if type(time_range) != type(None):
            start, end = time_range
            unique_timestamps = unique_timestamps[(start <= unique_timestamps) & (unique_timestamps <= end)]
        
        x_note_intervals = []
        y_mean_offsets   = []
        timestamps       = []

        # Got through the list of plays recorded
        for timestamp in unique_timestamps:
            # Get score data for the play
            data_filter = \
                (data[:, Data.TIMESTAMP] == timestamp) & \
                (data[:, Data.HIT_TYPE] == ManiaScoreData.TYPE_HITP)
            data_slice = data[data_filter]

            # Get intervals for notes on the specific columns they occur at
            note_intervals = data_slice[:, [Data.COL1, Data.COL2, Data.COL3, Data.COL4]]
            note_intervals = note_intervals[np.arange(note_intervals.shape[0]), data_slice[:, Data.KEYS].astype(int)]
            note_inf_filter = np.isfinite(note_intervals)
            note_intervals = note_intervals[note_inf_filter]

            # Get note interval distribution
            interv_freqs = Utils.get_freq_hist(note_intervals)
            note_intervals = note_intervals[interv_freqs >= min_interval_peak]
            note_intervals_peaks = np.unique(note_intervals)
            # TODO: figure out how to filter out peaks that are within +/- 1 of another peak

            # Get hit offsets, and filter out to match note interval size
            hit_offsets = data_slice[:, Data.OFFSETS]
            hit_offsets = hit_offsets[note_inf_filter]
            hit_offsets = hit_offsets[interv_freqs >= min_interval_peak]

            # Collect offsets in relation to peaks
            for peak in note_intervals_peaks:
                start = peak - half_window_width
                end   = peak + half_window_width
                offsets = hit_offsets[((start - 1) <= note_intervals) & (note_intervals <= (end + 1))]
                
                y_mean_offsets.append(np.mean(offsets))
                x_note_intervals.append(peak)
                timestamps.append(timestamp)

        # Calculate view
        xMin = min(x_note_intervals) - 100
        xMax = max(x_note_intervals) + 100
        yMax = max(y_mean_offsets) + 10
        yMin = min(y_mean_offsets) - 10

        # Calculate color
        is_latest   = max(data[:, Data.TIMESTAMP]) == np.asarray(timestamps)
        symbol_size = is_latest*2 + 2

        symbolBrush = pyqtgraph.ColorMap(
            np.array([ 0, 1 ]),            # Is latest?
            np.array([                     # Colors
                [ 100, 100, 255, 200  ],
                [ 0,   255, 0,   255  ],
            ]),
        ).map(is_latest, 'qcolor')

        self.__x_note_intervals = np.asarray(x_note_intervals)
        self.__y_mean_offsets   = np.asarray(y_mean_offsets)

        self.graphs[self.__id]['plot'].setData(x_note_intervals, y_mean_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=symbol_size, symbolBrush=symbolBrush)
        self.graphs[self.__id]['widget'].setLimits(xMin=xMin, yMin=yMin, xMax=xMax, yMax=yMax)


    def __plot_model(self, data):
        # Determine the y offset by getting the average mean offset within 16 ms range (60 fps)
        hor_area = self.__y_mean_offsets[(-16 <= self.__y_mean_offsets) & (self.__y_mean_offsets < 16)]
        p0y = np.average(hor_area)

        # Standard deviation of the points in the non straining region
        # This is used to center the model since the points determined initially are on the edge
        p0y_std = np.std(hor_area)

        top_std = p0y_std*2 + p0y
        btm_std = -p0y_std*2 + p0y
        '''
        # Get area of points above the 2*std line
        top_area_x = self.__x_note_intervals[top_std <= self.__y_mean_offsets]
        top_area_y = self.__y_mean_offsets[top_std <= self.__y_mean_offsets]

        # Get center of top area
        p1x = np.average(top_area_x, weights=1/top_area_x**2)
        p1y = np.average(top_area_y)

        # Get stdev of top area on vertical axis
        p1x_std = np.std(top_area_x)
        lft_std = -p1x_std + p1x
        rgt_std = p1x_std + p1x

        # Get area of points with area bounded by the 2*std_x and 2*std_y lines
        lft_area_x = self.__x_note_intervals[(lft_std < self.__x_note_intervals) & (self.__x_note_intervals < rgt_std)]
        lft_area_y = self.__y_mean_offsets[(btm_std < self.__y_mean_offsets) & (self.__y_mean_offsets < top_std)]
        
        # Get center of left area
        p2x = np.average(lft_area_x)
        print(lft_std, rgt_std)
        p2y = np.average(lft_area_y)

        # Get slope (p2x, p2y) to (p1x, p1y)
        r = (p2y - p1y)/(p2x - p1x)

        # tmin is at p2x
        t_min = p2x
        '''

        # Get a region of points between 0 and 2 note interval
        # Find the point that is left most in that region
        # Then shift from left towards center of data using stdev
        p0x = min(self.__x_note_intervals[(0 <= self.__y_mean_offsets) & (self.__y_mean_offsets < 2)]) # + 2*p0y_std
        
        # Get a region of point that are greater than 0 mean offset
        # Find the point that is left most in that region and top most in that region.
        # Then shift from top towards center of data using stdev
        p1x = min(self.__x_note_intervals[0 <= self.__x_note_intervals])
        p1y = max(self.__y_mean_offsets[0 <= self.__x_note_intervals]) #- 2*p0y_std

        r = (p0y - p1y)/(p0x - p1x)
        t_min = p0x


        err = Utils.calc_err(self.__x_note_intervals, self.__y_mean_offsets, r, t_min, p0y)/len(self.__x_note_intervals)
        print(f'r = {r:.2f}   t_min = {t_min:.2f} ms ({(1000*60)/(t_min*2):.2f} bpm)  y = {p0y:.2f} ms  err = {err}')
        curve_fit = Utils.softplus_func(self.__x_note_intervals, r, t_min, p0y)

        idx_sort = np.argsort(self.__x_note_intervals)
        self.__model_plot.setData(self.__x_note_intervals[idx_sort], curve_fit[idx_sort], pen='y')

        self.__model_std_line_x_pos.setValue(top_std)
        self.__model_std_line_x_neg.setValue(btm_std)
        '''
        self.__model_std_line_y_pos.setValue(lft_std)
        self.__model_std_line_y_neg.setValue(rgt_std)
        self.__model_avg_line_x.setValue(p1x)
        '''

        HitOffsetIntervalGraph.model_updated_event.emit((r, t_min, p0y))