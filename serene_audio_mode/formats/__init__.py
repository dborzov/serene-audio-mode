import av
import numpy as np
import os
import soundfile as sf
import re


def save_audio_as_mp3(y, sr, output_filename):
    if y.ndim > 1 and y.shape[0] < y.shape[1]:
        y = y.T
    if np.issubdtype(y.dtype, np.floating):
        y = np.int16(y / np.max(np.abs(y)) * 32767)
    sf.write(output_filename, y, sr, format='mp3')


def inspect_audio_tracks(video_file_path: str):
    """
    Quickly inspects audio track information, including file metadata.

    Args:
        video_file_path: Path to the video file.

    Raises:
        FileNotFoundError: If the video file does not exist.
         av.FFmpegError: If file open/decode errors occur (PyAV).
        RuntimeError: If unexpected errors occur.
    """
    try:
        file_size = os.path.getsize(video_file_path)
        print(f"Total File Size: {file_size / (1024 * 1024):,.2f} MB")

        with av.open(video_file_path) as container:
            extensions = ",".join(container.format.extensions)
            print(f"Container format: {container.format.long_name} (file extensions: {extensions})")

            audio_streams = [stream for stream in container.streams if stream.type == 'audio']
            num_audio_tracks = len(audio_streams)
            print(f"Number of Audio Tracks: {num_audio_tracks}")

            video_duration = float(container.duration / av.time_base) if container.duration else 'N/A'
            print(f"Video Duration (seconds): {video_duration:,}")


            for i, stream in enumerate(audio_streams):
                print(f"\n--- Audio Track {i + 1} (streamID: { stream.index })---")
                format_name = stream.codec_context.format.name if stream.codec_context.format else 'N/A'
                if format_name != 'N/A':
                    bytes_per_sample = stream.codec_context.format.bytes
                    calculated_bit_rate = stream.sample_rate * bytes_per_sample * stream.channels
                if video_duration != 'N/A' and format_name != 'N/A':
                    estimated_bytes = int(video_duration * (calculated_bit_rate / 8))
                    print(f"  Bytesize: {estimated_bytes / (1024 * 1024):,.2f} MB")
                else:
                    print("  Bytesize: N/A (Insufficient metadata)")

                print(f"  Codec: {stream.codec_context.name}")
                print(f"  Format: {format_name}")
                if format_name != 'N/A':
                    print(f"  Bytes per sample: {stream.codec_context.format.bytes}")
                stream.codec_context.format.bytes
                print(f"  Sample Rate: {stream.sample_rate} Hz")

                if format_name != 'N/A':
                    print(f"  Bit Rate: {calculated_bit_rate:,} bits/s")
                else:
                    print("  Bit Rate: N/A (Unknown sample format)")

                print(f"  Channels: {stream.channels}")
                print(f"  Layout: {stream.layout.name if stream.layout else 'N/A'}")
                print(f"  Time Base: {stream.time_base}")
                print(f"  Duration (seconds): {video_duration}")



                try:
                    first_frame = next(container.decode(stream))
                    print(f"  First Frame Samples: {first_frame.samples}")
                    print(f"  First Frame Format: {first_frame.format.name}")
                    print(f"  First Frame PTS: {first_frame.pts}")
                    print(f"  First Frame DTS: {first_frame.dts}")
                except StopIteration:
                    print("  No frames found in this audio track.")
                    continue
                except  av.FFmpegError as e:
                    print(f"  Error decoding first frame: {e}")
                    continue
                # Metadata (Tags)
                if stream.metadata:
                    print("  Metadata (Key:Value pairs):")
                    for key, value in stream.metadata.items():
                        print(f"    [K:{key}]: V:{value}]")
                else:
                    print("  Metadata: None")
                print("---------------")



    except FileNotFoundError:
        print(f"Error: Video file not found: '{video_file_path}'")
    except  av.FFmpegError as e:
        print(f"Error: AVError opening or processing '{video_file_path}': {e}")
    except RuntimeError as e:
        print(f"Error: RuntimeError during inspection of '{video_file_path}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



def extract_audio_track_from_container(video_file_path: str, verbose: bool = True) -> tuple[np.ndarray, int]:
    """
    Loads the first audio track from a video file, converts it to mono,
    and returns a NumPy array of audio samples along with the sample rate.

    Args:
        video_file_path: Path to the video file.
        verbose: Whether to print progress messages. Default is True.

    Returns:
        A tuple containing:
            - A NumPy array of floats (mono audio samples, [-1.0, 1.0]).
            - The sample rate of the audio (in Hz).

    Raises:
        Exception:  If any error happens.
    """

    with av.open(video_file_path) as container:
        audio_stream = next((s for s in container.streams if s.type == 'audio'), None)
        if audio_stream is None:
            raise RuntimeError(f"No audio stream found in '{video_file_path}'.")
        sample_rate = audio_stream.sample_rate
        duration_seconds = container.duration / av.time_base
        if verbose:
            print(f"Video Duration: {duration_seconds}s and sample rate {sample_rate} Hz")

        buffer = None
        buffer_size = 0
        for idx, frame in enumerate(container.decode(audio_stream)):
            f = frame.to_ndarray()
            if len(f) == 0:
                continue
            if f.ndim > 1:  # if more than one channel, convert to mono for now
                f = np.mean(f, axis=tuple(range(f.ndim - 1)))
            if buffer is None:
                allocate_size = int((duration_seconds + 1)*sample_rate)
                print(f"Allocating buffer of size {allocate_size}...")
                buffer = np.zeros( (allocate_size,), dtype=f.dtype)
            buffer[buffer_size: buffer_size + len(f)] = f[:]
            buffer_size += len(f)
            if verbose and idx % 100 == 0:
                seconds_processed = buffer_size / sample_rate  # Calculate processed time
                print(f"Processed {idx} frames ({seconds_processed:.2f} seconds)...\r", end="") 
        return buffer[:buffer_size], sample_rate



def shift_subtitle_time(srt_file_path, shift_seconds):
    """Shifts the timestamps in an SRT file by a specified number of seconds.

    Args:
        srt_file_path: Path to the SRT file.
        shift_seconds:  The number of seconds to shift the timestamps by.
                         Can be positive (shift forward) or negative (shift backward).

    Returns:
       A string containing the modified SRT file content, or None if an error occurred.
    """

    try:
        with open(srt_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {srt_file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

    modified_lines = []
    for line in lines:
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', line)
        if match:
            try:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())

                # Convert to seconds and shift
                total_seconds1 = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                total_seconds2 = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0

                shifted_seconds1 = total_seconds1 + shift_seconds
                shifted_seconds2 = total_seconds2 + shift_seconds

                # Handle negative times (clamp to 00:00:00,000)
                if shifted_seconds1 < 0:
                    shifted_seconds1 = 0
                if shifted_seconds2 < 0:
                    shifted_seconds2 = 0
                    
                # Convert back to HH:MM:SS,mmm format
                new_h1, remaining_seconds1 = divmod(shifted_seconds1, 3600)
                new_m1, remaining_seconds1 = divmod(remaining_seconds1, 60)
                new_s1, new_ms1 = divmod(remaining_seconds1, 1)
                new_ms1 = int(round(new_ms1 * 1000))  # Round milliseconds

                new_h2, remaining_seconds2 = divmod(shifted_seconds2, 3600)
                new_m2, remaining_seconds2 = divmod(remaining_seconds2, 60)
                new_s2, new_ms2 = divmod(remaining_seconds2, 1)
                new_ms2 = int(round(new_ms2 * 1000))
              
                # Ensure correct formatting (leading zeros)
                new_time_str = f"{int(new_h1):02d}:{int(new_m1):02d}:{int(new_s1):02d},{new_ms1:03d} --> {int(new_h2):02d}:{int(new_m2):02d}:{int(new_s2):02d},{new_ms2:03d}"
                modified_lines.append(new_time_str + "\n")

            except ValueError:
                print(f"Error parsing timestamp: {line.strip()}")
                return None  # Invalid timestamp format
        else:
            modified_lines.append(line)  # Keep non-timestamp lines as they are

    return "".join(modified_lines)

