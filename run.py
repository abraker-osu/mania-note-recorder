import sys

from PyQt5 import QtWidgets

from mania_monitor_app import ManiaMonitor



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open('stylesheet.css').read())

    ex  = ManiaMonitor()
    sys.exit(app.exec_())
