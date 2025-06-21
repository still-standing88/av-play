import pyfmodex as fmod

from typing import Any, Dict
from pyfmodex import enums as fmod_enums

from .__AV_Common import *
from .audio_filter import AudioFilter

class FMODAudioFilter(AudioFilter):


    def __init__(self, filter_handle: str, parameters: dict[str, int | float | str], backend_additional_info: dict[Any, Any]):
        media_backend: AVMediaBackend = AVMediaBackend.AV_BACKEND_FMOD
        super().__init__(media_backend, filter_handle, parameters, backend_additional_info)


class FMODEchoFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {"delay_ms": 500.0, "feedback_percent": 50.0, "dry_level_db": 0.0, "wet_level_db": 0.0}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.ECHO,
            "fmod_param_map": {
                "delay_ms": (fmod_enums.DSP_ECHO.DELAY, float, (1.0, 5000.0, 1.0, 500.0)),
                "feedback_percent": (fmod_enums.DSP_ECHO.FEEDBACK, float, (0.0, 100.0, 0.0, 50.0)),
                "dry_level_db": (fmod_enums.DSP_ECHO.DRYLEVEL, float, (-80.0, 10.0, -80.0, 0.0)),
                "wet_level_db": (fmod_enums.DSP_ECHO.WETLEVEL, float, (-80.0, 10.0, -80.0, 0.0)),
            }}
        super().__init__("ECHO", parameters, backend_additional_info)

class FMODReverbFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {
            "decay_time_ms": 1500.0, "early_delay_ms": 7.0, "late_delay_ms": 11.0,
            "hf_reference_hz": 5000.0, "hf_decay_ratio_percent": 83.0, "diffusion_percent": 100.0,
            "density_percent": 100.0, "low_shelf_frequency_hz": 250.0, "low_shelf_gain_db": 0.0,
            "high_cut_hz": 14500.0, "early_late_mix_percent": 96.0, "wet_level_db": -8.0, "dry_level_db": 0.0,
        }
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.SFXREVERB,
            "fmod_param_map": {
                "decay_time_ms": (fmod_enums.DSP_SFXREVERB.DECAYTIME, float, (100.0, 20000.0, 100.0, 1500.0)),
                "early_delay_ms": (fmod_enums.DSP_SFXREVERB.EARLYDELAY, float, (0.0, 300.0, 0.0, 7.0)),
                "late_delay_ms": (fmod_enums.DSP_SFXREVERB.LATEDELAY, float, (0.0, 100.0, 0.0, 11.0)),
                "hf_reference_hz": (fmod_enums.DSP_SFXREVERB.HFREFERENCE, float, (20.0, 20000.0, 20.0, 5000.0)),
                "hf_decay_ratio_percent": (fmod_enums.DSP_SFXREVERB.HFDECAYRATIO, float, (10.0, 100.0, 10.0, 83.0)),
                "diffusion_percent": (fmod_enums.DSP_SFXREVERB.DIFFUSION, float, (0.0, 100.0, 0.0, 100.0)),
                "density_percent": (fmod_enums.DSP_SFXREVERB.DENSITY, float, (0.0, 100.0, 0.0, 100.0)),
                "low_shelf_frequency_hz": (fmod_enums.DSP_SFXREVERB.LOWSHELFFREQUENCY, float, (20.0, 1000.0, 20.0, 250.0)),
                "low_shelf_gain_db": (fmod_enums.DSP_SFXREVERB.LOWSHELFGAIN, float, (-36.0, 12.0, -36.0, 0.0)),
                "high_cut_hz": (fmod_enums.DSP_SFXREVERB.HIGHCUT, float, (20.0, 20000.0, 20.0, 14500.0)),
                "early_late_mix_percent": (fmod_enums.DSP_SFXREVERB.EARLYLATEMIX, float, (0.0, 100.0, 0.0, 96.0)),
                "wet_level_db": (fmod_enums.DSP_SFXREVERB.WETLEVEL, float, (-80.0, 20.0, -80.0, -8.0)),
                "dry_level_db": (fmod_enums.DSP_SFXREVERB.DRYLEVEL, float, (-80.0, 20.0, -80.0, 0.0)),
            }}
        super().__init__("REVERB", parameters, backend_additional_info)

class FMODLowpassFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {"cutoff_frequency_hz": 5000.0, "q_factor": 1.0}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.MULTIBAND_EQ,
            "fixed_param_vals": {
                "filter_type": (fmod_enums.DSP_MULTIBAND_EQ.A_FILTER, fmod_enums.DSP_MULTIBAND_EQ_FILTER_TYPE.LOWPASS_24DB, int),
            },
            "fmod_param_map": {
                "cutoff_frequency_hz": (fmod_enums.DSP_MULTIBAND_EQ.A_FREQUENCY, float, (20.0, 22000.0, 1.0, 5000.0)),
                "q_factor": (fmod_enums.DSP_MULTIBAND_EQ.A_Q, float, (0.1, 10.0, 0.1, 1.0)),
            }}
        super().__init__("LOWPASS", parameters, backend_additional_info)

class FMODHighpassFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {"cutoff_frequency_hz": 250.0, "q_factor": 1.0}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.MULTIBAND_EQ,
            "fixed_param_vals": {
                "filter_type": (fmod_enums.DSP_MULTIBAND_EQ.A_FILTER, fmod_enums.DSP_MULTIBAND_EQ_FILTER_TYPE.HIGHPASS_24DB, int),
            },
            "fmod_param_map": {
                "cutoff_frequency_hz": (fmod_enums.DSP_MULTIBAND_EQ.A_FREQUENCY, float, (20.0, 22000.0, 1.0, 250.0)),
                "q_factor": (fmod_enums.DSP_MULTIBAND_EQ.A_Q, float, (0.1, 10.0, 0.1, 1.0)),
            }}
        super().__init__("HIGHPASS", parameters, backend_additional_info)

class FMODBandpassFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {"center_frequency_hz": 1000.0, "bandwidth_q": 1.0}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.MULTIBAND_EQ,
            "fixed_param_vals": {
                "filter_type": (fmod_enums.DSP_MULTIBAND_EQ.A_FILTER, fmod_enums.DSP_MULTIBAND_EQ_FILTER_TYPE.BANDPASS, int),
            },
            "fmod_param_map": {
                "center_frequency_hz": (fmod_enums.DSP_MULTIBAND_EQ.A_FREQUENCY, float, (20.0, 22000.0, 1.0, 1000.0)),
                "bandwidth_q": (fmod_enums.DSP_MULTIBAND_EQ.A_Q, float, (0.1, 10.0, 0.1, 1.0)),
            }}
        super().__init__("BANDPASS", parameters, backend_additional_info)

class FMODChorusFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {"mix_percent": 50.0, "rate_hz": 0.8, "depth_percent": 3.0}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.CHORUS,
            "fmod_param_map": {
                "mix_percent": (fmod_enums.DSP_CHORUS.MIX, float, (0.0, 100.0, 0.0, 50.0)),
                "rate_hz": (fmod_enums.DSP_CHORUS.RATE, float, (0.0, 20.0, 0.0, 0.8)),
                "depth_percent": (fmod_enums.DSP_CHORUS.DEPTH, float, (0.0, 100.0, 0.0, 3.0)),
            }}
        super().__init__("CHORUS", parameters, backend_additional_info)

class FMODCompressorFilter(FMODAudioFilter):
    def __init__(self):
        parameters = {
            "threshold_db": 0.0, "ratio": 2.5, "attack_ms": 20.0,
            "release_ms": 100.0, "makeup_gain_db": 0.0,
            "use_sidechain": False, "linked_channels": True,
        }
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.COMPRESSOR,
            "fmod_param_map": {
                "threshold_db": (fmod_enums.DSP_COMPRESSOR.THRESHOLD, float, (-80.0, 0.0, 1.0, 0.0)),
                "ratio": (fmod_enums.DSP_COMPRESSOR.RATIO, float, (1.0, 50.0, 0.1, 2.5)),
                "attack_ms": (fmod_enums.DSP_COMPRESSOR.ATTACK, float, (0.1, 1000.0, 0.1, 20.0)),
                "release_ms": (fmod_enums.DSP_COMPRESSOR.RELEASE, float, (10.0, 5000.0, 1.0, 100.0)),
                "makeup_gain_db": (fmod_enums.DSP_COMPRESSOR.GAINMAKEUP, float, (-30.0, 30.0, 0.1, 0.0)),
                "use_sidechain": (fmod_enums.DSP_COMPRESSOR.USESIDECHAIN, bool, (False, True, 1, False)),
                "linked_channels": (fmod_enums.DSP_COMPRESSOR.LINKED, bool, (False, True, 1, True)),
            }}
        super().__init__("COMPRESSOR", parameters, backend_additional_info)

class FMODFlangerFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {"mix_percent": 50.0, "depth_factor": 1.0, "rate_hz": 0.1}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.FLANGE,
            "fmod_param_map": {
                "mix_percent": (fmod_enums.DSP_FLANGE.MIX, float, (0.0, 100.0, 0.0, 50.0)),
                "depth_factor": (fmod_enums.DSP_FLANGE.DEPTH, float, (0.01, 1.0, 0.01, 1.0)),
                "rate_hz": (fmod_enums.DSP_FLANGE.RATE, float, (0.0, 20.0, 0.0, 0.1)),
            }}
        super().__init__("FLANGER", parameters, backend_additional_info)

class FMODDistortionFilter(FMODAudioFilter):
    def __init__(self):
        parameters:dict[str, ParameterValue] = {"level_factor": 0.5}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.DISTORTION,
            "fmod_param_map": {
                "level_factor": (fmod_enums.DSP_DISTORTION.LEVEL, float, (0.0, 1.0, 0.0, 0.5)),
            }}
        super().__init__("DISTORTION", parameters, backend_additional_info)

class FMODPitchShiftFilter(FMODAudioFilter):
    def __init__(self):
        parameters = {"pitch_scale": 1.0, "fft_size_samples": 1024}
        backend_additional_info = {
            "fmod_dsp_type": fmod_enums.DSP_TYPE.PITCHSHIFT,
            "fmod_param_map": {
                "pitch_scale": (fmod_enums.DSP_PITCHSHIFT.PITCH, float, (0.5, 2.0, 0.01, 1.0)),
                "fft_size_samples": (fmod_enums.DSP_PITCHSHIFT.FFTSIZE, float, (256, 4096, 64, 1024)),
            }}
        super().__init__("PITCH_SHIFT", parameters, backend_additional_info)