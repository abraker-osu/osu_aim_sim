import math
import time
import numpy as np

import pyqtgraph
from pyqtgraph.Qt import QtGui

np.set_printoptions(suppress=True)



class App(QtGui.QMainWindow):

    from ._pattern_visual import PatternVisual
    from ._player_simulator import PlayerSimulator
    from ._aim_graph import AimGraph
    from ._data_graph import DataGraph
    from .misc._osu_utils import OsuUtils
    from .misc._data_cor import DataCor

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.__init_gui()
        self.__run()


    def __init_gui(self):
        self.main_widget = QtGui.QTabWidget()
        self.map_visual_0deg = App.PatternVisual()
        self.map_visual_180deg = App.PatternVisual()
        self.aim_graph_0deg = App.AimGraph()
        self.aim_graph_180deg = App.AimGraph()
        self.graph = App.DataGraph()
        
        self.main_widget.addTab(self.map_visual_0deg, '0 deg')
        self.main_widget.addTab(self.map_visual_180deg, '180 deg')
        self.main_widget.addTab(self.aim_graph_0deg, 'Aim graph 0 deg')
        self.main_widget.addTab(self.aim_graph_180deg, 'Aim graph 180 deg')
        self.main_widget.addTab(self.graph, 'Graph')

        self.setCentralWidget(self.main_widget)


    def __run(self):
        self.show()
        
        #self.__run_one_simulation(mode=App.PlayerSimulator.RECORD_HITS)
        #self.__run_one_simulation(mode=App.PlayerSimulator.RECORD_REPLAY)
        self.__run_full_simulation()


    def __run_one_simulation(self, mode=PlayerSimulator.RECORD_HITS):
        # Map wide data
        bpm = 500
        cs  = 6
        ar  = 8

        # Player wide data
        hit_dev       = 15    # Hit deviation (in ms @ 95% confidence interval))
        avg_read_time = 1     # Human update interval mean (in ms)
        dev_read_time = 0     # Human update interval deviation (in ms)
        vel_dev       = 0     # Velocity deviation (in osu!px / ms)
        
        # Simulate player
        self.player_simulator = App.PlayerSimulator({
            'cs'             : cs,
            'hit_dev'        : hit_dev,
            'avg_read_time'  : avg_read_time,
            'dev_read_time'  : dev_read_time,
            'player_vel_dev' : vel_dev,
        })

        self.map_visual_180deg.set_ar(ar)
        self.map_visual_180deg.set_cs(cs)

        self.map_visual_0deg.set_ar(ar)
        self.map_visual_0deg.set_cs(cs)

        # Generate stream pattern
        map_data_0 = App.OsuUtils.generate_pattern(
            initial_angle = 0,
            distance      = 100,
            time          = 60/bpm, 
            angle         = 0 * math.pi/180, 
            n_points      = 1000 if (mode == App.PlayerSimulator.RECORD_HITS) else 200,
            n_repeats     = 1
        )

        # Generate back and forth jump pattern
        map_data_180 = App.OsuUtils.generate_pattern(
            initial_angle = 0,
            distance      = 100,
            time          = 60/bpm,
            angle         = 180 * math.pi/180,
            n_points      = 1000 if not (mode == App.PlayerSimulator.RECORD_HITS) else 200,
            n_repeats     = 1
        )

        self.map_visual_0deg.set_map(map_data_0)
        self.map_visual_180deg.set_map(map_data_180)

        replay_data_0deg = self.player_simulator.run_simulation(map_data_0, mode=mode)
        replay_data_180deg = self.player_simulator.run_simulation(map_data_180, mode=mode)

        hit_select_0deg = (replay_data_0deg[:, App.DataCor.IDX_K] > App.PlayerSimulator.KEY_NONE)
        aim_x_offsets, aim_y_offsets = self.__process_data(map_data_0, replay_data_0deg[hit_select_0deg])
        self.aim_graph_0deg.set_cs(cs)
        self.aim_graph_0deg.plot_data(aim_x_offsets, aim_y_offsets)

        hit_select_180deg = (replay_data_180deg[:, App.DataCor.IDX_K] > App.PlayerSimulator.KEY_NONE)
        aim_x_offsets, aim_y_offsets = self.__process_data(map_data_180, replay_data_180deg[hit_select_180deg])
        self.aim_graph_180deg.set_cs(cs)
        self.aim_graph_180deg.plot_data(aim_x_offsets, aim_y_offsets)

        self.map_visual_0deg.set_replay(replay_data_0deg)
        self.map_visual_180deg.set_replay(replay_data_180deg)


    def __run_full_simulation(self):
        # Map wide data
        cs  = 6
        ar  = 8

        # Player wide data
        '''
        hit_dev       = 18   # Hit deviation (in ms @ 95% confidence interval))
        avg_read_time = 140   # Human update interval mean (in ms)
        dev_read_time = 10    # Human update interval deviation (in ms)
        vel_dev       = 10    # Velocity deviation (in osu!px / ms)
        '''

        hit_dev       = 15    # Hit deviation (in ms @ 95% confidence interval))
        avg_read_time = 1     # Human update interval mean (in ms)
        dev_read_time = 0     # Human update interval deviation (in ms)
        vel_dev       = 0     # Velocity deviation (in osu!px / ms)
        
        # Simulate player
        self.player_simulator = App.PlayerSimulator({
            'cs'             : cs,
            'hit_dev'        : hit_dev,
            'avg_read_time'  : avg_read_time,
            'dev_read_time'  : dev_read_time,
            'player_vel_dev' : vel_dev,
        })

        
        self.map_visual_180deg.set_ar(ar)
        self.map_visual_180deg.set_cs(cs)

        self.map_visual_0deg.set_ar(ar)
        self.map_visual_0deg.set_cs(cs)

        note_bpms = list(range(120, 200, 5))
        note_dists = list(range(50, 110, 5))

        dev_0deg = np.zeros((len(note_bpms) * len(note_dists), 3))
        dev_180deg = np.zeros((len(note_bpms) * len(note_dists), 3))

        i = -1

        for note_bpm in note_bpms:
            for note_dist in note_dists:
                i += 1

                dev_0deg[i, 1] = note_dist
                dev_180deg[i, 1] = note_dist

                dev_0deg[i, 2] = note_bpm
                dev_180deg[i, 2] = note_bpm

                # Generate stream pattern
                map_data_0 = App.OsuUtils.generate_pattern(
                    initial_angle = 0,
                    distance      = note_dist,
                    time          = 60/note_bpm, 
                    angle         = 0 * math.pi/180, 
                    n_points      = 30,
                    n_repeats     = 1
                )

                # Generate back and forth jump pattern
                map_data_180 = App.OsuUtils.generate_pattern(
                    initial_angle = 0,
                    distance      = note_dist,
                    time          = 60/note_bpm,
                    angle         = 180 * math.pi/180,
                    n_points      = 60,
                    n_repeats     = 1
                )

                replay_data_0deg = self.player_simulator.run_simulation(map_data_0)
                aim_x_offsets, aim_y_offsets = self.__process_data(map_data_0, replay_data_0deg)
                dev_x = np.std(aim_x_offsets)

                QtWidgets.QApplication.processEvents()

                dev_0deg[i, 0] = dev_x

                replay_data_180deg = self.player_simulator.run_simulation(map_data_180)
                aim_x_offsets, aim_y_offsets = self.__process_data(map_data_180, replay_data_180deg)
                dev_x = np.std(aim_x_offsets)
                
                dev_180deg[i, 0] = dev_x

                self.graph.plot_data(dev_0deg[:i], True, 'y')
                self.graph.plot_data(dev_180deg[:i], False, 'g')

                QtWidgets.QApplication.processEvents()

        self.map_visual_0deg.set_map(map_data_0)
        self.map_visual_180deg.set_map(map_data_180)

        self.map_visual_0deg.set_replay(replay_data_0deg)
        self.map_visual_180deg.set_replay(replay_data_180deg)

        #print(f'0 deg,   dev = {dev_0deg[:, 0]}')
        #print(f'180 deg, dev = {dev_180deg[:, 0]}')

        
    def __process_data(self, map_data, replay_data):
        # Process data
        tap_offsets   = map_data[:, App.DataCor.IDX_T] - replay_data[:, App.DataCor.IDX_T]
        aim_x_offsets = map_data[:, App.DataCor.IDX_X] - replay_data[:, App.DataCor.IDX_X]
        aim_y_offsets = map_data[:, App.DataCor.IDX_Y] - replay_data[:, App.DataCor.IDX_Y]
        
        # Correct for incoming direction
        x_map_vecs = map_data[1:, App.DataCor.IDX_X] - map_data[:-1, App.DataCor.IDX_X]
        y_map_vecs = map_data[1:, App.DataCor.IDX_Y] - map_data[:-1, App.DataCor.IDX_Y]

        map_thetas = np.arctan2(y_map_vecs, x_map_vecs)
        hit_thetas = np.arctan2(aim_y_offsets, aim_x_offsets)
        mags = (aim_x_offsets**2 + aim_y_offsets**2)**0.5

        aim_x_offsets = mags[1:]*np.cos(map_thetas - hit_thetas[1:])
        aim_y_offsets = mags[1:]*np.sin(map_thetas - hit_thetas[1:])

        # Filter out nans that happen due to misc reasons (usually due to empty slices or div by zero)
        nan_filter = ~np.isnan(aim_x_offsets) & ~np.isnan(aim_y_offsets)

        aim_x_offsets = aim_x_offsets[nan_filter]
        aim_y_offsets = aim_y_offsets[nan_filter]
        #tap_offsets   = tap_offsets[nan_filter]

        return aim_x_offsets, aim_y_offsets