import numpy as np
import time

from app.misc._data_cor import DataCor
from app.misc._osu_utils import OsuUtils


class PlayerSimulator():

    def __init__(self, data):
        # Hitcircle diameter (osu!px)
        self.cs_px = OsuUtils.cs_to_px(data['cs'])

        # Player tap deviation (ms @ 95% confidence interval)
        self.hit_dev = data['hit_dev']

        # Player's average read time (ms)
        self.avg_read_time = data['avg_read_time']

        # Player's deviation of read time (ms)
        self.dev_read_time = data['dev_read_time']

        # Player's deviation of applied velocity (osu!px/ms @ 95% confidence interval)
        self.player_vel_dev = data['player_vel_dev']


    def run_simulation(self, map_data, mode=0):
        # Tick time of simulation in ms
        simulation_step = 10

        # Timings when player hits key to tap the note
        hit_timings = np.random.normal(0, self.hit_dev, len(map_data))

        # Time period it takes for player to processes visual information at this moment
        read_period = int(np.random.normal(self.avg_read_time, self.dev_read_time, None))

        # Time when the player last processed visual information
        last_read_time = 0

        # Index of the note being read
        note_read_idx = 0

        # Index of the note being acted upon
        note_act_idx = 0

        # Current note position
        cursor_pos = map_data[0, DataCor.IDX_X]

        # Current velocity of the cursor
        cursor_vel = 0

        # Timing of the last note in the map
        last_note_timing = int(1000*map_data[-1, DataCor.IDX_T])
        
        if mode == 0:
            replay_data = np.zeros((len(map_data), 3))
        else:
            replay_data = np.zeros((last_note_timing + 1, 3))

        #time_start = time.time()

        # For each simulations step
        for t in range(0, last_note_timing + 1, simulation_step):
            # If enough time has passed since the player last processed visual information
            if t - last_read_time >= read_period:
                # Generate next time period it would take to process visual information
                read_period = int(np.random.normal(self.avg_read_time, self.dev_read_time, None))
                last_read_time = t

                # Loop until reached a note that can be read in adequate time
                while True:
                    read_note_pos = map_data[note_read_idx, DataCor.IDX_X]
                    read_time_to_note = 1000*map_data[note_read_idx, DataCor.IDX_T] - t

                    # If the note can be read within adequate time, break out of the loop
                    if read_time_to_note >= read_period:
                        break

                    # Make sure it's not the last note
                    if note_read_idx >= len(map_data) - 1:
                        break

                    # Still focused on note acting on, no need to do anything else
                    if note_read_idx >= note_act_idx:
                        break

                    # Read the next note
                    note_read_idx += 1

                # Judge whether current velocity is sufficient to hit the note
                read_future_pos = cursor_pos + (cursor_vel * read_time_to_note)
                read_is_undershoot = (read_future_pos < (read_note_pos - self.cs_px/2))
                read_is_overshoot  = (read_future_pos > (read_note_pos + self.cs_px/2))

                #print(t, time_to_note, read_period, int(cursor_pos), read_future_pos, read_note_pos)
                #input()

                if read_is_undershoot or read_is_overshoot:
                    # Calculate target velocity
                    target_vel = (read_note_pos - cursor_pos) / read_time_to_note

                    # Update velocity
                    cursor_vel = target_vel #np.random.normal(target_vel, abs(target_vel)*0.05*self.player_vel_dev, None)

            '''
            pos_to_note = map_data[note_act_idx, DataCor.IDX_X] - cursor_pos
            time_to_note = 1000*map_data[note_act_idx, DataCor.IDX_T] - t

            if time_to_note == 0:
                cursor_vel = 0
            else:
                cursor_vel = pos_to_note / (1000*map_data[note_act_idx, DataCor.IDX_T] - t)
            '''

            # Update cursor position
            cursor_pos += cursor_vel*simulation_step

            is_within_timing = \
                (t >= 1000*map_data[note_act_idx, DataCor.IDX_T] - simulation_step/2) and \
                (t <  1000*map_data[note_act_idx, DataCor.IDX_T] + simulation_step/2)

            is_late_timing = (t >= 1000*map_data[note_act_idx, DataCor.IDX_T] + 2*self.hit_dev)

            if is_within_timing:
                note_timing = int(1000*map_data[note_act_idx, DataCor.IDX_T])

                #print(t, note_timing, int(cursor_pos), map_data[note_act_idx, DataCor.IDX_X], int(cursor_pos + cursor_vel*(note_timing - t)), cursor_vel*(note_timing - t))
                #input()

                # Simulate hit and record position
                replay_data[note_act_idx, DataCor.IDX_T] = t/1000
                replay_data[note_act_idx, DataCor.IDX_X] = int(cursor_pos + cursor_vel*(note_timing - t)) #int(cursor_pos + cursor_vel*hit_timings[note_act_idx])
                replay_data[note_act_idx, DataCor.IDX_Y] = map_data[note_act_idx, DataCor.IDX_Y]

                # If within the note, update note
                if note_act_idx < len(map_data) - 1:
                    note_act_idx += 1

            elif is_late_timing:
                if mode == 0:
                    # Simulate hit and record position
                    replay_data[note_act_idx, DataCor.IDX_T] = np.nan
                    replay_data[note_act_idx, DataCor.IDX_X] = np.nan
                    replay_data[note_act_idx, DataCor.IDX_Y] = np.nan

                # If within the note, update note
                if note_act_idx < len(map_data) - 1:
                    note_act_idx += 1

            if mode != 0:
                replay_data[t, DataCor.IDX_T] = t/1000
                replay_data[t, DataCor.IDX_X] = int(cursor_pos)
                replay_data[t, DataCor.IDX_Y] = map_data[note_act_idx, DataCor.IDX_Y]
            
        #print(f'elapsed: {time.time() - time_start}')

        return replay_data