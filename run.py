import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from mania_hitoffset_monitor import ManiaHitOffsetsMonitor



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex  = ManiaHitOffsetsMonitor('C:/Games/osu!')
    sys.exit(app.exec_())