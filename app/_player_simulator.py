import numpy as np
import math
import time

from app.misc._data_cor import DataCor
from app.misc._osu_utils import OsuUtils


class PlayerSimulator():

    RECORD_HITS   = 0
    RECORD_REPLAY = 1

    KEY_NONE = 0
    KEY_HIT  = 1
    KEY_MISS = 2

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

        print(self.hit_dev, self.avg_read_time, self.dev_read_time, self.player_vel_dev)


    # If mode is 0, record just hits scoring, if it's 1 record as if replay
    def run_simulation(self, map_data, mode=RECORD_HITS):
        ###
        ### Parameters related to replay recording
        ###

        # Tick time of simulation in ms
        simulation_step = 3     

        # Timing of the last note in the map
        first_note_timing = int(1000*map_data[0, DataCor.IDX_T])
        last_note_timing = int(1000*map_data[-1, DataCor.IDX_T])

        # List of timings to be processed
        sim_timing_steps = range(
            first_note_timing - 6*self.hit_dev - simulation_step, 
            last_note_timing  + 6*self.hit_dev + simulation_step, 
            simulation_step
        )
        
        if mode == PlayerSimulator.RECORD_HITS:
            replay_data = np.zeros((len(map_data), 4))
        else:
            replay_data = np.zeros((len(sim_timing_steps), 4))

        # Keep track of replay frame being recorded
        replay_idx = 0
        
        ###
        ### Parameters related to note being read
        ###

        # Time period it takes for player to processes visual information at this moment
        read_period = int(np.random.normal(self.avg_read_time, self.dev_read_time, None))

        # Time when the player last processed visual information
        last_read_time = 0

        # Index of the note being read
        note_read_idx = 0
        
        ###
        ### Parameters related to note being aimed
        ###

        # Current note position
        cursor_pos = map_data[0, DataCor.IDX_X]

        # Current velocity of the cursor
        cursor_vel = 0

        # Index of the note being aimed
        note_aim_idx = 0

        ###
        ### Parameters related to note being tapped
        ###

        # Timings when player hits key to tap the note
        hit_timings = (np.random.normal(0, self.hit_dev, len(map_data)) + 1000*map_data[:, DataCor.IDX_T]).astype(np.int)
        hit_timings = np.sort(hit_timings)

        # Index of the note being tapped
        note_tap_idx = 0

        def get_act_params(note_act_idx):
            # Time of active note
            note_timing = 1000*map_data[note_act_idx, DataCor.IDX_T]

            # Time of active hit timing
            hit_timing = int(hit_timings[note_act_idx])

            # Flag indicating whether the generated hit timing is >100 ms late
            is_late_timing = note_timing < (hit_timing - 100)

            return hit_timing, is_late_timing

        hit_timing, is_late_timing = get_act_params(note_tap_idx)

        #time_start = time.time()

        # For each simulations step
        for t in sim_timing_steps:
            # If enough time has passed since the player last processed visual information
            if t - last_read_time >= read_period:
                # Generate next time period it would take to process visual information
                if self.dev_read_time == 0:
                    read_period = self.avg_read_time
                else:
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

                    # Check if still focused on note acting on, no need to do anything else if so
                    if note_read_idx >= note_aim_idx:
                        break

                    # Read the next note
                    note_read_idx += 1

                # Judge whether current velocity is sufficient to hit the note
                # Reading precision of note's center is depenent on how fast the pattern is
                read_future_pos = cursor_pos + (cursor_vel * read_time_to_note)
                read_is_undershoot = (read_future_pos < (read_note_pos - self.cs_px/4 * 4*cursor_vel))
                read_is_overshoot  = (read_future_pos > (read_note_pos + self.cs_px/4 * 4*cursor_vel))

                #print(t, time_to_note, read_period, int(cursor_pos), read_future_pos, read_note_pos)
                #input()
                
                if read_is_undershoot or read_is_overshoot:
                    # If the player perceived the trajectory to miss aim, simulate a
                    # trajectory correction by the player
                    if read_time_to_note == 0:
                        # Avoid division by zero
                        target_vel = 0
                    else:
                        # Calculate target velocity
                        target_vel = (read_note_pos - cursor_pos) / read_time_to_note
                else:
                    # Player perceives current velocity as sufficient to hit the note
                    target_vel = cursor_vel

                '''
                \FIXME: The `vel_dev` is needed to kinda simulate the player's misjudgment of
                        how much force is needed to be applied to cursor/stylus when moving the 
                        cursor to the note. However, this causes back and forth jump cursor behavior
                        to be a lot more erradic then in reality, often overaiming in unrealistic amounts.
                '''
                # Update velocity; The player iteratively corrects their velocity when aim for note +/- some error
                cursor_vel = np.random.normal(target_vel, abs(target_vel)*0.05*self.player_vel_dev, None)

                # Update velocity; The player iteratively corrects their velocity when aim for note +/- some error'
                if self.player_vel_dev == 0:
                    cursor_vel = target_vel
                else:
                    cursor_vel = np.random.normal(target_vel, abs(target_vel)*0.05*self.player_vel_dev, None)

            # Aim processing
            if t > 1000*map_data[note_aim_idx, DataCor.IDX_T]:
                if note_aim_idx < len(map_data) - 1:
                    note_aim_idx += 1

            '''
            note_pos = map_data[note_aim_idx, DataCor.IDX_X]
            time_to_note = 1000*map_data[note_aim_idx, DataCor.IDX_T] - t

            if time_to_note == 0:
                cursor_vel = 0
            else:
                cursor_vel = (note_pos - cursor_pos) / time_to_note
            '''

            cursor_pos += cursor_vel*simulation_step

            # Tap processing
            is_within_hit_timing = \
                (t >= hit_timing - simulation_step/2) and \
                (t <  hit_timing + simulation_step/2)

            if is_within_hit_timing:
                #print(t, note_timing, int(cursor_pos), map_data[note_act_idx, DataCor.IDX_X], int(cursor_pos + cursor_vel*(note_timing - t)), cursor_vel*(note_timing - t))
                #input()

                # Simulate hit and record position
                replay_data[replay_idx, DataCor.IDX_T] = t/1000
                replay_data[replay_idx, DataCor.IDX_X] = int(cursor_pos)
                replay_data[replay_idx, DataCor.IDX_Y] = map_data[note_tap_idx, DataCor.IDX_Y]

                if is_late_timing:
                    replay_data[replay_idx, DataCor.IDX_K] = PlayerSimulator.KEY_MISS
                else:
                    replay_data[replay_idx, DataCor.IDX_K] = PlayerSimulator.KEY_HIT

                # If within the note, update note
                if note_tap_idx < len(map_data) - 1:
                    note_tap_idx += 1
                    hit_timing, is_late_timing = get_act_params(note_tap_idx)

                replay_idx += 1

            elif mode == PlayerSimulator.RECORD_REPLAY:
                replay_data[replay_idx, DataCor.IDX_T] = t/1000
                replay_data[replay_idx, DataCor.IDX_X] = int(cursor_pos)
                replay_data[replay_idx, DataCor.IDX_Y] = map_data[note_tap_idx, DataCor.IDX_Y]

                replay_idx += 1

            
        #print(f'elapsed: {time.time() - time_start}')

        return replay_data