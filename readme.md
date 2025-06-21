# AVPlay

## Table of Contents

1. [**Introduction**](#1-introduction)
2. [**Installation & Configuration**](#2-installation--configuration)
3. [**Quick Start**](#3-quick-start)
4. [**Core Data Types & Enums**](#4-core-data-types--enums)
5. [**Player API**](#5-player-api)
   - [Common Player Interface (`AVPlayer`)](#common-player-interface-avplayer)
   - [FMOD Audio Player (`FMODAudioPlayer`)](#fmod-audio-player-fmodaudioplayer)
   - [MPV Video Player (`MPVVideoPlayer`)](#mpv-video-player-mpvvideoplayer)
   - [VLC Video Player (`VLCVideoPlayer`)](#vlc-video-player-vlcvideoplayer)
6. [**Media Instance API (`AVMediaInstance`)**](#6-media-instance-api-avmediainstance)
7. [**Audio & Video Filters**](#7-audio--video-filters)
   - [FMOD Audio Filters](#fmod-audio-filters)
   - [MPV Audio Filters](#mpv-audio-filters)
   - [VLC Audio Filters](#vlc-audio-filters)
8. [**Playlist Management API**](#8-playlist-management-api)
   - [`PlaylistEntry`](#playlistentry)
   - [`Playlist`](#playlist)
   - [`PlaylistManager`](#playlistmanager)
9. [**Utility Functions**](#9-utility-functions)
10. [**License**](#10-license)

---

## 1. Introduction

AVPlay is a versatile media playback library that supports multiple media backends (both audio and video) all under a unified API. With added features such as playlist playback, applying audio filters, and more.

### Features

- **Multiple backends supported**, including: 
  - **MPV**: Video playback with FFmpeg supported filters
  - **FMOD**: High performance and low latency playback, with high quality audio filters
  - **VLC**: Simple media playback and widely supported formats
- **Flexible and consistent core API design**, which can be further extended to support more backends
- **Playlist management**: Easily load, create, manage, and save playlists in various formats (M3U, PLS, XSPF, JSON). Supports features like sorting, filtering, and shuffling
- **Apply high quality audio effects/filters** in real time
- And more

---

## 2. Installation & Configuration

### Installation

1. **Install via PyPI**:
   ```bash
   pip install AVPlay
   ```

AVPlay depends on the following libraries: *validators*, *music-tag*, and bindings for each of the supported backends: *python-mpv*, *pyfmodex*, and *python-vlc*.

2. **Install a native media backend**:
   AVPlay requires at least 1 backend available on your system to function properly.

#### FMOD
1. Create an account and download FMOD from the [main website](https://www.fmod.com/download)
2. Install FMOD. Then locate the library files matching your machine's OS and architecture.

#### MPV
1. Download the libmpv library:
   - **Windows**: You can find builds at [shinchiro's builds](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/). You require mpv-2.dll
   - **macOS**: `brew install mpv`
   - **Linux**: `sudo apt-get install libmpv-dev` or `sudo dnf install mpv-libs-devel`

#### VLC
Install the full VLC Media Player application from the [official VideoLAN website](https://www.videolan.org/vlc/).

### Configuration

AVPlay uses environment variables to detect which backend to use and where to find its native libraries. You must set these before importing av_play.

```python
import os

# --- Example for FMOD ---
os.environ["USE_FMOD"] = "1"
# Path to the directory containing fmod.dll or libfmod.so
# Only the path to the folder where the library is located.
os.environ["FMOD_LIB_PATH"] = "./libs/fmod" 

# Now import the library
import av_play
```

---

## 3. Quick Start

```python
import os
os.environ["USE_FMOD"] = "1"
os.environ["FMOD_LIB_PATH"] = "C:/Program Files (x86)/FMOD SoundSystem/FMOD Studio API Windows/api/core/lib/x64"
import av_play as av
import time

filepath = "test.mp3"
player = av.AudioPlayer()
player.init()

print("FMOD Player Initialized.")

try:
    instance = player.create_file_instance(filepath)
    instance.set_volume(0.8)
    instance.play()
    print(f"Playing '{instance.file_path}'...")
    
    while instance.get_playback_state() == av_play.AVPlaybackState.AV_STATE_PLAYING:
        pos = instance.get_position()
        length = instance.get_length()
        print(f"Position: {pos}/{length} seconds", end='\r')
        time.sleep(1)

    print("\nPlayback finished.")

finally:
    print("Releasing resources.")
    player.release()
```

---

## 4. Core Data Types & Enums

These types are used for arguments and return values throughout the library.

### `ParameterValue`
A type alias for values that can be passed to filters.
```python
from typing import Union
ParameterValue = Union[int, float, bool, str]
```

### `AVDevice`
A `dataclass` containing information about an audio output device.
- `media_backend: AVMediaBackend`: The backend this device belongs to.
- `name: str`: The human-readable name of the device.

### `AVError`
Exception raised for all library-specific errors.
- `info: AVErrorInfo`: The category of the error.
- `message: str`: A detailed error message from the backend.

### Enums

#### `AVPlaybackState`
Represents the current playback status of a media instance.
- `AV_STATE_NOTHING`: No media loaded or playback has finished/failed.
- `AV_STATE_STOPPED`: Media is loaded but stopped.
- `AV_STATE_PLAYING`: Media is actively playing.
- `AV_STATE_PAUSED`: Playback is paused.
- `AV_STATE_BUFFERING`: Network stream is buffering.
- `AV_STATE_LOADING`: Initial loading of media.

#### `AVPlaylistMode`
Defines the playback behavior for a playlist.
- `SEQUENTIAL`: Plays tracks in order, then stops.
- `REPEAT_ALL`: Plays tracks in order and repeats the playlist.
- `REPEAT_ONE`: Repeats the current track indefinitely.
- `SHUFFLE`: Plays tracks in a random order.

#### `AVPlaylistState`
Represents the overall state of the playlist controller.
- `STOPPED`: Playlist is stopped.
- `PLAYING`: Playlist is actively playing.
- `PAUSED`: Playlist is paused.
- `FINISHED`: Playlist has finished and is not set to repeat.

#### `AVMuteState`
Represents the audio mute status.
- `AV_AUDIO_MUTED`
- `AV_AUDIO_UNMUTED`

#### `AVMediaType`
The type of media the backend primarily handles.
- `AV_TYPE_AUDIO`
- `AV_TYPE_VIDEO`

#### `AVMediaBackend`
The underlying native library being used.
- `AV_BACKEND_FMOD`
- `AV_BACKEND_MPV`
- `AV_BACKEND_VLC`

#### `AVErrorInfo`
Describes the category of an `AVError` exception.
- `UNKNOWN_ERROR`, `INITIALIZATION_ERROR`, `FILE_NOTFOUND`, `UNSUPPORTED_FORMAT`, `INVALID_HANDLE`, `HTTP_ERROR`, `INVALID_MEDIA_FILTER`, `INVALID_FILTER_PARAMETER`, `INVALID_FILTER_PARAMETER_TYPE`, `INVALID_FILTER_PARAMETER_VALUE`, `INVALID_FILTER_PARAMETER_RANGE`, `UNINITIALIZED`, `NET_ERROR`.

---

## 5. Player API

The `Player` is the main entry point for creating and managing media.

### Common Player Interface (`AVPlayer`)

This is the base API available on `AudioPlayer` and `VideoPlayer`.

#### Initialization & Lifecycle
- `init(self, *args, **kw)`
  - Initializes the backend. Must be called before any other method.
  - **Arguments**: Vary by backend (see concrete player classes below).

- `release(self)`
  - Shuts down the backend and releases all associated resources.

#### Instance Creation
- `create_file_instance(self, file_path: str) -> AVMediaInstance`
  - Creates a media instance for a local file.

- `create_url_instance(self, url: str) -> AVMediaInstance`
  - Creates a media instance for a URL.

#### Playlist Management
- `load_playlist(self, playlist: Playlist, auto_play: bool = False, mode: AVPlaylistMode = AVPlaylistMode.SEQUENTIAL)`
  - Loads a `Playlist` object and controls playback via the `primary_instance`.

- `next(self)`
  - Skips to the next track in the playlist.

- `previous(self)`
  - Goes to the previous track in the playlist.

- `stop_playlist(self)`
  - Stops playlist playback completely.

- `pause_playlist(self)`
  - Pauses the currently playing track in the playlist.

- `resume_playlist(self)`
  - Resumes the currently paused track in the playlist.

- `set_playlist_mode(self, mode: AVPlaylistMode)`
  - Changes the playlist playback mode.

- `set_track_end_callback(self, callback: Callable[[int], None] | None)`
  - Sets a function to be called when a playlist track ends. The callback receives the integer index of the track that finished.

- `get_playlist_state(self) -> AVPlaylistState`
  - Returns the current state of the playlist.

- `get_playlist_mode(self) -> AVPlaylistMode`
  - Returns the current playlist mode.

- `get_current_track_index(self) -> int`
  - Returns the index of the currently playing track.

#### Device Management
- `get_devices(self) -> int`
  - Returns the number of available audio output devices.

- `get_device_info(self, index: int) -> AVDevice`
  - Gets information about a device at a specific index.

- `set_device(self, index: int)`
  - Sets the active audio output device by its index.

- `get_current_device(self) -> int`
  - Gets the index of the currently active device.

### FMOD Audio Player (`FMODAudioPlayer`)
Exposed as `AudioPlayer` when `USE_FMOD` is set. Implements the common `AVPlayer` interface.

- `init(self, max_channels: int = 64)`
  - Initializes the FMOD system.
  - **`max_channels`**: The maximum number of simultaneous sounds.

### MPV Video Player (`MPVVideoPlayer`)
Exposed as `VideoPlayer` when `USE_MPV` is set. Implements the common `AVPlayer` interface and adds video-specific methods.

- `init(self, window: int = None, ytdl_path: str = None, config: dict = {})`
  - Initializes the MPV player.
  - **`window`**: The window ID (WID) to embed the video in.
  - **`ytdl_path`**: Path to a `yt-dlp` executable for URL streaming.
  - **`config`**: A dictionary of MPV options.

- `set_window(self, window: int)`
  - Attaches the video output to a GUI window handle.

- `forward(self, offset: int)` / `backward(self, offset: int)`
  - Seeks forward or backward by `offset` seconds.

- `set_volume_relative(self, direction: str, offset: float)`
  - Adjusts volume. `direction` must be `"up"` or `"down"`.

- `set_fullscreen(self, state: bool)` / `get_fullscreen(self) -> bool`
  - Sets or gets the fullscreen state.

- `set_playback_speed(self, speed: float)`
  - Sets the playback speed (1.0 is normal).

- `set_resolution(self, width: int, height: int)`
  - Applies a video filter to scale the output.

### VLC Video Player (`VLCVideoPlayer`)
Exposed as `VideoPlayer` when `USE_VLC` is set. Implements the common `AVPlayer` interface and adds video-specific methods.

- `init(self, vlc_args: List[str] = [])`
  - Initializes the VLC player.
  - **`vlc_args`**: A list of command-line arguments to pass to the VLC instance.

- `set_window(self, window: int)`
  - Attaches the video output to a GUI window handle (HWND).

- `forward(self, offset: int)` / `backward(self, offset: int)`
  - Seeks forward or backward by `offset` seconds.

- `set_volume_relative(self, direction: str, offset: float)`
  - Adjusts volume. `direction` must be `"up"` or `"down"`.

- `set_fullscreen(self, state: bool)` / `get_fullscreen(self) -> bool`
  - Sets or gets the fullscreen state.

- `set_playback_speed(self, speed: float)`
  - Sets the playback rate (1.0 is normal).

- `set_resolution(self, width: int, height: int)`
  - Applies a video filter to scale the output.

---

## 6. Media Instance API (`AVMediaInstance`)

Controls a single media file or stream. Created via a `Player` object.

### Properties
- `media_type: AVMediaType`
- `media_backend: AVMediaBackend`
- `media_source: AVMediaSource`
- `instance_id: int`
- `file_path: str`

### Loading Methods
- `load_file(self, file_path: str)`
  - Loads media from a local file.
- `load_url(self, url: str)`
  - Loads media from a URL.

### Playback Control
- `play(self)`, `pause(self)`, `stop(self)`
- `mute(self)`, `unmute(self)`
- `set_volume(self, offset: float)`
- `set_position(self, position: int)`
- `set_loop(self, loop: bool)`

### State & Information
- `get_playback_state(self) -> AVPlaybackState`
- `get_mute_state(self) -> AVMuteState`
- `get_length(self) -> int`
- `get_position(self) -> int`
- `get_volume(self) -> float`

### Filter Management
- `apply_filter(self, filter: AVFilter) -> int`
  - Applies a filter and returns its unique ID.
- `remove_filter(self, filter_id: int)`
- `remove_filters(self)`
- `set_parameter(self, filter_id: int, parameter_name: str, parameter_value: ParameterValue)`
- `get_parameter(self, filter_id: int, parameter_name: str) -> ParameterValue | None`

### Cleanup
- `release(self)`
  - Stops playback, removes filters, and releases the instance from the backend.

---

## 7. Audio & Video Filters

Instantiate a filter class and apply it to a media instance.

### FMOD Audio Filters
(from `av_play.fmod_audio_filter`)
- `FMODEchoFilter()`: Parameters: `delay_ms`, `feedback_percent`, `dry_level_db`, `wet_level_db`.
- `FMODReverbFilter()`: Parameters: `decay_time_ms`, `early_delay_ms`, `late_delay_ms`, `hf_reference_hz`, `hf_decay_ratio_percent`, `diffusion_percent`, `density_percent`, `low_shelf_frequency_hz`, `low_shelf_gain_db`, `high_cut_hz`, `early_late_mix_percent`, `wet_level_db`, `dry_level_db`.
- `FMODLowpassFilter()`: Parameters: `cutoff_frequency_hz`, `q_factor`.
- `FMODHighpassFilter()`: Parameters: `cutoff_frequency_hz`, `q_factor`.
- `FMODBandpassFilter()`: Parameters: `center_frequency_hz`, `bandwidth_q`.
- `FMODChorusFilter()`: Parameters: `mix_percent`, `rate_hz`, `depth_percent`.
- `FMODCompressorFilter()`: Parameters: `threshold_db`, `ratio`, `attack_ms`, `release_ms`, `makeup_gain_db`, `use_sidechain`, `linked_channels`.
- `FMODFlangerFilter()`: Parameters: `mix_percent`, `depth_factor`, `rate_hz`.
- `FMODDistortionFilter()`: Parameters: `level_factor`.
- `FMODPitchShiftFilter()`: Parameters: `pitch_scale`, `fft_size_samples`.

### MPV Audio Filters
(from `av_play.mpv_audio_filter`)
- `MPVEchoFilter()`: Parameters: `in_gain`, `out_gain`, `delays`, `decays`.
- `MPVReverbFilter()`: Parameters: `dry`, `wet`, `length`, `irnorm`, `irgain`.
- `MPVLowPassFilter()`: Parameters: `frequency`, `poles`, `width`, `mix`.
- `MPVHighPassFilter()`: Parameters: `frequency`, `poles`, `width`, `mix`.
- `MPVCompressorFilter()`: Parameters: `level_in`, `threshold`, `ratio`, `attack`, `release`, `makeup`, `knee`, `detection`, `mix`.
- `MPVFlangerFilter()`: Parameters: `delay`, `depth`, `regen`, `width`, `speed`, `shape`, `phase`, `interp`.
- `MPVChorusFilter()`: Parameters: `in_gain`, `out_gain`, `delays`, `decays`, `speeds`, `depths`.
- `MPVPitchShiftFilter()`: Parameters: `pitch-scale`, `engine`.
- `MPVLimiterFilter()`: Parameters: `level_in`, `level_out`, `limit`, `attack`, `release`, `asc`, `asc_level`, `level`.
- `MPVBandPassFilter()`: Parameters: `frequency`, `width`, `csg`, `mix`, `width_type`.
- `MPVGateFilter()`: Parameters: `level_in`, `mode`, `range`, `threshold`, `ratio`, `attack`, `release`, `makeup`, `knee`, `detection`, `link`.

### VLC Audio Filters
(from `av_play.vlc_audio_filter`)
- `VLCEqualizerFilter()`: Parameters: `preamp`, `band_60`, `band_170`, `band_310`, `band_600`, `band_1000`, `band_3000`, `band_6000`, `band_12000`, `band_14000`, `band_16000`.

---

## 8. Playlist Management API

### `PlaylistEntry`
A `dataclass` representing one item in a playlist.
- `location: str` (Required)
- `title: Optional[str]`
- `duration: Optional[int]` (in seconds)
- `artist: Optional[str]`
- `album: Optional[str]`
- `metadata: Optional[Dict[str, Any]]`

### `Playlist`
Represents a list of `PlaylistEntry` objects.
- `__init__(self, title: str = "New Playlist")`
- `load(self, file_path_or_url: str, format_type: PlaylistFormat = None, encoding: str = 'utf-8') -> 'Playlist'`
- `save(self, file_path: str, format_type: PlaylistFormat = None, encoding: str = 'utf-8')`
- `add_entry(self, entry: PlaylistEntry)`
- `remove_entry(self, index: int) -> PlaylistEntry | None`
- `move_entry(self, from_index: int, to_index: int) -> bool`
- `clear(self)`
- `get_entry(self, index: int) -> PlaylistEntry | None`
- `sort(self, key: Union[str, Callable], reverse: bool = False)`
- `filter(self, predicate: Callable) -> 'Playlist'`
- `remove_duplicates(self, key: str = "location") -> int`
- `filter_by_extension(self, allowed_extensions: List[str], include: bool = True) -> int`
- `merge(self, other: 'Playlist') -> 'Playlist'`
- `entries: List[PlaylistEntry]` (property)
- Provides standard list-like access: `len(playlist)`, `playlist[i]`, `for entry in playlist:`.

### `PlaylistManager`
A helper class to manage multiple named playlists.
- `create_playlist(self, name: str, title: str = None) -> Playlist`
- `get_playlist(self, name: str) -> Playlist | None`
- `remove_playlist(self, name: str) -> bool`
- `load_playlist(self, name: str, file_path_or_url: str, ...)`
- `save_playlist(self, name: str, file_path: str, ...)`
- `list_playlists(self) -> List[str]`
- `merge_playlists(self, name: str, source_playlist_names: List[str], ...)`
- `sort_playlist(self, name: str, key: Union[str, Callable], ...)`
- `filter_playlist(self, source_name: str, target_name: str, ...)`
- `remove_duplicates(self, name: str, ...)`
- `filter_by_extension(self, name: str, ...)`

---

## 9. Utility Functions

- `MediaInfo(path: str) -> music_tag.AudioFile`
  - A convenience alias for `music_tag.load_file`. Reads metadata (ID3 tags, etc.) from a media file.
  - Example: `tags = MediaInfo("song.mp3"); print(tags['artist'])`

---

## 10. License

MIT