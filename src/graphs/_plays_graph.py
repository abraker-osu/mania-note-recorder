import pyqtgraph
from pyqtgraph import dockarea

import numpy as np

from note_recorder import Data
from graph_mgr import GraphManager

from misc._callback import callback


class PlaysGraph():

    @callback
    class region_changed_event(): pass

    def __init__(self, graph_mgr: GraphManager, pos, relative_to=None):

        self.__id        = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(axisItems = { 'bottom': pyqtgraph.DateAxisItem(orientation = 'bottom') })
        self.__graph_mgr = graph_mgr

        self.__graph_mgr.create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = self.__widget,
            dock_name   = ''
        )

        # Dock size
        dock = self.__graph_mgr.graphs[self.__id]['dock']
        assert isinstance(dock, dockarea.Dock)

        dock.setMaximumHeight(64)

        # hit_offsets graph
        plot_item = self.__widget.getPlotItem()
        assert isinstance(plot_item, pyqtgraph.PlotItem)

        plot_item.getAxis('left').hide()
        plot_item.getAxis('bottom').enableAutoSIPrefix(False)

        view_box = plot_item.getViewBox()
        assert isinstance(view_box, pyqtgraph.ViewBox)

        view_box.setMouseEnabled(y=False)
        self.__widget.setLimits(yMin=-200, yMax=200)

        # Interactive region item
        self.__region_plot = pyqtgraph.LinearRegionItem([0, 1], 'vertical', swapMode='block', pen='r')
        self.__region_plot.sigRegionChangeFinished.connect(lambda: PlaysGraph.__region_changed(self))
        self.__widget.addItem(self.__region_plot)


    def plot_data(self, data):
        PlaysGraph.__plot_plays(self, data)


    def __plot_plays(self, data):
        hit_timestamps = np.unique(data[:, Data.TIMESTAMP])

        # Set plot data
        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            hit_timestamps, np.zeros(hit_timestamps.shape[0]),
            pen = None, symbol = 'o', symbolPen = None, symbolSize = 4, symbolBrush = 'y'
        )

        # Calculate view
        xMin = min(hit_timestamps) - 100
        xMax = max(hit_timestamps) + 86400  # + 1 day

        self.__widget.setLimits(xMin = xMin, xMax = xMax)

        # Update region item
        rBeg, _ = self.__region_plot.getRegion()

        self.__region_plot.setBounds((xMin, xMax))
        self.__region_plot.setRegion((max(xMin, rBeg), xMax))


    def __region_changed(self):
        PlaysGraph.region_changed_event.emit(self.__region_plot.getRegion())
