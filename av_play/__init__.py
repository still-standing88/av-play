import os

from .media_info import MediaInfo
from .playlist import PlaylistManager, PlaylistParser, Playlist, PlaylistFormat
from .__AV_Common import *
from .__AV_Instance import AVMediaInstance
from .__utils import find_lib_path

use_fmod = os.environ.get("USE_FMOD", None)
use_mpv = os.environ.get("USE_MPV", None)
use_vlc = os.environ.get("USE_VLC", None)
fmod_lib_path = os.environ.get("FMOD_LIB_PATH", None)
mpv_lib_path = os.environ.get("MPV_LIB_PATH", None)
vlc_lib_path = os.environ.get("VLC_LIB_PATH", None)

if use_fmod:
    if os.path.exists(fmod_lib_path): # type: ignore
        os.environ["PYFMODEX_DLL_PATH"] = os.path.abspath(find_lib_path(fmod_lib_path, "fmod")) # type: ignore

    try:
        from .fmod_audio_player import FMODAudioPlayer
        from .fmod_audio_filter import (FMODAudioFilter, FMODBandpassFilter, FMODChorusFilter, FMODCompressorFilter,
                                        FMODDistortionFilter, FMODEchoFilter, FMODFlangerFilter,
                                        FMODLowpassFilter, FMODHighpassFilter, FMODPitchShiftFilter, FMODReverbFilter
                                        )
        AudioPlayer = FMODAudioPlayer
    except Exception as e:
        raise RuntimeError(f"Error initializing FMOD.\nDetails: {str(e)}")

if use_mpv:
    if os.path.exists(mpv_lib_path): # type: ignore
        os.environ["PATH"] += os.path.abspath(mpv_lib_path)+os.pathsep # type: ignore
    try:
        from .mpv_video_player import MPVVideoPlayer
        from .mpv_audio_filter import (MPVAudioFilter, MPVBandPassFilter, MPVChorusFilter, MPVCompressorFilter,
                                       MPVEchoFilter, MPVFlangerFilter, MPVGateFilter, MPVHighPassFilter,
                                       MPVLimiterFilter, MPVLowPassFilter, MPVPitchShiftFilter
                                       )
        VideoPlayer = MPVVideoPlayer
    except Exception as e:
        raise RuntimeError(f"Error initializing MPV.\nDetails: {str(e)}")

if use_vlc:
    if os.path.exists(vlc_lib_path): # type: ignore
        os.environ["PATH"] += os.path.abspath(vlc_lib_path)+os.pathsep # type: ignore
    try:
        from .vlc_video_player import VLCVideoPlayer
        from .vlc_audio_filter import (VLCAudioFilter, VLCEqualizerFilter)
        VideoPlayer = VLCVideoPlayer
    except Exception as e:
        raise RuntimeError(f"Error initializing VLC.\nDetails: {str(e)}")


if not use_fmod and not use_mpv and not use_vlc:
    raise Exception(
        "No media backend is initialized or has been detected.\n"
        "Define either of: USE_FMOD = 1 or USE_MPV = 1\n"
        "in the environment. Then set the appropriate paths:\n"
        "FMOD_LIB_PATH or MPV_LIB_PATH\n"
        "Example using FMOD:\n"
        "os.environ[\"USE_FMOD\"] = \"1\"\n"
        "os.environ[\"PATH\"] = \"./lib/\""
    )

