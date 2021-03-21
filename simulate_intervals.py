import sys
import time
import numpy as np
import pandas as pd

import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *

from osu_analysis import ManiaActionData, ManiaScoreData
from osu_analysis import BeatmapIO, ReplayIO, Gamemode


class SimulateHitoffsets(QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.data = {
            'distr_t' : [],
            'mean_h' : [],
        }

        self.__init_gui()
        self.show()

        for i in range(100):
            intervals = self.__generate_map_data()

            hit_timings = np.cumsum(intervals)
            hit_offsets = self.__generate_replay_data(intervals, 25, 162.63)

            self.__plot_offset_data(hit_offsets, hit_timings)
            self.__plot_note_interval_data(intervals, hit_offsets)
            self.__solve()

            self.__tick()


    def __init_gui(self):
        self.graphs = {}
        self.area = pyqtgraph.dockarea.DockArea()

        self.__create_graph(
            graph_id  = 'offset_time',
            pos       = 'top',
            widget    = pyqtgraph.PlotWidget(title='Hits scatterplot'),
        )

        self.__create_graph(
            graph_id  = 'offset_mean_scatter',
            pos       = 'bottom',
            widget    = pyqtgraph.PlotWidget(title='Mean distribution'),
        )

        self.__create_graph(
            graph_id  = 'freq_offset',
            pos       = 'right',
            widget    = pyqtgraph.PlotWidget(title='Hits distribution'),
        )

        self.__create_graph(
            graph_id  = 'freq_interval',
            pos       = 'bottom',
            relative_to = self.graphs['freq_offset']['dock'],
            widget    = pyqtgraph.PlotWidget(title='Note intervals distribution'),
        )   

        # Note interval distribtions
        self.region_plot = pyqtgraph.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='r')
        self.graphs['freq_interval']['widget'].addItem(self.region_plot)
        self.graphs['freq_interval']['widget'].setLabel('left', 'Number of notes hit', units='', unitPrefix='')
        self.graphs['freq_interval']['widget'].setLabel('bottom', 'Note interval', units='ms', unitPrefix='')

        # Hits scatterplot
        self.graphs['offset_time']['widget'].addLine(x=None, y=0, pen=pyqtgraph.mkPen('y', width=1))
        self.graphs['offset_time']['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs['offset_time']['widget'].setLabel('bottom', 'Time since start', units='ms', unitPrefix='')

        # Hits distribution
        self.graphs['freq_offset']['widget'].setLabel('left', '# of hits', units='', unitPrefix='')
        self.graphs['freq_offset']['widget'].setLabel('bottom', 'Hit offset', units='ms', unitPrefix='')

        # Mean distribution scatter
        self.fit_plot = self.graphs['offset_mean_scatter']['widget'].plot()
        self.graphs['offset_mean_scatter']['widget'].setLabel('left', 'Mean hit offset', units='ms', unitPrefix='')
        self.graphs['offset_mean_scatter']['widget'].setLabel('bottom', 'Note interval', units='ms', unitPrefix='')

        self.setCentralWidget(self.area)


    def __create_graph(self, graph_id=None, dock_name=' ', pos='bottom', relative_to=None, widget=None):
        if type(widget) == type(None):
            widget = pyqtgraph.PlotWidget()
            
        widget.getViewBox().enableAutoRange()
        
        dock = pyqtgraph.dockarea.Dock(dock_name, size=(500,400))
        dock.addWidget(widget)
        self.area.addDock(dock, pos, relativeTo=relative_to)

        self.graphs[graph_id] = {
            'widget' : widget,
            'dock'   : dock,
            'plot'   : widget.plot()
        }


    def __generate_map_data(self) -> np.array:
        # Have 10,000 notes of intervals 300 to 1, in multiples of 10, scattered randomly
        return np.random.choice(np.arange(0, 500, 5), 10000)


    def __generate_replay_data(self, interval_data: pd.DataFrame, sigma: float, t_min: float) -> np.array:   
        hit_offsets = np.zeros(interval_data.shape)
        
        offset = 0
        for i in range(len(interval_data)):
            if interval_data[i] >= t_min:
                offset = 0
            else:
                offset = 0.5*(t_min - interval_data[i])
        
            hit_offsets[i] = np.random.normal(offset, sigma, 1)
        
        return hit_offsets


    def __plot_offset_data(self, hit_offsets, hit_timings):
        # Calculate view
        xMin = min(hit_timings) - 100
        xMax = max(hit_timings) + 100

        # Set plot data
        self.graphs['offset_time']['plot'].setData(hit_timings, hit_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.graphs['offset_time']['widget'].setLimits(xMin=xMin, xMax=xMax)


    def __get_freq_hist(self, data):
        freq = np.zeros(len(data))
        unique = list(set(data))

        for val in unique:
            val_filter = (data == val)
            freq[val_filter] = np.arange(len(freq[val_filter]))

        return freq


    def __get_freq(self, data):
        unique = np.asarray(list(set(data)))
        freq = np.zeros(len(unique))

        for val in unique:
            freq[unique == val] = np.sum(data == val)

        return unique, freq


    def __get_stats_distr(self, intervals, offsets):
        half_window_width = 10

        win_centers  = []
        means        = []

        note_interv_distr, note_interv_freqs = self.__get_freq(intervals)
        # TODO: This does not take peaks that are less than 50 but are split due to quantization, adding to 50+ if added
        # Example: See first peak https://i.imgur.com/Fy6zR8m.png
        note_interv_peaks = note_interv_distr[note_interv_freqs >= 50]

        for peak in note_interv_peaks:
            start = peak - half_window_width
            end   = peak + half_window_width

            window_offsets = offsets[((start - 1) <= intervals) & (intervals <= (end + 1))]

            win_centers.append(peak)
            means.append(np.mean(window_offsets))

        win_centers = np.asarray(win_centers)
        means       = np.asarray(means)

        sort_idxs = np.argsort(win_centers)
        return win_centers[sort_idxs].tolist(), means[sort_idxs].tolist()


    def __plot_note_interval_data(self, intervals, offsets):
        # Plot note interval distribution
        interv_freqs = self.__get_freq_hist(intervals)
        self.graphs['freq_interval']['plot'].setData(intervals, interv_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

        self.region_plot.setRegion((min(intervals), max(intervals)))
        self.region_plot.setBounds((min(intervals) - 10, max(intervals) + 10))

        # Plot mean & variance distribution w.r.t. note interval
        win_centers, means = self.__get_stats_distr(intervals, offsets)
        self.data['distr_t'].extend(win_centers)
        self.data['mean_h'].extend(means)

        self.graphs['offset_mean_scatter']['plot'].setData(self.data['distr_t'], self.data['mean_h'], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=pyqtgraph.mkBrush(0, 255, 0, 200))


    def __tick(self, ms_sleep=0.1):
        QApplication.instance().processEvents()
        time.sleep(min(ms_sleep, 0.1))


    def __solve(self):
        distr_t = np.asarray(self.data['distr_t'])  # x
        mean_h = np.asarray(self.data['mean_h'])    # y

        # Determine the y offset by getting the average mean offset within 16 ms range (60 fps)
        p0y = np.average(mean_h[(-16 <= mean_h) & (mean_h < 16)])

        # Standard deviation of the points in the non straining region
        # This is used to center the model since the points determined initially are on the edge
        p0y_std = np.std(mean_h[(-16 <= mean_h) & (mean_h < 16)])

        # Get a region of points between 0 and 2 note interval
        # Find the point that is left most in that region
        # Then shift from left towards center of data using stdev
        p0x = min(distr_t[(0 <= mean_h) & (mean_h < 2)]) + 2*p0y_std
        
        # Get a region of point that are greater than 0 mean offset
        # Find the point that is left most in that region and top most in that region.
        # Then shift from top towards center of data using stdev
        p1x = min(distr_t[0 <= distr_t])
        p1y = max(mean_h[0 <= distr_t]) - 2*p0y_std

        t_min = p0x
        r = (p0y - p1y)/(p0x - p1x)
        #r = (0.05 - 0.95*t_min)/t_min
        
        print(f'r = {r:.2f}   t_min = {t_min:.2f} ms ({(1000*60)/(t_min*2):.2f} bpm)  y = {p0y:.2f} ms  err = {self.__calc_err(r, t_min, p0y)/len(distr_t)}')
        curve_fit = self.__softplus_func(distr_t, r, t_min, p0y)

        idx_sort = np.argsort(self.data['distr_t'])
        self.fit_plot.setData(distr_t[idx_sort], curve_fit[idx_sort], pen='y')


    def __calc_err(self, r, t_min, y=0):
        curve_fit = self.__softplus_func(np.asarray(self.data['distr_t']), r, t_min, y)
        return np.sum(np.abs(np.asarray(self.data['mean_h']) - curve_fit))


    def __softplus_func(self, t, r, t_min, y=0):
        lin = r*(t - t_min)
        lin[lin < 100] = np.log(np.exp(lin[lin < 100]) + np.exp(y))
        return lin


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex  = SimulateHitoffsets()
    sys.exit(app.exec_())
