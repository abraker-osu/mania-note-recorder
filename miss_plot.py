import pyqtgraph
from pyqtgraph import QtCore, QtGui


class MissPlotItem(pyqtgraph.GraphicsObject):

    def __init__(self, data):
        pyqtgraph.GraphicsObject.__init__(self)
        self.setData(data)
    

    def setData(self, data):
        self.data = data
        
        self.px_h = self.pixelHeight()
        self.px_w = self.pixelWidth()

        self.generatePicture()


    def generatePicture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()

        painter = QtGui.QPainter(self.picture)
        painter.setPen(pyqtgraph.mkPen(color=(255, 0, 0, 50), width=1))

        vr = self.viewRect()
        for timing in self.data:
            painter.drawLine(QtCore.QPointF(float(timing), vr.bottom()), QtCore.QPointF(float(timing), vr.top()))

        painter.end()
    

    def paint(self, painter, *args):
        painter.drawPicture(0, 0, self.picture)
    

    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        return QtCore.QRectF()


    def viewRangeChanged(self):
        """
        Called whenever the view coordinates of the ViewBox containing this item have changed.
        """
        px_h = self.pixelHeight()
        px_w = self.pixelWidth()

        # Without pixel_height the render scales with how the view is zoomed in/out
        if self.px_h != px_h or self.px_w != px_w:
            self.px_h = px_h
            self.px_w = px_w

            self.generatePicture()