import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from app import App



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex  = App()
    sys.exit(app.exec_())