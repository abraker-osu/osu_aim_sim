import pyqtgraph
from pyqtgraph.Qt import QtGui

from app.misc._osu_utils import OsuUtils
from app.misc._data_cor import DataCor


class PatternVisual(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.map_data_x = None
        self.map_data_y = None
        self.map_data_t = None

        self.replay_data_x = None
        self.replay_data_y = None
        self.replay_data_t = None
        self.replay_data_k = None

        self.cs    = None
        self.ar    = None
        self.t     = None

        self.setWindowTitle('osu! Aim Tool Pattern Visualization')

        self.layout = QtGui.QVBoxLayout(self)
        self.visual = pyqtgraph.PlotWidget(title='Pattern visualization')
        self.timeline = pyqtgraph.PlotWidget()
        self.layout.addWidget(self.visual)
        self.layout.addWidget(self.timeline)

        self.plot_hits = self.visual.plot(title='Hit scatter', pen=None, symbol='o', symbolPen=None, symbolSize=100, symbolBrush=(100, 100, 255, 200), pxMode=False)
        self.visual.showGrid(True, True)
        self.visual.setXRange(0, 540)
        self.visual.setYRange(0, 410)
        #self.visual.getViewBox().setMouseEnabled(x=False, y=False)
        self.visual.enableAutoRange(axis='x', enable=False)
        self.visual.enableAutoRange(axis='y', enable=False)

        self.plot_approach = self.visual.plot(pen=None, symbol='o', symbolPen=(100, 100, 255, 200), symbolBrush=None, symbolSize=100, pxMode=False)
        #self.plot_cursor   = self.visual.plot(pen='y', pxMode=False)
        self.plot_cursor   = self.visual.plot(pen=None, symbol='o', symbolPen='y', symbolBrush=None, symbolSize=5, pxMode=False)
        
        self.timeline.setFixedHeight(64)
        self.timeline.hideAxis('left')
        self.timeline.setXRange(-1, 4)

        # Interactive region item
        self.timeline_marker = pyqtgraph.InfiniteLine(angle=90, movable=True)
        self.timeline_marker.setBounds((-10000, None))
        self.timeline_marker.sigPositionChanged.connect(self.__time_changed_event)

        self.timeline.addItem(self.timeline_marker, ignoreBounds=True)
        self.__time_changed_event()


    def show(self):
        self.main_widget.show()


    def hide(self):
        self.main_widget.hide()


    def set_map(self,  map_data):
        self.map_data_x = map_data[:, DataCor.IDX_X]
        self.map_data_y = map_data[:, DataCor.IDX_Y]
        self.map_data_t = map_data[:, DataCor.IDX_T]

        self.__draw_map_data()
        self.visual.update()

    
    def set_replay(self, replay_data):
        self.replay_data_x = replay_data[:, DataCor.IDX_X]
        self.replay_data_y = replay_data[:, DataCor.IDX_Y]
        self.replay_data_t = replay_data[:, DataCor.IDX_T]
        self.replay_data_k = replay_data[:, DataCor.IDX_K]

        self.__draw_replay_data()
        self.visual.update()


    def set_ar(self, ar):
        self.ar = ar
        self.__draw_map_data()
        self.visual.update()


    def set_cs(self, cs):
        self.cs = cs
        self.__draw_map_data()
        self.visual.update()
                

    def __draw_map_data(self):
        if type(self.map_data_x) == type(None): return
        if type(self.map_data_y) == type(None): return
        if type(self.map_data_t) == type(None): return

        if len(self.map_data_x) != len(self.map_data_y) != len(self.map_data_t):
            raise AssertionError('len(self.map_data_x) != len(self.map_data_y) != len(self.map_data_t)')

        if type(self.ar) == type(None): return
        if type(self.cs) == type(None): return

        cs_px = OsuUtils.cs_to_px(self.cs)
        ar_ms = OsuUtils.ar_to_ms(self.ar)/1000
        ar_select = (self.t <= self.map_data_t) & (self.map_data_t <= (self.t + ar_ms))

        self.plot_hits.setData(self.map_data_x[ar_select], self.map_data_y[ar_select], symbolSize=cs_px)

        sizes = OsuUtils.approach_circle_to_radius(cs_px, ar_ms, self.map_data_t[ar_select] - self.t)
        self.plot_approach.setData(self.map_data_x[ar_select], self.map_data_y[ar_select], symbolSize=sizes)


    def __draw_replay_data(self):
        if type(self.replay_data_x) == type(None): return
        if type(self.replay_data_y) == type(None): return
        if type(self.replay_data_t) == type(None): return

        if len(self.replay_data_x) != len(self.replay_data_y) != len(self.replay_data_t):
            raise AssertionError('len(self.replay_data_x) != len(self.replay_data_y) != len(self.replay_data_t)')

        select_time = (self.replay_data_t >= self.t - 0.2) & (self.replay_data_t <= self.t)
        
        color_map = {
           0 :  (255, 255, 0, 100),  # Yellow
           1 :  (  0, 255, 0, 200),  # Green
           2 :  (255,   0, 0, 200),  # Red
        }

        colors = [
            color_map[key] for key in self.replay_data_k[select_time]
        ]

        self.plot_cursor.setData(self.replay_data_x[select_time], self.replay_data_y[select_time], symbolPen=colors)


    def __time_changed_event(self):
        self.t = self.timeline_marker.getPos()[0]

        self.__draw_map_data()
        self.__draw_replay_data()