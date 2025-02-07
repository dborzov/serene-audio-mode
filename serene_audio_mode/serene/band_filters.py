from scipy.signal import butter, sosfiltfilt



def apply_filters(waveform, sr, low_cutoff_freq, mid_range_freq, bass_weight):
    sos_low = butter(2, low_cutoff_freq, btype='low', analog=False, output='sos', fs=sr)
    sos_high = butter(2, mid_range_freq , btype='high', analog=False, output='sos', fs=sr)
    filtered_low = sosfiltfilt(sos_low, waveform)
    filtered_high = sosfiltfilt(sos_high, waveform)

    return bass_weight*filtered_low + waveform, filtered_high
