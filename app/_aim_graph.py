import numpy as np
import math

import pyqtgraph
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore


class AimGraph(QtGui.QWidget):

    SCALE = 3.0
    SIZE = 140*SCALE

    # Construct a unit radius circle for a graph
    class HitCircle(QtGui.QGraphicsObject):
        def __init__(self, center=(0.0, 0.0), radius=1.0, pen=pyqtgraph.mkPen(color=(255, 255, 255, 255), width=0.5)):
            QtGui.QGraphicsObject.__init__(self)
            self.center = center
            self.radius = radius
            self.pen = pen


        def boundingRect(self):
            rect = QtCore.QRectF(0, 0, 2*self.radius, 2*self.radius)
            rect.moveCenter(QtCore.QPointF(*self.center))
            return rect


        def paint(self, painter, option, widget):
            painter.setPen(self.pen)
            painter.drawEllipse(self.boundingRect())


    def __init__(self):
        QtGui.QWidget.__init__(self)

        DEV_GRAPH_HEIGHT = 64 + 4*AimGraph.SCALE
        TITLE_PADDING = 32

        self.setWindowTitle('Aim visualization')
        self.setSizePolicy(QtGui.QSizePolicy.Policy.Maximum, QtGui.QSizePolicy.Policy.Maximum)
        self.setMaximumSize(QtCore.QSize(AimGraph.SIZE + DEV_GRAPH_HEIGHT, AimGraph.SIZE + DEV_GRAPH_HEIGHT))

        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)
        
        self.win_hits = pyqtgraph.PlotWidget(show=False, title='Hit visualization')
        self.win_hits.setWindowTitle('osu! Aim Tool Hit Visualization')
        self.win_hits.setFixedSize(AimGraph.SIZE, AimGraph.SIZE)

        # Scatter plot for aim data
        self.plot_hits = self.win_hits.plot(title='Hit scatter')
        self.win_hits.enableAutoRange(axis='x', enable=False)
        self.win_hits.enableAutoRange(axis='y', enable=False)
        self.win_hits.hideAxis('left')
        self.win_hits.hideAxis('bottom')
        self.win_hits.setXRange(-AimGraph.SIZE/2, AimGraph.SIZE/2)
        self.win_hits.setYRange(-AimGraph.SIZE/2, AimGraph.SIZE/2)
        self.win_hits.getViewBox().setMouseEnabled(x=False, y=False)
        
        # Hit circle visualization
        self.circle_item = AimGraph.HitCircle((0, 0))
        self.win_hits.addItem(self.circle_item)

        # X-axis deviation histogram
        self.dev_x = pyqtgraph.PlotWidget(show=False)
        self.dev_x.getViewBox().setMouseEnabled(x=False, y=False)
        self.dev_x.enableAutoRange(axis='x', enable=False)
        self.dev_x.enableAutoRange(axis='y', enable=True)
        self.dev_x.hideAxis('left')
        self.dev_x.showAxis('bottom')
        self.dev_x.setFixedHeight(64 + 4*AimGraph.SCALE)
        self.dev_x.setXRange(-AimGraph.SIZE/2, AimGraph.SIZE/2)

        # Y-axis deviation histogram
        self.dev_y = pyqtgraph.PlotWidget(show=False)
        self.dev_y.getViewBox().setMouseEnabled(x=False, y=False)
        self.dev_y.enableAutoRange(axis='x', enable=True)
        self.dev_y.enableAutoRange(axis='y', enable=False)
        self.dev_y.hideAxis('bottom')
        self.dev_y.hideAxis('left')
        self.dev_y.showAxis('right')
        self.dev_y.setFixedWidth(64 + 4*AimGraph.SCALE)
        self.dev_y.setYRange(-AimGraph.SIZE/2, AimGraph.SIZE/2 + TITLE_PADDING)

        # Cov area metrics
        self.text_info = pyqtgraph.TextItem('', anchor=(0, 0), )
        self.text_info.setPos(-AimGraph.SIZE/2, AimGraph.SIZE/2)
        self.win_hits.addItem(self.text_info)

        self.main_layout.addWidget(self.win_hits, 0, 0)
        self.main_layout.addWidget(self.dev_x, 1, 0)
        self.main_layout.addWidget(self.dev_y, 0, 1)


    def show(self):
        self.main_widget.show()


    def hide(self):
        self.main_widget.hide()


    def set_cs(self, cs):
        # From https://github.com/ppy/osu/blob/master/osu.Game.Rulesets.Osu/Objects/OsuHitObject.cs#L137
        cs_px = (108.8 - 8.96*cs)/2
        
        self.circle_item.radius = cs_px*AimGraph.SCALE
        self.win_hits.update()


    def plot_data(self, aim_x_offsets, aim_y_offsets):
        scaled_aim_x_offsets = aim_x_offsets*AimGraph.SCALE
        scaled_aim_y_offsets = aim_y_offsets*AimGraph.SCALE

        # Plot aim data scatter plot
        self.plot_hits.setData(scaled_aim_x_offsets, scaled_aim_y_offsets, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(100, 100, 255, 200))

        # Plot a histogram for x-dev
        y, x = np.histogram(scaled_aim_x_offsets, bins=np.linspace(-AimGraph.SIZE/2, AimGraph.SIZE/2, int(AimGraph.SIZE/5)))
        self.dev_x.clearPlots()
        self.dev_x.plot(x, y, stepMode='center', fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))

        # Plot a histogram for y-dev
        y, x = np.histogram(scaled_aim_y_offsets, bins=np.linspace(-AimGraph.SIZE/2, AimGraph.SIZE/2, int(AimGraph.SIZE/5)))
        self.dev_y.clearPlots()
        plot = self.dev_y.plot(x, y, stepMode='center', fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))
        plot.rotate(90)

        self.text_info.setText(
            f'x-dev: {np.std(aim_x_offsets):.2f}\n'
            f'y-dev: {np.std(aim_y_offsets):.2f}\n'
            f'cs_px: {2*self.circle_item.radius/AimGraph.SCALE:.2f} o!px'
        )