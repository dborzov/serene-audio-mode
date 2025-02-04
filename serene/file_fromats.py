import numpy as np
import soundfile as sf


def save_audio_as_mp3(y, sr, output_filename):
    if y.ndim > 1 and y.shape[0] < y.shape[1]:
        y = y.T
    if np.issubdtype(y.dtype, np.floating):
        y = np.int16(y / np.max(np.abs(y)) * 32767)
    sf.write(output_filename, y, sr, format='mp3')
