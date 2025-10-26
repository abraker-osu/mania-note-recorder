from numpy.core.fromnumeric import std
import pyqtgraph

import numpy as np

from graph_mgr import GraphManager

from misc._utils import Utils



class StddevDistrGraph():

    def __init__(self, graph_mgr: GraphManager, pos, relative_to=None):
        # `App.__init__` is not needed as it is passed as `self` by App

        self.__id: str   = __class__.__name__
        self.__widget    = pyqtgraph.PlotWidget(title='Stddev*2 Distribution')
        self.__graph_mgr = graph_mgr

        self.__graph_mgr.create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = self.__widget,
        )

        plot_item = self.__widget.getPlotItem()
        assert isinstance(plot_item, pyqtgraph.PlotItem)

        plot_item.getAxis('left').enableAutoSIPrefix(False)
        plot_item.getAxis('bottom').enableAutoSIPrefix(False)
        self.__widget.setLabel('left', 'Freq', units = '#', unitPrefix = '')
        self.__widget.setLabel('bottom', 'Stddev*2', units = 'ms', unitPrefix = '')
        #self.__widget.setLimits(xMin = -200, yMin = -1, xMax = 200)

        self.__min_err_line = pyqtgraph.InfiniteLine(angle = 90, pen = pyqtgraph.mkPen((255, 100, 0, 150), width = 1))
        self.__widget.addItem(self.__min_err_line)


    def plot_data(self, data):
        self.__plot_stddevs(data)


    def __plot_stddevs(self, data):
        means, stddevs = data
        stddevs = stddevs[stddevs != 0]  # These are invalid

        if len(stddevs) == 0:
            return

        # Get a histogram for stddevs
        step = (150 - 0) / (0.1*stddevs.shape[0])
        y, x = np.histogram(stddevs, bins = np.linspace(0, 150, num=int(0.15*stddevs.shape[0])))

        # Set plot data
        plot_item = self.__graph_mgr.graphs[self.__id]['plot']
        assert isinstance(plot_item, pyqtgraph.PlotDataItem)

        plot_item.setData(
            x, y,
            stepMode = 'center', fillLevel = 0, fillOutline = True, brush = (0,0,255,150)
        )

        self.__min_err_line.setValue(x[:-1][y == np.max(y)][0] + step/2)
        print(f'Std peak: {x[:-1][y == np.max(y)][0] + step/2} ms')
