import argparse
import sys
import traceback
from serene_audio_mode import formats  # Assuming you have a formats.py


def inspect_command(args):
    formats.inspect_audio_tracks(args.path)

def load_command(args):
    try:
        audio_data, sample_rate = formats.load_audio_track_from_container_optimized(args.path)
        print(f"Loaded audio track from '{args.path}'.")
        print(f"  Sample Rate: {sample_rate} Hz")
        print(f"  Number of Samples: {len(audio_data)}")
        print(f"  Data Type: {audio_data.dtype}")
    except Exception:
        print(f"An error occurred while loading the audio track from '{args.path}':", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for the command-line tool."""
    parser = argparse.ArgumentParser(
        prog="serene-audio-mode-dev",
        description="Development tools for Serene Audio Mode.",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Preserves newlines in description
    )

    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="subcommand",  # Stores the name of the chosen subcommand
        help="Available subcommands",
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect audio track details of a video file.",
        description="Prints detailed information about all audio tracks in a video file."
    )
    inspect_parser.add_argument("path", help="Path to the video file.")
    inspect_parser.set_defaults(func=inspect_command) # set the function to execute

    # 'load' subcommand
    load_parser = subparsers.add_parser(
        "load",
        help="Load the audio track from a video file.",
        description="Loads the first audio track from a video file and returns it as a NumPy array."
    )
    load_parser.add_argument("path", help="Path to the video file.")
    load_parser.set_defaults(func=load_command)

    args = parser.parse_args()


    if args.subcommand is None:
        parser.print_help() # display general help and exit
        sys.exit(1)
    else:
      args.func(args) # calls one of registered functions

if __name__ == "__main__":
    main()
