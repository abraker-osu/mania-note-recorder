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

        for i in range(1000):
            for t_min in range(0, 105, 5):
                intervals = self.__generate_map_data()

                hit_timings = np.cumsum(intervals)
                hit_offsets = self.__generate_replay_data(intervals, 25, t_min)

                self.__plot_offset_data(hit_offsets, hit_timings)
                self.__plot_note_interval_data(intervals, hit_offsets, t_min)

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
            widget    = pyqtgraph.PlotWidget(title='Hit offset at t=0'),
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
        self.graphs['offset_mean_scatter']['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs['offset_mean_scatter']['widget'].setLabel('bottom', 't_min', units='ms', unitPrefix='')

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
        return np.random.choice(np.arange(0, 100, 5), 1000)


    def __generate_replay_data(self, interval_data: pd.DataFrame, sigma: float, t_min: float) -> np.array:   
        hit_offsets = np.zeros(interval_data.shape)
        
        offset = 0
        for i in range(len(interval_data)):
            if interval_data[i] >= t_min:
                offset = 0
            else:
                offset = t_min - interval_data[i]
        
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
        return win_centers[sort_idxs], means[sort_idxs]


    def __plot_note_interval_data(self, intervals, offsets, t_min):
        # Plot note interval distribution
        interv_freqs = self.__get_freq_hist(intervals)
        self.graphs['freq_interval']['plot'].setData(intervals, interv_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

        self.region_plot.setRegion((min(intervals), max(intervals)))
        self.region_plot.setBounds((min(intervals) - 10, max(intervals) + 10))

        # Plot mean & variance distribution w.r.t. note interval
        win_centers, means = self.__get_stats_distr(intervals, offsets)
        self.data['mean_h'].extend(means[win_centers < 5].tolist())
        self.data['distr_t'].extend(np.full(len(means[win_centers < 5]), t_min).tolist())

        self.graphs['offset_mean_scatter']['plot'].setData(self.data['distr_t'], self.data['mean_h'], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=pyqtgraph.mkBrush(0, 255, 0, 200))

        # Calc model
        t_min = np.asarray(self.data['distr_t'])
        offset = np.asarray(self.data['mean_h'])

        mean_x0 = np.mean(t_min[(-2 <= t_min) & (t_min <= 2)])
        mean_y0 = np.mean(offset[(-2 <= t_min) & (t_min <= 2)])

        mean_x1 = np.mean(t_min[(98 <= t_min) & (t_min <= 102)])
        mean_y1 = np.mean(offset[(98 <= t_min) & (t_min <= 102)])

        slope = (mean_y0 - mean_y1)/(mean_x0 - mean_x1)
        b0 = -slope*mean_x0 + mean_y0
        print(f'y = {slope}*t_min + {b0}')


    def __tick(self, ms_sleep=0.1):
        QApplication.instance().processEvents()
        time.sleep(min(ms_sleep, 0.1))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex  = SimulateHitoffsets()
    sys.exit(app.exec_())
