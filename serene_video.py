import argparse, os
import av


def main():
    parser = argparse.ArgumentParser(
        description="Outputs calmer verison of the audiotrack."
    )
    parser.add_argument(
        "input_path", 
        help="Path to the input video file"
    )
    args = parser.parse_args()
    container = av.open(args.input_path)
    for frmae

