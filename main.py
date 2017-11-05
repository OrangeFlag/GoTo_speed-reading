#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication

from GUI import GUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUI()
    gui.MainWindow.show()
    
    sys.exit(app.exec_())