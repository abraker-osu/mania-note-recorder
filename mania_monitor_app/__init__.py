import pyqtgraph
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.QtGui import *

from osu_performance_recorder import Recorder, Data



class ManiaMonitor(QtGui.QMainWindow):

    from ._hit_offset_graph import HitOffsetGraph
    from ._hit_distr_graph import HitDistrGraph
    from ._plays_graph import PlaysGraph
    from ._note_offset_graph import NoteOffsetGraph
    from ._note_offset_proc_graph import NoteOffsetProcGraph
    from ._note_distr_graph import NoteDistrGraph
    from ._map_display import MapDisplay
    from ._avg_stddev_distr_graph import AvgStddevDistrGraph

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

        ManiaMonitor.PlaysGraph.__init__(self, pos='bottom')
        ManiaMonitor.NoteOffsetGraph.__init__(self, pos='top')
        ManiaMonitor.NoteOffsetProcGraph.__init__(self, pos='below', relative_to='NoteOffsetGraph')
        ManiaMonitor.HitDistrGraph.__init__(self, pos='top')
        ManiaMonitor.HitOffsetGraph.__init__(self, pos='below', relative_to='HitDistrGraph')
        ManiaMonitor.NoteDistrGraph.__init__(self, pos='right', relative_to='NoteDistrGraph')
        ManiaMonitor.AvgStddevDistrGraph.__init__(self, pos='below', relative_to='NoteDistrGraph')
        ManiaMonitor.MapDisplay.__init__(self, pos='right', relative_to='AvgStddevDistrGraph')
        
        ManiaMonitor.NoteOffsetGraph.region_changed_event.connect(
            lambda event_data: ManiaMonitor.NoteDistrGraph._plot_data(self, self.data_cache, event_data)
        )

        ManiaMonitor.NoteOffsetProcGraph.region_changed_event.connect(
            lambda event_data: ManiaMonitor.NoteDistrGraph._plot_data(self, self.data_cache, event_data)
        )

        ManiaMonitor.NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: ManiaMonitor.AvgStddevDistrGraph._plot_data(self, event_data)
        )

        ManiaMonitor.NoteOffsetProcGraph.calc_done_event.connect(
            lambda event_data: ManiaMonitor.MapDisplay._plot_stddevs(self, event_data)
        )


    def __handle_new_replay_qt(self, args):
        data, title = args
        self.data_cache = data

        try: self.setWindowTitle(title)
        except AttributeError: pass

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