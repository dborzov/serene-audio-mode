import numpy as np
from band_filters import *
from rms import *


def calc_gains(levels, tap_value):
    desired_levels =  tap_value*np.tanh(levels / tap_value)
    return desired_levels / levels


def smooth_fade(waveform, levels, fade_size):
    left_value = np.roll(levels, 1)
    left_value[0] = np.PINF
    left_edge = np.minimum(levels, left_value)

    right_value = np.roll(levels, -1)
    right_value[-1] = np.PINF
    right_edge = np.minimum(levels, right_value)

    for i in range(len(levels)):
        upper_limit = min((i+1)*fade_size, waveform.size )
        if upper_limit > i*fade_size:
            waveform[i*fade_size: upper_limit] *= np.geomspace(left_edge[i], right_edge[i], upper_limit - i*fade_size)
    return waveform
