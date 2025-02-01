import argparse, os
import warnings
import librosa
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

# Parameters
TIME_TICK = 0.25  # in seconds
BUTTER_ORDER = 5
FREQ_SUB = 60
FREQ_BASS = 250
RMS_THRESHOLD = 0.01
FADE_DURATION = 0.20 # in seconds




def split_into_bands(waveform, sr):
    sos_sub_bass = butter(BUTTER_ORDER, FREQ_SUB, btype='lowpass', output='sos', fs=sr)
    sos_bass = butter(BUTTER_ORDER, (FREQ_SUB, FREQ_BASS), btype='bandpass', output='sos', fs=sr)
    sos_high = butter(BUTTER_ORDER, FREQ_BASS, btype='highpass', output='sos', fs=sr)
    sub_bass_audio = sosfilt(sos_sub_bass, waveform)
    bass_audio = sosfilt(sos_bass, waveform)
    high_audio = sosfilt(sos_high, waveform)
    return sub_bass_audio, bass_audio, high_audio



def calc_rms(waveform, sr):
    obnoxious_ranges = []
    samples_per_period = int(TIME_TICK * sr)
    num_periods = int(np.ceil(len(waveform) / samples_per_period))
    cur_start = None
    for i in range(num_periods):
        start = i * samples_per_period
        end = min((i + 1) * samples_per_period, len(waveform))  # Handle the last period
        rms_value = np.sqrt(np.mean(waveform[start:end]**2, dtype=np.float64))
        if rms_value > RMS_THRESHOLD:
             if cur_start is None:
                cur_start = start
        elif cur_start is not None:
                obnoxious_ranges.append( (cur_start, end) )
                cur_start = None
    if cur_start is not None:
        end = len(waveform)
        obnoxious_ranges.append((cur_start, end))
    return obnoxious_ranges


def smooth_fade(waveform, start_sample, end_sample, target_level, sr):
    fade_number_of_samples = int(FADE_DURATION*sr)
    
    # Ensure everything is within limits
    start_sample = max(0, start_sample)
    end_sample = min(len(waveform), end_sample)
    start_fade_sample = max(0, start_sample - fade_number_of_samples)
    end_fade_sample = min(len(waveform), end_sample + fade_number_of_samples)

    waveform[start_sample:end_sample] *= target_level
    if start_sample > start_fade_sample:
        fade_in_window = np.linspace(1, target_level, start_sample - start_fade_sample)
        waveform[start_fade_sample:start_sample] *= fade_in_window
    if end_fade_sample > end_sample:
        fade_out_window = np.linspace(target_level, 1, end_fade_sample - end_sample)
        waveform[end_sample:end_fade_sample] *= fade_out_window



def save_audio_as_mp3(y, sr, output_filename):
    # soundfile expects the data in (samples, channels) format, so transpose if necessary
    if y.ndim > 1 and y.shape[0] < y.shape[1]:
        y = y.T
    # If y is a float array, scale it to the range of int16
    if np.issubdtype(y.dtype, np.floating):
        y = np.int16(y / np.max(np.abs(y)) * 32767)
    # Write to MP3 using soundfile
    sf.write(output_filename, y, sr, format='mp3')


def process_audio(audio_path, output_filepath):
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    y, sr = librosa.load(audio_path)
    warnings.resetwarnings()
    print(f"succesfully loaded {audio_path}")
    duration = y.size / sr
    print(f"  audio is at the sampling rate: {sr}")
    print(f"  duration is {duration:.2f}s")
    sub_bass_audio, bass_audio, high_audio = split_into_bands(y, sr)
    print(f"succesfully applied bandpass filtering")
    obnoxious_ranges = calc_rms(sub_bass_audio, sr)
    print(f"found {len(obnoxious_ranges)} the ranges of excessive noise")
    for start_sample, end_sample in obnoxious_ranges:
        smooth_fade(bass_audio, start_sample, end_sample, 0.0001, sr)
        smooth_fade(high_audio, start_sample, end_sample, 0.01, sr)
    print(f"applied obnoxious noise reduction")
    y *= 0
    y += bass_audio + high_audio
    print(f"audio processing complete")
    save_audio_as_mp3(y, sr, output_filepath)
    print(f"succesfully saved output to {output_filepath}")





def main():
    parser = argparse.ArgumentParser(
        description="Outputs calmer verison of the audiotrack."
    )
    parser.add_argument(
        "audio_path", 
        help="Path to the input audio file (any format supported by librosa)"
    )
    args = parser.parse_args()
    input_dir = os.path.dirname(args.audio_path)
    base_filename, input_ext = os.path.splitext(os.path.basename(args.audio_path))
    output_filename = f"{base_filename}_serene1.mp3"
    output_filepath = os.path.join(input_dir, output_filename)
    process_audio(args.audio_path, output_filepath)

if __name__ == "__main__":
    main()