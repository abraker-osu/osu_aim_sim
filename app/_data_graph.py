import numpy as np
import math

import pyqtgraph
from pyqtgraph.Qt import QtGui

from app.misc._utils import Utils


class DataGraph(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        # Deviation vs Distance graph
        self.__graph = pyqtgraph.PlotWidget(title='Aim dev-x (vel)')
        self.__graph.getPlotItem().getAxis('left').enableAutoSIPrefix(False)
        self.__graph.getPlotItem().getAxis('bottom').enableAutoSIPrefix(False)
        self.__graph.enableAutoRange(axis='x', enable=False)
        self.__graph.enableAutoRange(axis='y', enable=False)
        self.__graph.setLimits(xMin=0, xMax=5000, yMin=-10, yMax=1000)
        self.__graph.setRange(xRange=[-10, 600], yRange=[-10, 20])
        self.__graph.setLabel('left', 'deviation', units='σ', unitPrefix='')
        self.__graph.setLabel('bottom', 'velocity', units='osu!px/s', unitPrefix='')
        self.__graph.addLegend()

        # Used to set text in legend item
        self.__label_style = pyqtgraph.PlotDataItem(pen=(0,0,0))
        self.__graph.getPlotItem().legend.addItem(self.__label_style, '')
        self.__text = self.__graph.getPlotItem().legend.getLabel(self.__label_style)

        self.__layout = QtGui.QHBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(2)
        self.__layout.addWidget(self.__graph)


    def plot_data(self, data, angle, clear=False, model=False, color='y'):
        if data.shape[0] == 0:
            return

        # Clear plots for redraw
        if clear:
            self.__graph.clearPlots()

        vels = data[:, 1]*data[:, 2]/60
        devs = data[:, 0]

        self.__graph.plot(x=vels, y=devs, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=color)

        # Calc linear regression
        m, b = Utils.linear_regresion(vels, devs)
        if type(m) == type(None) or type(b) == type(None):
            return

        y_model = m*vels + b                # model: y = mx + b
        x_model = (devs - b)/m              # model: x = (y - b)/m

        m_dev_y = np.std(devs - y_model)    # deviation of y from model
        m_dev_x = np.std(vels - x_model)    # deviation of x from model

        # Standard error of slope @ 95% confidence interval
        m_se_95 = (m_dev_y/m_dev_x)/math.sqrt(devs.shape[0] - 2)*1.96

        label = f'∠={angle:.2f}  n={devs.shape[0]}  σ={m_dev_y:.2f}  m={m:.5f}±{m_se_95:.5f}  b={b:.2f}'
        self.__graph.plot(x=[0, max(vels)], y=[b, m*max(vels) + b], pen=(100, 100, 0, 150), name=label)  

