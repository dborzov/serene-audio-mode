from scipy.signal import butter, sosfiltfilt, freqz
import librosa
import numpy as np
import IPython.display as ipd
import matplotlib.pyplot as plt
import humanize
import soundfile as sf


audio_input_path = '/k/dataset/audiotrack.mp3'
audio_output_path = '/k/dataset/audiotrack_serene03.mp3'
# audio_input_path = '/k/dataset/audiotrack.mp3'
# audio_output_path = '/k/dataset/audiotrack_serene2.mp3'


# Load the audio file
y, sr = librosa.load(audio_input_path)
duration = y.size / sr
print(f"the track's size is {y.size} ({humanize.naturalsize(y.nbytes)})")
print(f"the sampling rate: {sr}; duration is {duration:.3f}")


# Parameters
TIME_TICK = 0.01  # in seconds
TIME_FADE = 1.0 # in seconds
BUTTER_ORDER = 5
FREQ_SUB = 60
FREQ_BASS = 250
RMS_THRESHOLD = 0.01

tick_size = int(TIME_TICK*sr)
ticks_in_fade = int(TIME_FADE / TIME_TICK)

print(f"fine interval size is {tick_size} samples")


LOW_CUTOFF_FREQ = 70.0
MID_RANGE_FREQ = 100.0


def apply_filters(waveform, sr):
    sos_low = butter(2, LOW_CUTOFF_FREQ, btype='low', analog=False, output='sos', fs=sr)
    sos_high = butter(2, MID_RANGE_FREQ , btype='high', analog=False, output='sos', fs=sr)
    filtered_low = sosfiltfilt(sos_low, waveform)
    filtered_high = sosfiltfilt(sos_high, waveform)

    return 4*filtered_low + waveform, filtered_high

    
y_bassed, y_clear = apply_filters(y,sr)
print(f"filtering done")

def pad_to_match(waveform, multiple):
    remainder = len(waveform) % multiple
    if remainder == 0:
        return waveform
    return np.pad(waveform, (0, multiple - remainder),  mode='constant', constant_values=0)

def calc_rms(waveform, period):
    waveform = pad_to_match(waveform, period)
    waveform_ticks = waveform.reshape(-1, period)
    return 10*np.sum(waveform_ticks**2, axis=1, dtype=np.float64)


def calc_tops(rms):
    rms = pad_to_match(rms, ticks_in_fade)
    rms_fades = rms.reshape(-1, ticks_in_fade)
    return np.max(rms_fades, axis=1)


rms1 = calc_rms(y_bassed, tick_size)
rms2 = calc_rms(np.roll(y_bassed, - tick_size// 2), tick_size)
rms = rms1+rms2
fade_levels = calc_tops(rms)
print(f"loudness analysis done")

TAP_VALUE = 32
def calc_gains(levels):
    desired_levels =  TAP_VALUE*np.tanh(levels / TAP_VALUE)
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


y_serene2 = smooth_fade(y_clear.copy(), calc_gains(fade_levels), ticks_in_fade*tick_size)
print(f"adjusting... done")


def save_audio_as_mp3(y, sr, output_filename):
    # soundfile expects the data in (samples, channels) format, so transpose if necessary
    if y.ndim > 1 and y.shape[0] < y.shape[1]:
        y = y.T
    # If y is a float array, scale it to the range of int16
    if np.issubdtype(y.dtype, np.floating):
        y = np.int16(y / np.max(np.abs(y)) * 32767)
    # Write to MP3 using soundfile
    sf.write(output_filename, y, sr, format='mp3')


save_audio_as_mp3(y_serene2, sr, audio_output_path)
print(f"saved the result to {audio_output_path}\n... complete\n\n")
