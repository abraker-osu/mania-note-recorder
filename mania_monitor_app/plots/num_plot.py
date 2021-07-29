import pyqtgraph
from pyqtgraph.Qt import QtCore, QtGui


class NumPlotItem(pyqtgraph.GraphicsObject):

    def __init__(self):
        pyqtgraph.GraphicsObject.__init__(self)
    
        self._x = None
        self._y = None
        self._num = None

        self._picture = QtGui.QPicture()

        self._px_h = self.pixelHeight()
        self._px_w = self.pixelWidth()

        #self.f = QFont()
        #self.f.setPointSize(48)



    def setData(self, x, y, num):
        self._x = x
        self._y = y
        self._num = num

        self._cached_bounding = None

        self._px_h = self.pixelHeight()
        self._px_w = self.pixelWidth()

        self.generatePicture()


    def generatePicture(self):
        if type(self._x) == type(None) or \
           type(self._y) == type(None) or \
           type(self._num) == type(None):
            return

        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self._picture = QtGui.QPicture()

        painter = QtGui.QPainter(self._picture)
        #painter.setPen(pyqtgraph.mkPen(color=(255, 0, 0, 50), width=1))

        font = painter.font()
        font.setPixelSize(48)
        painter.setFont(font)

        for x, y, num in zip(self._x, self._y, self._num):
            painter.drawText(x, y, str(num))

        painter.end()
    

    def paint(self, painter, *args):
        painter.drawPicture(0, 0, self._picture)
    

    def boundingRect(self):
        if type(self._x) == type(None) or type(self._y) == type(None):
            return QtCore.QRectF()

        if len(self._x) == 0 or len(self._y) == 0:
            return QtCore.QRectF()

        if type(self._cached_bounding) == type(None):
            # boundingRect _must_ indicate the entire area that will be drawn on
            # or else we will get artifacts and possibly crashing.
            # (in this case, QPicture does all the work of computing the bouning rect for us)
            self._cached_bounding = QtCore.QRectF(min(self._x), max(self._x) - min(self._x), min(self._y), max(self._x) - min(self._x))

        return self._cached_bounding


    def viewRangeChanged(self):
        """
        Called whenever the view coordinates of the ViewBox containing this item have changed.
        """
        px_h = self.pixelHeight()
        px_w = self.pixelWidth()

        # Without pixel_height the render scales with how the view is zoomed in/out
        if self._px_h != px_h or self._px_w != px_w:
            self._px_h = px_h
            self._px_w = px_w

            self.generatePicture()