import os
import re
import time
import math
import json
import glob

import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *

import numpy as np

from osu_analysis import ManiaActionData, ManiaScoreData
from osu_analysis import BeatmapIO, ReplayIO, Gamemode
from osu_apiv1 import OsuApiv1

from monitor import Monitor
from api_key import api_key
from miss_plot import MissPlotItem



class ManiaHitOffsetsMonitor(QtGui.QMainWindow):

    new_replay_event = QtCore.pyqtSignal(str)

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

                self.show()
                self.__solve2()
        except FileNotFoundError: 
            try: os.makedirs('data')
            except FileExistsError: pass

        self.osu_path = osu_path
        self.monitor = Monitor(osu_path)
        self.monitor.create_replay_monitor('Replay Grapher', self.__handle_new_replay)

        self.new_replay_event.connect(self.__handle_new_replay_qt)
        #self.show()


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

        # Note interval distribtions
        self.region_plot = pyqtgraph.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='r')
        self.region_plot.sigRegionChanged.connect(self.__region_changed)
        self.graphs['freq_interval']['widget'].addItem(self.region_plot)
        self.graphs['freq_interval']['widget'].setLabel('left', 'Number of notes hit', units='', unitPrefix='')
        self.graphs['freq_interval']['widget'].setLabel('bottom', 'Note interval', units='ms', unitPrefix='')

        # Hits scatterplot
        self.miss_plot = MissPlotItem([])
        self.graphs['offset_time']['widget'].addItem(self.miss_plot)

        self.graphs['offset_time']['widget'].addLine(x=None, y=0, pen=pyqtgraph.mkPen('y', width=1))
        self.graphs['offset_time']['widget'].setLabel('left', 'Hit offset', units='ms', unitPrefix='')
        self.graphs['offset_time']['widget'].setLabel('bottom', 'Time since start', units='ms', unitPrefix='')

        # Hits distribution
        self.graphs['freq_offset']['widget'].setLabel('left', '# of hits', units='', unitPrefix='')
        self.graphs['freq_offset']['widget'].setLabel('bottom', 'Hit offset', units='ms', unitPrefix='')

        # Mean distribution scatter
        self.fit_plot = self.graphs['offset_mean_scatter']['widget'].plot()
        self.model_plot = self.graphs['freq_offset']['widget'].plot()
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


    def __handle_new_replay(self, replay_path):
        time.sleep(1)
        self.new_replay_event.emit(replay_path)


    def __handle_new_replay_qt(self, replay_path):
        print('New replay detected!')

        try: replay, beatmap = self.__get_files(replay_path)
        except TypeError: return

        try: self.setWindowTitle(beatmap.metadata.name + ' ' + replay.get_name())
        except AttributeError: pass

        map_data = ManiaActionData.get_action_data(beatmap)
        replay_data = ManiaActionData.get_action_data(replay)
        score_data = ManiaScoreData.get_score_data(map_data, replay_data)

        # Analysis data
        self.hit_note_intervals, self.hit_offsets, hit_timings = self.__get_hit_data(beatmap.difficulty.cs, map_data, score_data)
        miss_note_intervals, miss_timings = self.__get_miss_data(beatmap.difficulty.cs, map_data, score_data)

        self.__plot_offset_data(self.hit_offsets, hit_timings, miss_timings)
        self.__plot_note_interval_data(self.hit_note_intervals, self.hit_offsets, hit_timings)
        self.__update_hit_distr_graphs(self.hit_note_intervals, self.hit_offsets)
        self.__update_hits_analysis_data()
        self.__solve2()


    def __get_files(self, replay_path):
        print('Loading replay...')

        try: replay = ReplayIO.open_replay(replay_path)
        except Exception as e:
            print(f'Error opening replay: {e}')
            return

        if replay.game_mode != Gamemode.MANIA:
            print('Only mania gamemode supported for now')            
            return

        print(replay.mods)

        if replay.mods.has_mod('DT') or replay.mods.has_mod('NC'):
            print('DT and NC is not supported yet!')
            return 

        print('Determining beatmap...')

        try: beatmap_data = OsuApiv1.fetch_beatmap_info(map_md5=replay.beatmap_hash, api_key=api_key)
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
            #',' : '',
            ':' : '',
        })
        results = glob.glob1(f'{path}', f'* [[]{version}[]].osu')
        
        if len(results) == 0:
            print(f'Cannot find *.osu file "{path}/{beatmap_data["artist"]} - {beatmap_data["title"]} ({beatmap_data["creator"]}) [{beatmap_data["version"]}].osu"')
            return

        print('Loading beatmap...')

        path = f'{path}/{results[0]}'
        beatmap = BeatmapIO.open_beatmap(path)

        return replay, beatmap


    def __get_hit_data(self, num_keys, map_data, score_data):
        note_intervals = []
        offsets        = []
        timings        = []

        for col in range(int(num_keys)):
            # Get note times where needed to press for current column
            map_filter = map_data[col] == ManiaActionData.PRESS
            map_times  = map_data.index[map_filter].values

            # Get scoring data for the current column
            score_col = score_data.loc[col]

            # Get score times associated with successful press for current column
            hit_filter    = score_col['type'] == ManiaScoreData.TYPE_HITP
            hit_map_times = score_col['map_t'][hit_filter].values

            # Correlate map's note press timings to scoring press times
            # Then get interval between the hit note and previous
            hit_time_filter = np.isin(map_times, hit_map_times)
            map_interval = np.diff(map_times)[hit_time_filter[1:]]

            # Get replay hitoffsets and timings for those offsets
            offset = (score_col['replay_t'] - score_col['map_t'])[hit_filter].values[1:]
            timing = score_col['replay_t'][hit_filter].values[1:]

            # Append data for column to overall data
            note_intervals.append(map_interval)
            offsets.append(offset)
            timings.append(timing)

            if len(offset) != len(map_interval):
                print(f'len(offsets) != len(note_intervals) for col {col}')
                print(f'len(map_times) = {len(map_times)}  len(hit_map_times) = {len(hit_map_times)}')
                print(f'len(hit_filter) = {len(hit_filter)}  len(hit_time_filter[1:]) = {len(hit_time_filter[1:])}')

        return np.concatenate(note_intervals), np.concatenate(offsets), np.concatenate(timings)


    def __get_miss_data(self, num_keys, map_data, score_data):
        note_intervals = []
        timings        = []

        for col in range(int(num_keys)):
            # Get note times where needed to press for current column
            map_filter = map_data[col] == ManiaActionData.PRESS
            map_times  = map_data.index[map_filter].values

            # Get scoring data for the current column
            score_col = score_data.loc[col]

            # Get score times associated with successful press for current column
            hit_filter    = score_col['type'] == ManiaScoreData.TYPE_MISS
            hit_map_times = score_col['map_t'][hit_filter].values

            # Correlate map's note press timings to scoring press times
            # Then get interval between the hit note and previous
            hit_time_filter = np.isin(map_times, hit_map_times)
            map_interval = np.diff(map_times)[hit_time_filter[1:]]

            # Get replay timings for misses
            timing = score_col['replay_t'][hit_filter].values[1:]

            # Append data for column to overall data
            note_intervals.append(map_interval)
            timings.append(timing)

        return np.concatenate(note_intervals), np.concatenate(timings)


    def __plot_offset_data(self, hit_offsets, hit_timings, miss_timings):
        # Calculate view
        try:
            xMin = min(min(hit_timings), min(miss_timings)) - 100
            xMax = max(max(hit_timings), max(miss_timings)) + 100
        except ValueError:
            # No misses were made
            try: 
                xMin = min(hit_timings) - 100
                xMax = max(hit_timings) + 100
            except ValueError: 
                # No hits were made
                return

        # Set plot data
        self.graphs['offset_time']['plot'].setData(hit_timings, hit_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=2, symbolBrush=(100, 100, 255, 200))
        self.graphs['offset_time']['widget'].setLimits(xMin=xMin, xMax=xMax)
        self.miss_plot.setData(miss_timings)


    def __plot_note_interval_data(self, note_intervals, offsets, timings):
        # Plot note interval distribution
        interv_freqs = self.__get_freq_hist(note_intervals)
        self.graphs['freq_interval']['plot'].setData(note_intervals, interv_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

        self.region_plot.setRegion((min(note_intervals), max(note_intervals)))
        self.region_plot.setBounds((min(note_intervals) - 10, max(note_intervals) + 10))

        # Plot mean & variance distribution w.r.t. note interval
        win_centers, means, variances = self.__get_stats_distr(note_intervals, offsets)
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


    def __update_hit_distr_graphs(self, note_intervals, offsets):
        start, end = self.region_plot.getRegion()

        # Collect offsets that fall within the selected region
        try:
            offsets = offsets[(start <= note_intervals) & (note_intervals <= end)]
        except IndexError as e:
            print(len(offsets), len(note_intervals))
            print(offsets, note_intervals)
            print((start <= note_intervals) & (note_intervals <= end))

            raise e

        # If there is no data, clear all displayed
        if len(offsets) == 0:
            self.graphs['freq_offset']['plot'].setData([], [], pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))
            self.model_plot.setData([], [], pen='y')
        # Otherwise display it
        else:
            # Get a histogram of offsets for each ms
            offset_freqs = self.__get_freq_hist(offsets)
            self.graphs['freq_offset']['plot'].setData(offsets, offset_freqs, pen=None, symbol='o', symbolSize=5, symbolPen=(255,255,255,150), symbolBrush=(0,0,255,150))

            # Plotting model of offset distribution (normal distribution)
            hits = np.arange(-ManiaScoreData.neg_hit_range, ManiaScoreData.pos_hit_range)
            avg  = np.mean(offsets)
            std  = np.std(offsets)

            # Special case if standard deviation is point-like
            # Then there is no model to display
            if std == 0:
                self.model_plot.setData([], [], pen='y')
                return 

            # Calculate normal distribution
            vec_normal_distr = np.vectorize(self.__normal_distr)
            pdf = vec_normal_distr(hits, avg, std)

            self.model_plot.setData(hits, pdf*len(offsets), pen='y')


    def __region_changed(self):
        self.__update_hit_distr_graphs(self.hit_note_intervals, self.hit_offsets)


    def __normal_distr(self, x, avg, std):
        return 1/(std*((2*math.pi)**0.5))*math.exp(-0.5*((x - avg)/std)**2)


    def __multiple_replace(self, text, dict):
        # Thanks https://stackoverflow.com/a/8687114/3256177
        regex = re.compile('|'.join(map(re.escape, dict.keys())))
        return regex.sub(lambda mo: dict[mo.group(0)], text)


    def __get_stats_distr(self, note_intervals, offsets):
        half_window_width = 10

        win_centers  = []
        means        = []
        variances    = []

        note_interv_distr, note_interv_freqs = self.__get_freq(note_intervals)
        # TODO: This does not take peaks that are less than 50 but are split due to quantization, adding to 50+ if added
        # Example: See first peak https://i.imgur.com/Fy6zR8m.png
        note_interv_peaks = note_interv_distr[note_interv_freqs >= 50]

        for peak in note_interv_peaks:
            start = peak - half_window_width
            end   = peak + half_window_width

            window_offsets = offsets[((start - 1) <= note_intervals) & (note_intervals <= (end + 1))]

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


    def __solve(self):
        distr_t = np.asarray(self.data['distr_t'])
        mean_h = np.asarray(self.data['mean_h'])

        p0x = min(distr_t[(0 <= mean_h) & (mean_h < 2)])
        p1x = min(distr_t[0 <= distr_t])
        p1y = max(mean_h[0 <= distr_t])

        t_min = p0x
        r = (0 - p1y)/(p0x - p1x)
        
        print(f'r = {r}   t_min = {t_min}  err = {self.__calc_err(r, t_min)/len(distr_t)}')
        curve_fit = self.__softplus_func(distr_t, r, t_min)

        idx_sort = np.argsort(self.data['distr_t'])
        self.fit_plot.setData(distr_t[idx_sort], curve_fit[idx_sort], pen='y')


    def __solve2(self):
        r = -0.5
        t_min = 200
        y = 0

        d = 0.1

        a_r = 0.01
        a_t = 1
        a_y = 1

        r_err_hist = np.zeros(3)
        t_err_hist = np.zeros(3)
        y_err_hist = np.zeros(3)

        step = 500

        distr_t = np.asarray(self.data['distr_t'])
        mean_h = np.asarray(self.data['mean_h'])

        while step > 0:
            step -= 1

            # Calculate error
            r_err = self.__calc_err(r + d, t_min, y) - self.__calc_err(r, t_min, y)
            t_err = self.__calc_err(r, t_min + d, y) - self.__calc_err(r, t_min, y)
            y_err = self.__calc_err(r, t_min, y + d) - self.__calc_err(r, t_min, y)

            # Anti oscilation algorithm
            r_err_hist[1:] = r_err_hist[:-1]
            r_err_hist[0] = r_err

            if (self.__is_opposite_sign(r_err_hist[0], r_err_hist[1])) and self.__is_opposite_sign(r_err_hist[1], r_err_hist[2]):
                a_r /= 2

            t_err_hist[1:] = t_err_hist[:-1]
            t_err_hist[0] = t_err

            if (self.__is_opposite_sign(t_err_hist[0], t_err_hist[1])) and self.__is_opposite_sign(t_err_hist[1], t_err_hist[2]):
                a_t /= 2

            y_err_hist[1:] = y_err_hist[:-1]
            y_err_hist[0] = y_err

            if (self.__is_opposite_sign(y_err_hist[0], y_err_hist[1])) and self.__is_opposite_sign(y_err_hist[1], y_err_hist[2]):
                a_y /= 2

            # Calculate new param values
            r = r - a_r*r_err
            t_min = t_min - a_t*t_err
            y = y - a_y*y_err

            # Visualize
            #print((r_err, t_err, y_err, self.__calc_err(r, t_min, y)/len(distr_t)), (r, t_min, y), (a_r, a_t, a_y))
            #print(r_err_hist)

            curve_fit = self.__softplus_func(distr_t, r, t_min, y)

            idx_sort = np.argsort(self.data['distr_t'])
            self.fit_plot.setData(distr_t[idx_sort], curve_fit[idx_sort], pen='y')

            #self.__tick()

        print(f'r = {r:.2f}   t_min = {t_min:.2f} ms ({(1000*60)/(t_min*2):.2f} bpm)  y = {y:.2f} ms   err = {self.__calc_err(r, t_min, y)/len(distr_t)}')


    def __calc_err(self, r, t_min, y=0):
        curve_fit = self.__softplus_func(np.asarray(self.data['distr_t']), r, t_min, y)
        return np.sum(np.abs(np.asarray(self.data['mean_h']) - curve_fit))


    def __softplus_func(self, t, r, t_min, y=0):
        lin = r*(t - t_min)
        lin[lin < 100] = np.log(np.exp(lin[lin < 100]) + 1)
        return lin + y


    def __is_opposite_sign(self, a, b):
        return (a >= 0) != (b >= 0)


    def __tick(self, ms_sleep=0.1):
        QApplication.instance().processEvents()
        time.sleep(min(ms_sleep, 0.1))