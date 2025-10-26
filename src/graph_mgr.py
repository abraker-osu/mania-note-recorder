
from types import MappingProxyType

import pyqtgraph
from pyqtgraph import dockarea



class GraphManager:
    """A simple singleton manager for graph objects."""

    def __init__(self, area: dockarea.DockArea):
        self.__graphs: dict[str, dict[str, pyqtgraph.PlotWidget | pyqtgraph.PlotDataItem | dockarea.DockArea]] = {}
        self.__area = area


    @property
    def graphs(self):
        return MappingProxyType(self.__graphs)


    def create_graph(self,
        graph_id:    str,
        dock_name:   str = ' ',
        pos:         str = 'bottom',
        relative_to: pyqtgraph.PlotWidget | None = None,
        widget:      pyqtgraph.PlotWidget | None = None,
        plot:        pyqtgraph.PlotItem   | None = None
    ):
        if isinstance(widget, type(None)):
            widget = pyqtgraph.PlotWidget()

        try: widget.getViewBox().enableAutoRange()
        except AttributeError:
            pass

        dock = dockarea.Dock(dock_name, size=(500,400))
        dock.addWidget(widget)

        try: relative_dock = self.__graphs[relative_to]['dock']
        except KeyError:
            relative_dock = None

        self.__area.addDock(dock, pos, relativeTo = relative_dock)

        self.__graphs[graph_id] = {
            'widget' : widget,
            'dock'   : dock,
            'plot'   : widget.plot() if plot == None else plot
        }

        if plot != None:
            widget.addItem(plot)
