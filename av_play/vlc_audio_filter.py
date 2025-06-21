from typing import Any
from .__AV_Common import *
from .audio_filter import AudioFilter

class VLCAudioFilter(AVFilter):
    def __init__(self, filter_handle: str, parameters: dict[str, ParameterValue], backend_additional_info: dict[Any, Any]):
        super().__init__(AVFilterType.AV_TYPE_AUDIO, AVMediaBackend.AV_BACKEND_VLC, filter_handle, parameters, backend_additional_info)
        self._validate_parameters()
    
    def _validate_parameters(self):
        vlc_param_map = self.info.get("vlc_param_map", {})
        current_params = self.get_parameters()
        
        for param_name, param_value in current_params.items():
            if param_name in vlc_param_map:
                vlc_param_name, param_type, param_range = vlc_param_map[param_name]
                
                if not isinstance(param_value, param_type):
                    raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_TYPE, 
                                f"Parameter {param_name} must be of type {param_type.__name__}")
                
                if param_range and param_type in [int, float]:
                    min_val, max_val = param_range[:2]
                    if not (min_val <= param_value <= max_val):
                        raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_RANGE,
                                    f"Parameter {param_name} must be between {min_val} and {max_val}")
    
    def set_parameter(self, name: str, value: ParameterValue):
        vlc_param_map = self.info.get("vlc_param_map", {})
        if name in vlc_param_map:
            vlc_param_name, param_type, param_range = vlc_param_map[name]
            
            if not isinstance(value, param_type):
                raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_TYPE,
                            f"Parameter {name} must be of type {param_type.__name__}")
            
            if param_range and param_type in [int, float]:
                min_val, max_val = param_range[:2]
                if not (min_val <= value <= max_val):
                    raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_RANGE,
                                f"Parameter {name} must be between {min_val} and {max_val}")
        
        super().set_parameter(name, value)
    
    def construct(self) -> str:
        return ""


class VLCEqualizerFilter(VLCAudioFilter):
    def __init__(self):
        vlc_param_map = {
            "preamp": ("preamp", float, (-20.0, 20.0)),
            "band_60": ("60Hz", float, (-20.0, 20.0)),
            "band_170": ("170Hz", float, (-20.0, 20.0)),
            "band_310": ("310Hz", float, (-20.0, 20.0)),
            "band_600": ("600Hz", float, (-20.0, 20.0)),
            "band_1000": ("1KHz", float, (-20.0, 20.0)),
            "band_3000": ("3KHz", float, (-20.0, 20.0)),
            "band_6000": ("6KHz", float, (-20.0, 20.0)),
            "band_12000": ("12KHz", float, (-20.0, 20.0)),
            "band_14000": ("14KHz", float, (-20.0, 20.0)),
            "band_16000": ("16KHz", float, (-20.0, 20.0))
        }
        
        parameters = {
            "preamp": 12.0,
            "band_60": 0.0,
            "band_170": 0.0,
            "band_310": 0.0,
            "band_600": 0.0,
            "band_1000": 0.0,
            "band_3000": 0.0,
            "band_6000": 0.0,
            "band_12000": 0.0,
            "band_14000": 0.0,
            "band_16000": 0.0
        }
        
        backend_info = {
            "vlc_filter_type": "equalizer",
            "vlc_param_map": vlc_param_map
        }
        
        super().__init__("Equalizer", parameters, backend_info)