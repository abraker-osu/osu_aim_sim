import pyqtgraph
from pyqtgraph.Qt import QtGui



class DataGraph(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        # Deviation vs Distance graph
        self.__graph = pyqtgraph.PlotWidget(title='Aim dev-x (vel)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=0, xMax=5000, yMin=-10, yMax=200)
        self.__graph.setRange(xRange=[-10, 600], yRange=[-10, 20])
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'velocity', units='osu!px/s', unitPrefix='')
        self.__graph.addLegend()

        self.__layout = QtGui.QHBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)


    def plot_data(self, data, clear=False, color='y'):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        if clear:
            self.__graph.clearPlots()

        vels = data[:, 1]*data[:, 2]/60

        self.__graph.plot(x=vels, y=data[:, 0], pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=color)
