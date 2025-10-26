import os

import numpy as np
import json

import tinydb
from tinydb.table import Table

from PyQt6 import QtGui
from PyQt6 import QtWidgets

from pyqtgraph import dockarea

from graph_mgr import GraphManager
from app_cfg  import AppConfig
from note_recorder import NoteRecorder, Data

from graphs._hit_offset_graph       import HitOffsetGraph
from graphs._hit_distr_graph        import HitDistrGraph
from graphs._plays_graph            import PlaysGraph
from graphs._note_offset_graph      import NoteOffsetGraph
from graphs._note_offset_proc_graph import NoteOffsetProcGraph
from graphs._note_distr_graph       import NoteDistrGraph
from graphs._map_display            import MapDisplay
from graphs._stddev_distr_graph     import StddevDistrGraph
from graphs._avg_distr_graph        import AvgDistrGraph
from graphs._note_interval_graph    import NoteIntervalGraph
from graphs._interval_offset_graph  import IntervalOffsetGraph


class App(QtWidgets.QMainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        print('Checking app config...')

        if not os.path.isdir(AppConfig.cfg['osu_dir']):
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
            msg.setWindowTitle('osu! folder config')
            msg.setText('Locate your osu! folder')
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec()

            osu_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, 'Select osu! folder'))
            if len(osu_dir) == 0:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setWindowTitle('osu! folder config')
                msg.setText(
                    'Invalid osu! path! Alternatively find config.json in app folder and edit it.\n'
                    'Then restart the app.\n'
                    'Make sure to use double backslashes for osu! path (ex: "C:\\\\Games\\\\osu!")\n'
                )
                msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
                msg.exec()
                return

            AppConfig.cfg['osu_dir'] = osu_dir
            with open('config.json', 'w') as f:
                json.dump(AppConfig.cfg, f, indent=4)

        print('Initializing gui...')

        self.__init_gui()
        os.makedirs('data', exist_ok = True)

        self.score_db = tinydb.TinyDB('data/scores.json')
        self.nps_table = self.score_db.table('nps')

        print('Initializing recorder...')

        self.__note_recorder = NoteRecorder(AppConfig.cfg['osu_dir'], self.__handle_new_replay_qt)
        self.show()


    def __init_gui(self):
        self.nps_action = QtGui.QAction("&Top nps", self)
        self.nps_action.triggered.connect(lambda: self.__update_top_nps(show = True))

        self.new_action = QtGui.QAction("&New", self)
        self.new_action.triggered.connect(self.__do_new_recording)

        self.open_action = QtGui.QAction("&Open", self)
        self.open_action.triggered.connect(self.__open_recording_dialog)

        self.view_menu = QtWidgets.QMenu("&View", self)
        self.view_menu.addAction(self.nps_action)

        self.file_menu = QtWidgets.QMenu("&File", self)
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)

        self.menu_bar = QtWidgets.QMenuBar(self)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.view_menu)

        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QHBoxLayout()
        self.map_list    = QtWidgets.QListWidget()
        self.splitter    = QtWidgets.QSplitter()
        self.area        = dockarea.DockArea()

        self.splitter.addWidget(self.map_list)
        self.splitter.addWidget(self.area)
        self.setCentralWidget(self.splitter)

        self.setMenuBar(self.menu_bar)

        self.score_list = QtWidgets.QListWidget()

        self.__graph_mgr       = GraphManager(self.area)
        self.map_list_data     = []
        self.data_cache        = None
        self.map_list.currentRowChanged.connect(self.__map_list_click_event)

        self.selected_map_hash = 0
        self.selected_map_mods = 0

        self.__note_offset_graph      = NoteOffsetGraph(self.__graph_mgr, pos = 'top')
        self.__note_offset_proc_graph = NoteOffsetProcGraph(self.__graph_mgr, pos = 'below', relative_to = 'NoteOffsetGraph')
        self.__hit_distr_graph        = HitDistrGraph(self.__graph_mgr, pos = 'top')
        self.__hit_offset_graph       = HitOffsetGraph(self.__graph_mgr, pos = 'below', relative_to = 'HitDistrGraph')
        self.__note_distr_graph       = NoteDistrGraph(self.__graph_mgr, pos = 'right', relative_to = 'NoteDistrGraph')
        self.__avg_distr_graph        = AvgDistrGraph(self.__graph_mgr, pos = 'below', relative_to = 'NoteDistrGraph')
        self.__stddev_distr_graph     = StddevDistrGraph(self.__graph_mgr, pos = 'below', relative_to = 'AvgDistrGraph')
        self.__interval_offset_graph  = IntervalOffsetGraph(self.__graph_mgr, pos = 'below', relative_to = 'StddevDistrGraph')
        self.__note_interval_graph    = NoteIntervalGraph(self.__graph_mgr, pos = 'right', relative_to = 'AvgStddevDistrGraph')
        self.__map_display            = MapDisplay(self.__graph_mgr, pos = 'below', relative_to = 'NoteIntervalGraph')
        self.__plays_graph            = PlaysGraph(self.__graph_mgr, pos = 'bottom')

        NoteOffsetGraph.region_changed_event.connect(
            lambda event_data: self.__note_distr_graph.plot_data(self.data_cache, event_data)
        )

        NoteOffsetProcGraph.region_changed_event.connect(
            lambda event_data: self.__note_offset_proc_graph.plot_data(self.data_cache, event_data)
        )

        NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: self.__stddev_distr_graph.plot_data(event_data)
        )

        NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: self.__avg_distr_graph.plot_data(event_data)
        )

        NoteIntervalGraph.calc_done_event.connect(
            lambda event_data: self.__interval_offset_graph.plot_data(event_data)
        )

        NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: self.__map_display.plot_stddevs(event_data)
        )

        IntervalOffsetGraph.calc_done_event.connect(
            lambda event_data: self.__record_nps(event_data)
        )


    def __handle_new_replay_qt(self, args: tuple[Table | None, np.ndarray, str | None]):
        maps_table, data, title = args
        self.data_cache = data

        print(f'Handling new replay "{title}"...')

        if not isinstance(title, type(None)):
            try:
                self.setWindowTitle(title)
            except AttributeError:
                pass

        if not isinstance(maps_table, type(None)):
            is_new_maps = self.__check_new_maps(maps_table, data)

            if is_new_maps:
                self.map_list.setCurrentRow(len(self.map_list_data) - 1)

        # Select data
        tmp = data.astype(np.uint64)
        data = data[(tmp[:, Data.HASH] + tmp[:, Data.MODS]) == int(self.selected_map_hash, 16)]

        self.__map_display.plot_data(data)
        self.__hit_offset_graph.plot_data(data)
        self.__hit_distr_graph.plot_data(data)
        self.__note_offset_graph.plot_data(data)
        self.__note_offset_proc_graph.plot_data(data)
        self.__plays_graph.plot_data(data)
        self.__note_interval_graph.plot_data(data)


    def __decode_map_hash(self, map_hash: str) -> tuple[str, str]:
        hash_str = map_hash[:-4]
        mods_str = map_hash[-4:]

        mods = ''
        if int(mods_str, 16) & (1 << 0): mods += 'DT'
        if int(mods_str, 16) & (1 << 1): mods += 'HT'
        mods = f' +{mods}' if len(mods) != 0 else ''

        return hash_str, mods


    def __check_new_maps(self, maps_table, data: np.ndarray) -> bool:
        is_new_maps = False
        vhex = np.vectorize(lambda x: hex(x)[2:])
        data = data.astype(np.uint64)

        # Determine new play data
        unique_map_hahes = np.unique(data[:, Data.HASH] + data[:, Data.MODS])
        new_map_hashes   = np.setdiff1d(vhex(unique_map_hahes), self.map_list_data)

        # Go through unlisted maps
        for new_map_hash in new_map_hashes:
            # Decode hash
            map_hash, mods = self.__decode_map_hash(new_map_hash)

            # Find the map the hash is related to in db
            maps = maps_table.search(tinydb.where('md5h') == map_hash)
            if len(maps) == 0:
                self.map_list.addItem(new_map_hash)
                self.map_list_data.append(new_map_hash)
                is_new_maps = True
                continue

            # Add map to list
            self.map_list.addItem(maps[0]['path'].split('/')[-1] + mods)
            self.map_list_data.append(new_map_hash)
            is_new_maps = True

        if self.selected_map_hash == None:
            self.selected_map_hash = new_map_hash

        return is_new_maps


    def __map_list_click_event(self, idx: int):
        selected_map_hash = self.map_list_data[idx]

        if self.selected_map_hash != selected_map_hash:
            self.selected_map_hash = selected_map_hash
            self.__handle_new_replay_qt((None, self.__note_recorder.data, None))

            self.__update_top_nps()


    def __do_new_recording(self):
        self.map_list.clear()
        self.map_list_data.clear()
        self.__note_recorder.new_file()


    def __open_recording_dialog(self):
        name_filter = 'npy files (*.npy)'

        file_pathname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open data file',  f'./data', name_filter)[0]
        if len(file_pathname) == 0:
            return

        self.map_list.clear()
        self.map_list_data.clear()
        self.__note_recorder.open_file(file_pathname)


    def __record_nps(self, nps_data: tuple):
        is_definite, nps = nps_data
        interval = 1000/nps

        if is_definite:
            print(f'Min average player tapping rate: {nps:.2f} nps ({interval:.2f} ms)')
        else:
            print(f'Min average player tapping rate: > {nps:.2f} nps (< {interval:.2f} ms)')

        play_hash = int(self.selected_map_hash, 16)
        data = self.nps_table.search(tinydb.where('hash') == play_hash)

        if len(data) == 0:
            self.nps_table.upsert({ 'nps' : nps, 'hash' : play_hash }, tinydb.where('hash') == play_hash)
            return

        old_nps = data[0]['nps']
        if old_nps < nps:
            self.nps_table.upsert({ 'nps' : nps }, tinydb.where('hash') == play_hash)

        self.__update_top_nps()


    def __update_top_nps(self, show: bool = False):
        # Get nps data from db
        data = self.nps_table.search(tinydb.where('nps').exists())

        nps = np.asarray([ round(entry['nps'], 2) for entry in data ])
        hashes = list([ entry['hash'] for entry in data ])

        # Figure out how to sort the nps
        idx_sort = np.argsort(nps)[::-1]

        # Add the sorted nps to qlist widget
        self.score_list.clear()
        for score in nps[idx_sort]:
            self.score_list.addItem(f'{score} nps')

        # Resolve current hash's sorted index
        play_hash = int(self.selected_map_hash, 16)

        try: hash_idx = np.where(idx_sort == hashes.index(play_hash))[0][0]
        except ValueError as e:
            print(f'{e}')
            print(f'Entries: {data}')
            return

        # Highlight the corresponding value in the list
        self.score_list.setCurrentRow(hash_idx)

        # Show window
        if show:
            self.score_list.show()
