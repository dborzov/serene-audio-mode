import argparse
import serene
import librosa
import numpy as np
import humanize
import time

def main():
    parser = argparse.ArgumentParser(
        description="serene-audio-mode is a tool that lets you rebalance the audiotracks of video files by selectively reducing the volume of loud, bass-heavy, and jarring sounds (explosions, gunfire, and aggressive musical beats), while leaving the rest (like dialogue) untouched."
    )

    parser.add_argument("audio_input_path", type=str, help="Path to the input audio file (default: '/k/dataset/audiotrack.mp3')",
                        nargs='?', default='audiotrack.mp3')
    parser.add_argument("audio_output_path", type=str, help="Path to the output audio file (default: '/k/dataset/audiotrack_serene03.mp3')",
                        nargs='?', default='audiotrack_serene.mp3')
    parser.add_argument("-tt", "--time_tick", type=float, default=0.01, help="Duration of intervals for RMS loudness evaluation (in seconds) (default: 0.01)")
    parser.add_argument("-tf", "--time_fade", type=float, default=1.0, help="Duration of intervals of constant volume configuration (in seconds) (default: 1.0)")
    parser.add_argument("-bw", "--bass_weight", type=float, default=4, help="The relative importance/weight paid to the low-band part vs the high-band part for loudness level detection (default: 4)")
    parser.add_argument("-lc", "--low_cutoff_freq", type=float, default=70.0, help="The sub-bass cut-off frequency for obnoxious noise detection (in Hz) (default: 70.0)")
    parser.add_argument("-mr", "--mid_range_freq", type=float, default=100.0, help="Sounds below this frequency are cut out of the audiotrack by default (in Hz) (default: 100.0)")
    parser.add_argument("-tv", "--tap_value", type=int, default=32, help="How steep is the gain function: tap_value*tanh(levels / tap_value) (default: 32)")

    args = parser.parse_args()

    audio_input_path = args.audio_input_path
    audio_output_path = args.audio_output_path
    TIME_TICK = args.time_tick
    TIME_FADE = args.time_fade
    BASS_WEIGHT = args.bass_weight
    LOW_CUTOFF_FREQ = args.low_cutoff_freq
    MID_RANGE_FREQ = args.mid_range_freq
    TAP_VALUE = args.tap_value

    print("Starting audio processing...")
    print("\nParameters:")
    print(f"  Input Audio Path: {audio_input_path}")
    print(f"  Output Audio Path: {audio_output_path}")
    print(f"  Time Tick: {TIME_TICK} s")
    print(f"  Time Fade: {TIME_FADE} s")
    print(f"  Bass Weight: {BASS_WEIGHT}")
    print(f"  Low Cutoff Frequency: {LOW_CUTOFF_FREQ} Hz")
    print(f"  Mid Range Frequency: {MID_RANGE_FREQ} Hz")
    print(f"  Tap Value: {TAP_VALUE}")

    print("\nProcessing Steps:")
    print("1. Load Audio")
    print("2. Calculate Parameters")
    print("3. Apply Filters")
    print("4. Analyze Loudness (RMS)")
    print("5. Calculate Gain Levels")
    print("6. Adjust Volume")
    print("7. Save Output")

    # 1. Load Audio
    print("\n[1/7] Loading audio...")
    start_time = time.time()
    y, sr = librosa.load(audio_input_path)
    duration = y.size / sr
    print(f"  the track's size is {y.size} ({humanize.naturalsize(y.nbytes)})")
    print(f"  the sampling rate: {sr}; duration is {duration:.3f}")
    print(f"  Audio loaded in {time.time() - start_time:.2f} seconds")

    # 2. Calculate Parameters
    print("\n[2/7] Calculating parameters...")
    start_time = time.time()
    tick_size = int(TIME_TICK * sr)
    ticks_in_fade = int(TIME_FADE / TIME_TICK)
    print(f"  Fine interval size is {tick_size} samples")
    print(f"  Parameters calculated in {time.time() - start_time:.2f} seconds")

    # 3. Apply Filters
    print("\n[3/7] Applying filters...")
    start_time = time.time()
    y_bassed, y_clear = serene.apply_filters(y, sr, LOW_CUTOFF_FREQ, MID_RANGE_FREQ, BASS_WEIGHT)
    print(f"  Filtering done in {time.time() - start_time:.2f} seconds")

    # 4. Analyze Loudness (RMS)
    print("\n[4/7] Analyzing loudness...")
    start_time = time.time()
    rms1 = serene.calc_rms(y_bassed, tick_size)
    rms2 = serene.calc_rms(np.roll(2*y, - tick_size// 2), tick_size)
    rms = rms1+rms2
    print(f"  Loudness analysis done in {time.time() - start_time:.2f} seconds")

    # 5. Calculate Gain Levels
    print("\n[5/7] Calculating gain levels...")
    start_time = time.time()
    fade_levels = serene.calc_tops(rms, ticks_in_fade)
    print(f"  Gain levels calculated in {time.time() - start_time:.2f} seconds")

    # 6. Adjust Volume
    print("\n[6/7] Adjusting volume...")
    start_time = time.time()
    y_serene2 = serene.smooth_fade(y_clear.copy(), serene.calc_gains(fade_levels, TAP_VALUE), ticks_in_fade * tick_size)
    print(f"  Volume adjusted in {time.time() - start_time:.2f} seconds")

    # 7. Save Output
    print("\n[7/7] Saving output...")
    start_time = time.time()
    serene.save_audio_as_mp3(y_serene2, sr, audio_output_path)
    print(f"  Output saved to {audio_output_path} in {time.time() - start_time:.2f} seconds")

    print("\n... complete\n\n")

if __name__ == "__main__":
    main()