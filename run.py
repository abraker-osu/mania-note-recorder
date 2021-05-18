import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from mania_monitor_app import ManiaMonitor



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex  = ManiaMonitor('C:/Games/osu!')
    sys.exit(app.exec_())