import os
import re
import time
import math
import json
import glob

import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

import numpy as np

from osu_analysis import ManiaActionData, ManiaScoreData
from osu_analysis import BeatmapIO, ReplayIO, Gamemode
from osu_apiv1 import OsuApiv1

from monitor import Monitor
from api_key import api_key



class ManiaHitOffsetsMonitor(QtGui.QMainWindow):

    def __init__(self, osu_path):
        QtGui.QMainWindow.__init__(self)

        self.__init_gui()

        self.data = {
            'distr_t' : [],
            'mean_h' : [],
            'var_h' : [],
        }

        self.y_bound = 5

        try:
            with open(f'data/hit-offsets.json', 'r') as f:
                self.data = json.loads(f.read())
                self.__update_hits_analysis_data()
        except FileNotFoundError: 
            try: os.makedirs('data')
            except FileExistsError: pass

        self.osu_path = osu_path
        self.monitor = Monitor(osu_path)
        self.monitor.create_replay_monitor('Replay Grapher', self.__graph_results)

        self.show()


    def closeEvent(self, event):
        self.monitor.stop()


    def __init_gui(self):
        self.graphs = {}
        self.area = pyqtgraph.dockarea.DockArea()

        self.__create_graph(
            graph_id  = 'offset_time',
            pos       = 'top',
            widget    = pyqtgraph.PlotWidget(title='Hits scatterplot'),
        )

        self.__create_graph(
            graph_id  = 'offset_mean',
            pos       = 'bottom',
            widget    = pyqtgraph.PlotWidget(title='Mean distribution'),
        )

        self.__create_graph(
            graph_id    = 'offset_var',
            pos         = 'bottom',
            widget      = pyqtgraph.PlotWidget(title='Variance distribution'),
        )

        self.__create_graph(
            graph_id    = 'offset_mean_scatter',
            pos         = 'above',
            relative_to = self.graphs['offset_mean']['dock'],
            widget      = pyqtgraph.PlotWidget(title='Mean distribution Scatter'),
        )

        self.__create_graph(
            graph_id    = 'offset_var_scatter',
            pos         = 'above',
            relative_to = self.graphs['offset_var']['dock'],
            widget      = pyqtgraph.PlotWidget(title='Variance distribution Scatter'),
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

        self.region_plot = pyqtgraph.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='r')
        self.region_plot.sigRegionChanged.connect(self.__region_changed)
        self.graphs['freq_interval']['widget'].addItem(self.region_plot)

        self.graphs['offset_time']['widget'].addLine(x=None, y=0, pen=pyqtgraph.mkPen('r', width=1))
        self.graphs['offset_time']['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs['offset_time']['widget'].setLabel('bottom', 'Time since start', units='ms', unitPrefix='')

        self.graphs['freq_offset']['widget'].setLabel('left', '# of hits', units='', unitPrefix='')
        self.graphs['freq_offset']['widget'].setLabel('bottom', 'Hit offset', units='ms', unitPrefix='')

        self.model_plot = self.graphs['freq_offset']['widget'].plot()

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


    def __graph_results(self, replay_path):
        time.sleep(1)

        try: self.replay = ReplayIO.open_replay(replay_path)
        except Exception as e:
            print(f'Error opening replay: {e}')
            return

        try: beatmap_data = OsuApiv1.fetch_beatmap_info(map_md5=self.replay.beatmap_hash, api_key=api_key)
        except Exception as e:
            print(f'Error fetching beatmap info: {e}')
            return

        if len(beatmap_data) == 0:
            print('Associated beatmap not found. Is it unsubmitted?')
            return

        beatmap_data = beatmap_data[0]
        if int(beatmap_data['mode']) != Gamemode.MANIA:
            print('Only mania gamemode supported for now')            
            return

        path = f'{self.osu_path}/Songs'
        results = glob.glob(f'{path}/{beatmap_data["beatmapset_id"]} *')

        if len(results) == 0:
            print(f'Cannot find folder "{self.osu_path}/Songs/{beatmap_data["beatmapset_id"]} {beatmap_data["artist"]} - {beatmap_data["title"]}"')
            return

        path = results[0]
        version = self.__multiple_replace(beatmap_data["version"], {
            '[' : '[[]',
            ']' : '[]]',
            '/' : '',
            ',' : '',
            ':' : '',
        })
        results = glob.glob1(f'{path}', f'* [[]{version}[]].osu')
        
        if len(results) == 0:
            print(f'Cannot find *.osu file "{path}/{beatmap_data["artist"]} - {beatmap_data["title"]} ({beatmap_data["creator"]}) [{beatmap_data["version"]}].osu"')
            return

        path = f'{path}/{results[0]}'

        self.beatmap = BeatmapIO.open_beatmap(path)
        self.map_data = ManiaActionData.get_action_data(self.beatmap)
        self.replay_data = ManiaActionData.get_action_data(self.replay)
        self.score_data = ManiaScoreData.get_score_data(self.map_data, self.replay_data)

        # Analysis data
        self.note_intervals, self.offsets, self.timings = self.__get_analysis_data()

        self.__update_data()
        self.__update_hits_distr_data()
        self.__update_hits_analysis_data()
        #self.__update_analysis()


    def __update_data(self):
        try: self.setWindowTitle(self.beatmap.metadata.name + ' ' + self.replay.get_name())
        except AttributeError: pass
        
        # Plotting offset distribution
        self.graphs['offset_time']['plot'].setData(self.timings, self.offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.graphs['offset_time']['widget'].setLimits(xMin=min(self.timings) - 100, xMax=max(self.timings) + 100)

        # Plotting note interval distribution
        interv_freqs = self.__get_freq_hist(self.note_intervals)
        self.graphs['freq_interval']['plot'].setData(self.note_intervals, interv_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

        self.region_plot.setRegion((min(self.note_intervals), max(self.note_intervals)))
        self.region_plot.setBounds((min(self.note_intervals) - 10, max(self.note_intervals) + 10))

        # Plotting mean & variance distribution w.r.t. note interval
        win_centers, means, variances = self.__get_stats_distr()
        #means -= np.mean(self.offsets)

        self.graphs['offset_mean']['plot'].setData(win_centers, means, pen='y')
        self.graphs['offset_var']['plot'].setData(win_centers, variances, pen='y')

        self.data['distr_t'].extend(win_centers)
        self.data['mean_h'].extend(means)
        self.data['var_h'].extend(variances)


    def __update_hits_analysis_data(self):
        with open(f'data/hit-offsets.json', 'w') as f:
            json.dump(self.data, f)

        #scatter_brush = [ pyqtgraph.mkBrush(int(mean/60*255), 100, int(255 - (mean/60*255)), 200) for mean in self.data['mean_h'] ]

        #self.graphs['offset_mean_scatter']['plot'].setData(self.data['distr_t'], self.data['mean_h'], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=scatter_brush)
        #self.graphs['offset_var_scatter']['plot'].setData(self.data['distr_t'], self.data['var_h'], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=scatter_brush)

        self.graphs['offset_mean_scatter']['plot'].setData(self.data['distr_t'], self.data['mean_h'], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=pyqtgraph.mkBrush(0, 255, 0, 200))
        self.graphs['offset_var_scatter']['plot'].setData(self.data['distr_t'], self.data['var_h'], pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=pyqtgraph.mkBrush(0, 255, 0, 200))



    def __update_hits_distr_data(self):
        start, end = self.region_plot.getRegion()

        try:
            offsets = self.offsets[(start <= self.note_intervals) & (self.note_intervals <= end)]
        except IndexError as e:
            print(len(self.offsets), len(self.note_intervals), len((start <= self.note_intervals) & (self.note_intervals <= end)))
            print(self.offsets, self.note_intervals)
            print((start <= self.note_intervals) & (self.note_intervals <= end))

            raise e

        if len(offsets) == 0:
            self.graphs['freq_offset']['plot'].setData([], [], pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))
            self.model_plot.setData([], [], pen='y')
        else:
            offset_freqs = self.__get_freq_hist(offsets)
            self.graphs['freq_offset']['plot'].setData(offsets, offset_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

            # Plotting model of offset distribution
            hits = np.arange(-200, 200)
            avg  = np.mean(offsets)
            std  = np.std(offsets)

            if std == 0:
                self.model_plot.setData([], [], pen='y')
                return 

            vec_normal_distr = np.vectorize(self.__normal_distr)
            pdf = vec_normal_distr(hits, avg, std)

            self.model_plot.setData(hits, pdf*len(offsets), pen='y')


    def __update_analysis(self):
        data = np.column_stack((self.data['distr_t'], self.data['mean_h']))
        
        select = (-self.y_bound < data[:, 1]) & (data[:, 1] < self.y_bound)
        idx_min = np.argmin(data[select], 0)
        p_A = data[select][idx_min[0]]

        select = (data[:, 0] <= p_A[0])
        idx_min = np.argmin(data[select], 0)
        p_B = data[select][idx_min[0]]
        
        dxy = p_A - p_B
        m = dxy[1]/dxy[0]
        b = p_A[1] - m*p_A[0]

        # TODO: create a line mx+b to graph


    def __get_analysis_data(self):
        note_intervals = []
        offsets        = []
        timings        = []

        for col in range(int(self.beatmap.difficulty.cs)):
            map_filter  = self.map_data[col] == ManiaActionData.PRESS
            map_col     = self.map_data[col][map_filter].values
            map_times   = self.map_data.index[map_filter].values

            score_col = self.score_data.loc[col]

            hit_filter    = score_col['type'] == ManiaScoreData.TYPE_HITP
            hit_map_times = score_col['map_t'][hit_filter].values

            hit_time_filter = np.isin(map_times, hit_map_times)
            map_interval = np.diff(map_times)[hit_time_filter[1:]]

            offset = (score_col['replay_t'] - score_col['map_t'])[hit_filter].values[1:]
            timing = score_col['replay_t'][hit_filter].values[1:]

            note_intervals.append(map_interval)
            offsets.append(offset)
            timings.append(timing)

        return np.concatenate(note_intervals), np.concatenate(offsets), np.concatenate(timings)


    def __region_changed(self):
        self.__update_hits_distr_data()


    def __normal_distr(self, x, avg, std):
        return 1/(std*((2*math.pi)**0.5))*math.exp(-0.5*((x - avg)/std)**2)


    def __multiple_replace(self, text, dict):
        # Thanks https://stackoverflow.com/a/8687114/3256177
        regex = re.compile("|".join(map(re.escape, dict.keys())))
        return regex.sub(lambda mo: dict[mo.group(0)], text)


    def __get_stats_distr(self):
        half_window_width = 10

        win_centers  = []
        means        = []
        variances    = []

        note_intervals, note_interv_freqs = self.__get_freq(self.note_intervals)
        # TODO: This does not take peaks that are less than 50 but are split due to quantization, adding to 50+ if added
        # Example: See first peak https://i.imgur.com/Fy6zR8m.png
        interval_peaks = note_intervals[note_interv_freqs >= 50]

        for peak in interval_peaks:
            start = peak - half_window_width
            end   = peak + half_window_width

            window_offsets = self.offsets[((start - 1) <= self.note_intervals) & (self.note_intervals <= (end + 1))]

            std = np.std(window_offsets)
            if variances == 0:
                continue

            win_centers.append(peak)
            means.append(np.mean(window_offsets))
            #variances.append(std**2)
            variances.append(std)

        win_centers = np.asarray(win_centers)
        means       = np.asarray(means)
        variances   = np.asarray(variances)

        sort_idxs = np.argsort(win_centers)
        return win_centers[sort_idxs].tolist(), means[sort_idxs].tolist(), variances[sort_idxs].tolist()


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