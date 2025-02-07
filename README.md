## serene-audio-mode

Tired of dramatic volume swings in modern movies? Wishing you could watch something without disturbing those who are close to you?




 `serene-audio-mode` is a tool that lets you rebalance the audiotracks of videos by selectively reducing the volume of loud, low pitch, and jarring sounds (explosions, gunfire, and aggressive musical beats), while leaving the rest (things like dialogue) untouched. No more scrambling for the remote when a whisper is followed by an explosion that reverberates down your spine – just consistent, comfortable listening.

More on how this works exactly can be found [here](https://github.com/dborzov/serene-audio-mode).

To get a general idea about what the result feels like compare [before](https://www.youtube.com/watch?v=MNZZhTXw72M) and [after](https://youtu.be/-Cy1-18S5A0).

![screenshot](https://www.borzov.ca/img/serene/comic.jpg)





## Install

This tool relies on [ffmpeg](https://www.ffmpeg.org/) to read and write to the video files. 

Install it with pip or download the latest release binary.




:

```
git clone https://github.com/dborzov/serene-audio-mode.git
```

## Usage

The basic usage:

```bash
python serene.py [audio_input_path] [audio_output_path] [options]
```

**Positional Arguments:**

*   `audio_input_path`: Path to the input audio file. *Default:* `audiotrack.mp3`
*   `audio_output_path`: Path to the output audio file where the processed audio will be saved. *Default:* `audiotrack_serene.mp3`

**Optional Arguments:**

| Short | Long              | Default | Description                                                                                                                               |
| :---- | :---------------- | :------ | :---------------------------------------------------------------------------------------------------------------------------------------- |
| `-tt` | `time_tick`     | `0.01`  | Duration of intervals for RMS loudness evaluation (in seconds).                                                                         |
| `-tf` | `time_fade`     | `1.0`   | Duration of intervals of constant volume configuration (in seconds).                                                                    |
| `-bw` | `bass_weight`   | `4`     | The relative importance/weight paid to the low-band part vs the high-band part for loudness level detection.                          |
| `-lc` | `low_cutoff_freq` | `70.0`  | The sub-bass cut-off frequency for obnoxious noise detection (in Hz).                                                                 |
| `-mr` | `mid_range_freq` | `100.0` | Sounds below this frequency are cut out of the audiotrack by default (in Hz).                                                          |
| `-tv` | `tap_value`     | `32`    | How steep is the gain function: `tap_value * tanh(levels / tap_value)`. A higher value means steeper volume adjustments. |



## WIP warning

This project is work-in-progress and not especially user-friendly yet. 

Specifically, right now the script only takes mp3s of audiotracks as an input and outputs the updated version as another mp3 file.

For now one has to use `ffmpeg` yourself to extract the audiotrack from a video file, run `serene-audio-mode` python script on it, and then add back to the same video file the `serene-mode` version as an extra audiotrack with a `serene` label:

```
ffmpeg -i myvideo.avi -vn audiotrack.mp3
python serene.py audiotrack.mp3  audiotrack_serene_version.mp3
ffmpeg -i myvideo.avi -i audiotrack_serene_version.mp3.mp3 -map 0 -map 1:a -c copy -metadata:s:a:1 title="serene" -disposition:a:1 default myvideo_with_serene.avi
```

 The current version is built on top of Python+Numpy ecosystem for speed of development.  Once I am confident the algorithm does not need any more major changes, the plan will be to rewrite this in something like Go or C and take some effort to optimize the performance. 

This will make it faster and easier to distribute as a standalone binary. And make potential embedding scenarios down the line easier.




