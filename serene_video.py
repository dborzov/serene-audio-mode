import argparse
import ffmpeg
import librosa
import numpy as np
import os

def extract_audio_and_load(video_path, audio_track_index=0):
    """
    Extracts the first audio track from a video file using ffmpeg-python and loads it with librosa.

    Args:
        video_path: Path to the video file.
        audio_track_index: Index of the audio track to extract (default: 0).

    Returns:
        A tuple containing:
        - y: The audio time series (NumPy array)
        - sr: The sampling rate of the audio
        - audio_path: The path to the extracted audio file (or None if extraction failed)
    """

    # Construct a temporary path for the extracted audio
    base_filename, _ = os.path.splitext(os.path.basename(video_path))
    temp_audio_path = os.path.join(os.path.dirname(video_path), f"{base_filename}_temp_audio.wav")

    try:
        # Extract audio using ffmpeg
        (
            ffmpeg
            .input(video_path)
            .output(temp_audio_path, map=f"0:a:{audio_track_index}")  # Select audio stream by index
            .run(overwrite_output=True)
        )
        print(f"Audio extracted to: {temp_audio_path}")

        # Load the extracted audio with librosa
        y, sr = librosa.load(temp_audio_path, sr=None, mono=False)  # Load in stereo if present
        print(f"Audio loaded successfully from: {temp_audio_path}")

        return y, sr, temp_audio_path

    except ffmpeg.Error as e:
        print(f"Error extracting audio: {e.stderr.decode()}")
        return None, None, None
    except Exception as e:
        print(f"Error loading audio with librosa: {e}")
        return None, None, None


def main():
    parser = argparse.ArgumentParser(description="Extract and load audio from a video file.")
    parser.add_argument("video_path", help="Path to the video file")

    args = parser.parse_args()

    y, sr, audio_path = extract_audio_and_load(args.video_path)

    if y is not None:
        print(f"Audio loaded successfully. Sampling rate: {sr}")
        print(f"Audio data shape: {y.shape}")

        # You can now work with the audio data 'y' and sample rate 'sr'
        # ...

    if audio_path:
      os.remove(audio_path)
      print(f"Temporary audio file removed: {audio_path}")

if __name__ == "__main__":
    main()