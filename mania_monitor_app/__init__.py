import os
import sys
import time
import numpy as np

import pyqtgraph
from pyqtgraph import dockarea
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtGui import *

from osu_analysis import ManiaScoreData
from osu_performance_recorder import Recorder, Data



class ManiaMonitor(QtGui.QMainWindow):

    from ._hit_offset_graph import HitOffsetGraph
    from ._rel_offset_graph import ReleaseOffsetGraph
    from ._note_interval_graph import NoteIntervalGraph
    from ._hit_distr_graph import HitDistrGraph
    from ._hit_offset_interval_graph import HitOffsetIntervalGraph
    from ._plays_graph import PlaysGraph
    from ._predicted_hit_offset_graph import PredictedHitOffsetGraph

    def __init__(self, osu_path):
        QtGui.QMainWindow.__init__(self)

        self.__init_gui()

        self.recorder = Recorder(osu_path, self.__handle_new_replay_qt)
        self.show()


    def __init_gui(self):
        self.graphs = {}
        self.area = pyqtgraph.dockarea.DockArea()
        self.setCentralWidget(self.area)

        self.data_cache = None

        ManiaMonitor.NoteIntervalGraph.__init__(self, pos='top')
        ManiaMonitor.HitDistrGraph.__init__(self, pos='left')
        ManiaMonitor.ReleaseOffsetGraph.__init__(self, pos='bottom', relative_to='HitDistrGraph')
        ManiaMonitor.HitOffsetGraph.__init__(self, pos='below', relative_to='ReleaseOffsetGraph')
        ManiaMonitor.PredictedHitOffsetGraph.__init__(self, pos='below', relative_to='HitOffsetGraph')
        ManiaMonitor.HitOffsetIntervalGraph.__init__(self, pos='bottom', relative_to='NoteIntervalGraph')
        ManiaMonitor.PlaysGraph.__init__(self, pos='bottom')

        ManiaMonitor.PlaysGraph.region_changed_event.connect(
            lambda event_data: ManiaMonitor.HitOffsetIntervalGraph._plot_data(self, self.data_cache, event_data)
        )

        ManiaMonitor.HitOffsetIntervalGraph.model_updated_event.connect(
            lambda event_data: ManiaMonitor.PredictedHitOffsetGraph._plot_data(self, self.data_cache, event_data)
        )


    def __handle_new_replay_qt(self, args):
        data, title = args
        self.data_cache = data

        try: self.setWindowTitle(title)
        except AttributeError: pass

        ManiaMonitor.HitOffsetGraph._plot_data(self, data)
        ManiaMonitor.ReleaseOffsetGraph._plot_data(self, data)
        ManiaMonitor.NoteIntervalGraph._plot_data(self, data)
        ManiaMonitor.HitDistrGraph._plot_data(self, data)
        ManiaMonitor.HitOffsetIntervalGraph._plot_data(self, data)
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