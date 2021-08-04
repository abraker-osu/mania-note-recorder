from PyQt5.QtGui import *
from PyQt5.QtWidgets import QHBoxLayout

import pyqtgraph
from pyqtgraph.Qt import QtCore, QtGui

import numpy as np
import tinydb

from osu_performance_recorder import Recorder, Data



class ManiaMonitor(QtGui.QMainWindow):

    from ._hit_offset_graph import HitOffsetGraph
    from ._hit_distr_graph import HitDistrGraph
    from ._plays_graph import PlaysGraph
    from ._note_offset_graph import NoteOffsetGraph
    from ._note_offset_proc_graph import NoteOffsetProcGraph
    from ._note_distr_graph import NoteDistrGraph
    from ._map_display import MapDisplay
    from ._stddev_distr_graph import StddevDistrGraph
    from ._avg_distr_graph import AvgDistrGraph

    def __init__(self, osu_path):
        QtGui.QMainWindow.__init__(self)

        self.__init_gui()

        self.recorder = Recorder(osu_path, self.__handle_new_replay_qt)
        self.show()


    def __init_gui(self):
        self.graphs = {}
        self.main_widget = QtGui.QWidget()
        self.main_layout = QHBoxLayout()
        self.map_list = QtGui.QListWidget()
        self.splitter = QtGui.QSplitter()
        self.area = pyqtgraph.dockarea.DockArea()

        self.splitter.addWidget(self.map_list)
        self.splitter.addWidget(self.area)
        self.setCentralWidget(self.splitter)

        self.data_cache = None
        self.map_list_data = []
        self.selected_map_id = None

        self.map_list.itemClicked.connect(self.__map_list_click_event)

        ManiaMonitor.PlaysGraph.__init__(self, pos='bottom')
        ManiaMonitor.NoteOffsetGraph.__init__(self, pos='top')
        ManiaMonitor.NoteOffsetProcGraph.__init__(self, pos='below', relative_to='NoteOffsetGraph')
        ManiaMonitor.HitDistrGraph.__init__(self, pos='top')
        ManiaMonitor.HitOffsetGraph.__init__(self, pos='below', relative_to='HitDistrGraph')
        ManiaMonitor.NoteDistrGraph.__init__(self, pos='right', relative_to='NoteDistrGraph')
        ManiaMonitor.AvgDistrGraph.__init__(self, pos='below', relative_to='NoteDistrGraph')
        ManiaMonitor.StddevDistrGraph.__init__(self, pos='below', relative_to='AvgDistrGraph')
        ManiaMonitor.MapDisplay.__init__(self, pos='right', relative_to='AvgStddevDistrGraph')
        
        ManiaMonitor.NoteOffsetGraph.region_changed_event.connect(
            lambda event_data: ManiaMonitor.NoteDistrGraph._plot_data(self, self.data_cache, event_data)
        )

        ManiaMonitor.NoteOffsetProcGraph.region_changed_event.connect(
            lambda event_data: ManiaMonitor.NoteDistrGraph._plot_data(self, self.data_cache, event_data)
        )

        ManiaMonitor.NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: ManiaMonitor.StddevDistrGraph._plot_data(self, event_data)
        )

        ManiaMonitor.NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: ManiaMonitor.AvgDistrGraph._plot_data(self, event_data)
        )

        ManiaMonitor.NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: ManiaMonitor.MapDisplay._plot_stddevs(self, event_data)
        )


    def __handle_new_replay_qt(self, args):
        maps_table, data, title = args
        self.data_cache = data

        if title != None:
            try: self.setWindowTitle(title)
            except AttributeError: pass

        if maps_table != None:
            self.__check_new_maps(maps_table, data)

        data = data[data[:, Data.MAP_ID] == self.selected_map_id]

        ManiaMonitor.MapDisplay._plot_data(self, data)
        ManiaMonitor.HitOffsetGraph._plot_data(self, data)
        ManiaMonitor.HitDistrGraph._plot_data(self, data)
        ManiaMonitor.NoteOffsetGraph._plot_data(self, data)
        ManiaMonitor.NoteOffsetProcGraph._plot_data(self, data)
        ManiaMonitor.PlaysGraph._plot_data(self, data)


    def _create_graph(self, graph_id=None, dock_name=' ', pos='bottom', relative_to=None, widget=None, plot=None):
        if type(widget) == type(None):
            widget = pyqtgraph.PlotWidget()
        
        try: widget.getViewBox().enableAutoRange()
        except AttributeError: pass
        
        dock = pyqtgraph.dockarea.Dock(dock_name, size=(500,400))
        dock.addWidget(widget)
        
        try: relative_dock = self.graphs[relative_to]['dock']
        except KeyError:
            relative_dock = None

        self.area.addDock(dock, pos, relativeTo=relative_dock)

        self.graphs[graph_id] = {
            'widget' : widget,
            'dock'   : dock,
            'plot'   : widget.plot() if plot == None else plot
        }

        if plot != None:
            widget.addItem(plot)


    def __check_new_maps(self, maps_table, data):
        unique_map_ids = np.unique(data[:, Data.MAP_ID])
        new_map_ids = np.setdiff1d(unique_map_ids, self.map_list_data)

        for new_map_id in new_map_ids:
            maps = maps_table.search(tinydb.where('id') == new_map_id)
            if len(maps) == 0:
                continue

            self.map_list.addItem(maps[0]['path'].split('/')[-1])
            self.map_list_data.append(new_map_id)

        if self.selected_map_id == None:
            self.selected_map_id = self.map_list_data[0]


    def __map_list_click_event(self, item):
        selected_map_id = self.map_list_data[self.map_list.row(item)]
        if self.selected_map_id != selected_map_id:
            self.selected_map_id = selected_map_id
            self.__handle_new_replay_qt((None, self.recorder.data, None))
