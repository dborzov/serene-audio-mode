import numpy as np

def pad_to_match(waveform, multiple):
    remainder = len(waveform) % multiple
    if remainder == 0:
        return waveform
    return np.pad(waveform, (0, multiple - remainder),  mode='constant', constant_values=0)

def calc_rms(waveform, period):
    waveform = pad_to_match(waveform, period)
    waveform_ticks = waveform.reshape(-1, period)
    return 10*np.sum(waveform_ticks**2, axis=1, dtype=np.float64)


def calc_tops(rms, ticks_in_fade):
    rms = pad_to_match(rms, ticks_in_fade)
    rms_fades = rms.reshape(-1, ticks_in_fade)
    return np.max(rms_fades, axis=1)
