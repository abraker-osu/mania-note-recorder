from numpy.core.fromnumeric import std
import pyqtgraph

from PyQt5.QtGui import *
import numpy as np

from ._utils import Utils



class AvgDistrGraph():

    def __init__(self, pos, relative_to=None):

        self.__id = __class__.__name__
        self._create_graph(
            graph_id    = self.__id,
            pos         = pos,
            relative_to = relative_to,
            widget      = pyqtgraph.PlotWidget(title='Means Distribution'),
        )

        self.graphs[self.__id]['widget'].getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.graphs[self.__id]['widget'].setLabel('left', 'Freq', units='#', unitPrefix='')
        self.graphs[self.__id]['widget'].setLabel('bottom', 'Mean', units='ms', unitPrefix='')
        self.graphs[self.__id]['widget'].setLimits(xMin=-200, yMin=-1, xMax=200)

        self.__min_err_line = pyqtgraph.InfiniteLine(angle=90, pen=pyqtgraph.mkPen((255, 100, 0, 150), width=1))
        self.graphs[self.__id]['widget'].addItem(self.__min_err_line)


    def _plot_data(self, data):
        AvgDistrGraph.__plot_stddevs(self, data)


    def __plot_stddevs(self, data):
        means, stddevs = data
        means = means[means != 0]  # These are invalid

        if len(means) == 0:
            return
        
        # Get a histogram for stddevs
        step = (150 - 0)/(0.1*means.shape[0])
        y, x = np.histogram(means, bins=np.linspace(-150, 150, int(0.1*means.shape[0])))
        self.graphs[self.__id]['plot'].setData(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0,0,255,150))

        self.__min_err_line.setValue(x[:-1][y == np.max(y)][0] + step/2)
        print(f'Avg distr peak: {x[:-1][y == np.max(y)][0] + step/2} ms')