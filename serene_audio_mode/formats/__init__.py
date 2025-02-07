import av
import numpy as np

import av
import numpy as np

def inspect_audio_tracks(video_file_path: str):
    """
    Inspects and prints detailed information about all audio tracks in a video file.

    Args:
        video_file_path: The path to the video file.

    Raises:
        FileNotFoundError: If the video file does not exist.
        av.error.AVError: If the file cannot be opened or other PyAV errors occur.
        RuntimeError: If unexpected errors occur.
    """
    try:
        with av.open(video_file_path) as container:
            audio_streams = [stream for stream in container.streams if stream.type == 'audio']

            if not audio_streams:
                print(f"No audio tracks found in '{video_file_path}'.")
                return

            for i, stream in enumerate(audio_streams):
                print(f"\n--- Audio Track {i + 1} ---")
                print(f"  Index: {stream.index}")
                print(f"  Codec: {stream.codec_context.name}")
                print(f"  Format: {stream.format.name if stream.format else 'N/A'}")
                print(f"  Sample Rate: {stream.sample_rate} Hz")
                print(f"  Bit Rate: {stream.bit_rate} bits/s")
                print(f"  Channels: {stream.channels}")
                print(f"  Layout: {stream.layout.name if stream.layout else 'N/A'}")
                print(f"  Time Base: {stream.time_base}")
                print(f"  Duration (seconds): {float(stream.duration * stream.time_base) if stream.duration else 'N/A'}")

                # Analyze the first frame for frame-specific properties
                try:
                    first_frame = next(container.decode(stream))  # Get the first frame
                    print(f"  First Frame Samples: {first_frame.samples}")
                    print(f"  First Frame Format: {first_frame.format.name}")
                    print(f"  First Frame PTS: {first_frame.pts}")
                    print(f"  First Frame DTS: {first_frame.dts}")


                except StopIteration:
                    print("  No frames found in this audio track.")
                    continue #proceed with next track
                except av.error.AVError as e:
                    print(f"  Error decoding first frame: {e}")
                    continue # skip the rest of processing for current stream

                # Calculate total frame count and byte size (more accurate)
                total_frames = 0
                total_bytes = 0
                try:
                    for frame in container.decode(stream):
                        total_frames += 1
                        total_bytes += frame.samples * frame.format.bytes * frame.layout.channels

                except av.error.AVError as e:
                     print(f"  Error decoding frames for total count/size: {e}")


                print(f"  Total Frames: {total_frames}")
                print(f"  Total Byte Size: {total_bytes:,} bytes ({total_bytes / (1024 * 1024):.2f} MB)")


    except FileNotFoundError:
        print(f"Error: Video file not found: '{video_file_path}'")
    except av.error.AVError as e:
        print(f"Error: AVError opening or processing '{video_file_path}': {e}")
    except RuntimeError as e:
        print(f"Error: RuntimeError during inspection of '{video_file_path}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

      

def load_audio_track_from_container(video_file_path: str) -> tuple[np.ndarray, int]:
    """
    Loads the first audio track from a video file, converts it to mono,
    and returns a NumPy array of audio samples along with the sample rate.

    Args:
        video_file_path: Path to the video file.

    Returns:
        A tuple containing:
            - A NumPy array of floats (mono audio samples, [-1.0, 1.0]).
            - The sample rate of the audio (in Hz).

    Raises:
        FileNotFoundError: If the video file does not exist.
        av.error.AVError:  If file open/decode errors occur (PyAV).
        RuntimeError:  If no audio stream, no frames, or unexpected errors.
        ValueError: If unsupported audio codec or sample format conversion fails.
    """
    try:
        with av.open(video_file_path) as container:
            audio_stream = None
            for stream in container.streams:
                if stream.type == 'audio':
                    audio_stream = stream
                    break

            if audio_stream is None:
                raise RuntimeError(f"No audio stream found in '{video_file_path}'.")

            resampler = av.AudioResampler(format='fltp', layout='mono', rate=audio_stream.rate)
            sample_rate = audio_stream.rate

            frames = []
            for frame in container.decode(audio=0):
                resampled_frame = resampler.resample(frame)
                frames.append(resampled_frame)
           
            if not frames:
                raise RuntimeError(f"No audio frames decoded from '{video_file_path}'.")

            audio_data = np.concatenate([f.planes[0] for f in frames]) # type: ignore
            return audio_data, sample_rate

    except FileNotFoundError:
        raise FileNotFoundError(f"Video file not found: '{video_file_path}'.")
    except av.error.AVError as e:
        raise av.error.AVError(f"Error opening or decoding '{video_file_path}': {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Runtime error during audio loading from '{video_file_path}': {e}")
    except ValueError as e:
        raise ValueError(f"ValueError processing '{video_file_path}': {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred processing '{video_file_path}': {e}")



def _concatenate_audio_planes(frames: list[av.AudioFrame]) -> np.ndarray:
    """
    Concatenates audio planes from a list of AudioFrames into a single NumPy array.
    Optimized for efficiency.  Internal helper function.
    """
    # Pre-allocate the output array for efficiency.
    total_samples = sum(f.samples for f in frames)
    if len(frames) > 0 and frames[0].planes: # checking if frames exist and has at least one plane
      output_array = np.empty(total_samples, dtype=frames[0].planes[0].dtype)
      offset = 0
      for frame in frames:
          num_samples = frame.samples
          output_array[offset:offset + num_samples] = frame.planes[0]  # type: ignore
          offset += num_samples
    else: # handle the case if len(frames)==0
        output_array = np.array([])

    return output_array


def load_audio_track_from_container_optimized(video_file_path: str) -> tuple[np.ndarray, int]:
    """
    Loads the first audio track (optimized), converts to mono, and returns samples + rate.
    Optimized version using pre-allocation for concatenation.

    Args:
        video_file_path: Path to the video file.

    Returns:
        Tuple: (NumPy array of floats (mono audio, [-1.0, 1.0]), sample rate (Hz)).

    Raises:
        FileNotFoundError: If the file does not exist.
        av.error.AVError: File open/decode errors (PyAV).
        RuntimeError:  No audio, no frames, or unexpected errors.
        ValueError: Unsupported codec or format conversion.
    """
    try:
        with av.open(video_file_path) as container:
            audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
            if audio_stream is None:
                raise RuntimeError(f"No audio stream found in '{video_file_path}'.")

            # Use the stream's sample rate for the resampler.  This avoids
            # unnecessary resampling if the input is already at the desired rate.
            resampler = av.AudioResampler(format='fltp', layout='mono', rate=audio_stream.time_base.denominator)
            sample_rate = audio_stream.time_base.denominator

            frames = []
            for frame in container.decode(audio=0):
                resampled_frame = resampler.resample(frame)
                # resampler.resample() is very fast -- it's essentially a
                # single FFmpeg function call (swr_convert) per frame.
                frames.append(resampled_frame)

            if not frames:
                raise RuntimeError(f"No audio frames decoded from '{video_file_path}'.")

            # Use the optimized concatenation helper.
            audio_data = _concatenate_audio_planes(frames)
            return audio_data, sample_rate

    except FileNotFoundError:
        raise FileNotFoundError(f"Video file not found: '{video_file_path}'.")
    except av.error.AVError as e:
        raise av.error.AVError(f"Error opening or decoding '{video_file_path}': {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Runtime error processing '{video_file_path}': {e}")
    except ValueError as e:
        raise ValueError(f"ValueError processing '{video_file_path}': {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error processing '{video_file_path}': {e}")