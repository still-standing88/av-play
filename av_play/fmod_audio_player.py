import os
import pyfmodex as fmod

from pyfmodex import flags as fmod_flags
from pyfmodex import enums as fmod_enums
from pyfmodex.exceptions import FmodError
from pyfmodex.structobject import Structobject
from pyfmodex.structures import CREATESOUNDEXINFO

from typing import Dict, List, Callable, Any, Tuple, Union
from enum import Enum

from .fmod_audio_filter import FMODAudioFilter
from .__AV_Common import *
from .__AV_Instance import AVMediaInstance
from .__AV_Interface import AVMediaInterface
from .__AV_Player import AVPlayer

MIN_FMOD_VERSION = 0x00020108
RangeType = Union[int,float]
fmod_res = fmod_enums.RESULT
TIMEUNIT = fmod_enums.TIMEUNIT

def handle_call_err(call_func:Callable) -> Any:
    try:
        return call_func()
    except FmodError as fmod_err:
        result = fmod_err.result
        info = AVErrorInfo.UNKNOWN_ERROR
        if result == fmod_res.FILE_NOTFOUND:
            info = AVErrorInfo.FILE_NOTFOUND
        elif result == fmod_res.FORMAT:
            info = AVErrorInfo.UNSUPPORTED_FORMAT
        elif result == fmod_res.INVALID_HANDLE or result == fmod_res.CHANNEL_STOLEN:
            info = AVErrorInfo.INVALID_HANDLE
        elif result in [fmod_res.HTTP, fmod_res.HTTP_ACCESS, fmod_res.HTTP_PROXY_AUTH, fmod_res.HTTP_SERVER_ERROR, fmod_res.HTTP_TIMEOUT]:
            info = AVErrorInfo.HTTP_ERROR
        elif result in [fmod_res.NET_CONNECT, fmod_res.NET_SOCKET_ERROR, fmod_res.NET_URL]:
            info = AVErrorInfo.NET_ERROR
        elif result == fmod_res.UNINITIALIZED:
            info = AVErrorInfo.UNINITIALIZED
        else:
            info = AVErrorInfo.UNKNOWN_ERROR
        raise AVError(info, f"Details: {fmod_err.result}")
    except Exception as e:
        raise AVError(AVErrorInfo.UNKNOWN_ERROR, f"unknown error: {str(e)}")


def safe_assert(condition) -> bool:
    """Custom assert that returns True/False instead of raising AssertionError"""
    return bool(condition)

class AudioMediaInterface(AVMediaInterface):


    def __init__(self) -> None:
        super().__init__(AVMediaType.AV_TYPE_AUDIO, AVMediaBackend.AV_BACKEND_FMOD)
        self.__instances:Dict[int, fmod.sound.Sound] = {}
        self.__effects:Dict[int, fmod.dsp.DSP] = {}
        self.__effect_structs:Dict[int, AVFilter] = {}
        self.__instance_effects:Dict[int, List[int]] = {}
        self.__channels:Dict[int, fmod.channel.Channel] = {}
        self.__system = fmod.System()

        if self.__system.version < MIN_FMOD_VERSION:
            raise Exception(f"Error: Detected FMOD version is lower then the mimum supported version.\nMinimum version is {MIN_FMOD_VERSION}")


    def init(self, *args, **kw):
        max_channels = kw["max_channels"] if "max_channels" in kw else 64
        flags = fmod_flags.INIT_FLAGS.NORMAL | fmod_flags.INIT_FLAGS.PROFILE_ENABLE
        try:
            self.__system.init(maxchannels=max_channels, flags=flags)
            self.__system.stream_buffer_size = Structobject(size=64 * 1024, unit=fmod_enums.TIMEUNIT.RAWBYTES)
        except Exception as e:
            raise AVError(AVErrorInfo.INITIALIZATION_ERROR, f"Error initializing FMOD. {str(e)}")

    def free(self):
        for instance in list(self.__instances.keys()):
            try:
                self.release(instance)
            except Exception:
               pass

        for instance in list(self.__instance_effects.keys()):
            for effect in self.__instance_effects[instance].copy():
                try:
                    self.remove_filter(instance, effect)
                except:
                    pass

        self.__effects.clear()
        self.__instance_effects.clear()
        self.__effect_structs.clear()
        try:
            self.__system.release()
        except Exception as e:
            raise AVError(AVErrorInfo.INVALID_HANDLE)

    def load_file(self, id:int, path:str):
        try:
            self.release(id)
        except: 
            pass
        def create_instance():
            if (path is not None and path != "") and (id not in self.__instances or self.__instances[id] is None):
                self.__instances[id] = self.__system.create_stream(path, mode=fmod_flags.MODE.NONBLOCKING)

        handle_call_err(create_instance)

    def load_url(self, id:int, url:str):
        def create_instance():
            MODE = fmod_flags.MODE
            exinfo = CREATESOUNDEXINFO(filebuffersize=1024 * 16)
            self.__instances[id] = self.__system.create_sound(url, mode=MODE.CREATESTREAM | MODE.NONBLOCKING, exinfo=exinfo)

        if (url is not None and url != "") and (id not in self.__instances or self.__instances[id] is None):
            handle_call_err(create_instance)

    def release(self, id:int):
        try:
            self.stop(id)
        except:
            pass

        if id in self.__channels:
            del self.__channels[id]
            
        if id in self.__instances and self.__instances[id] is not None:
            try:
                handle_call_err(lambda: self.__instances[id].release())
            except:
                pass
            del self.__instances[id]


    def play(self, id:int):
        self.__check_handle(id)

        fmod_state = fmod_enums.OPENSTATE
        sound:fmod.sound.Sound = self.__instances[id]
        state:fmod_enums.OPENSTATE|None = None

        def create_channel(): self.__channels[id] = sound.play(paused=True)
        
        def play_channel():
            starving:bool|None = getattr(sound.open_state, "starving", None)
            if self.__channels[id] and starving is not None:
                self.__channels[id].mute = starving

                self.__channels[id].paused = False
                if id in self.__instance_effects and self.__instance_effects[id] is not None:
                    for effect in self.__instance_effects[id]:
                        self.apply_filter(id, effect, self.__effect_structs[effect])

        try:
            state = getattr(sound.open_state, "state")
            if state == fmod_state.BUFFERING or state == fmod_state.LOADING or state == fmod_state.CONNECTING:
                pass
        except Exception:
            pass

        def play_sound():
            if state == fmod_state.READY or state == fmod_state.PLAYING:
                try:
                    if id not in self.__channels or self.__channels[id] is None:
                        create_channel()
                    play_channel()
                except FmodError as fmod_err:
                    if fmod_err.result == fmod_res.INVALID_HANDLE or fmod_err.result == fmod_res.CHANNEL_STOLEN:
                        create_channel()
                    play_channel()

        handle_call_err(play_sound)

    def pause(self, id:int):
        self.__check_handle(id)

        def pause_channel():
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return
            channel.paused = True  # type: ignore

        try: handle_call_err(pause_channel)
        except: pass

    def mute(self, id:int):
        self.__check_handle(id)

        def mute_channel():
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return
            channel.mute = True  # type: ignore

        try: handle_call_err(mute_channel)
        except: pass

    def unmute(self, id:int):
        self.__check_handle(id)

        def unmute_channel():
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return
            channel.mute = False  # type: ignore

        try: handle_call_err(unmute_channel)
        except: pass

    def stop(self, id:int):
        self.__check_handle(id)

        def stop_channel():
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return
            channel.stop()  # type: ignore

        try: handle_call_err(stop_channel)
        except: pass

    def set_volume(self, id:int, offset:float):
        self.__check_handle(id)

        def set_channel_volume():
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return
            channel.volume = offset  # type: ignore

        try: handle_call_err(set_channel_volume)
        except: pass

    def set_position(self, id:int, offset:int):
        self.__check_handle(id)

        def set_channel_pos():
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return
            channel.set_position(pos=offset*1000, unit=TIMEUNIT.MS)  # type: ignore

        try: handle_call_err(set_channel_pos)
        except: pass

    def set_loop(self, id:int, loop:bool):
        sound:fmod.sound.Sound|None  = self.__check_handle(id)

        def set_loop_mode():
            MODE = fmod_flags.MODE
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(sound is not None) or not safe_assert(channel is not None):
                return
            current_pos:int = channel.get_position(unit=TIMEUNIT.MS)  # type: ignore
            sound.mode = sound.mode | MODE.LOOP_NORMAL if loop else sound.mode & ~MODE.LOOP_NORMAL | MODE.LOOP_OFF  # type: ignore
            channel.mode = channel.mode | MODE.LOOP_NORMAL if loop else channel.mode & ~MODE.LOOP_NORMAL | MODE.LOOP_OFF  # type: ignore
            sound.loop_count = -1 if loop else 0  # type: ignore
            channel.loop_count = -1 if loop else 0  # type: ignore
            if loop: channel.set_position(pos=current_pos, unit=TIMEUNIT.MS)  # type: ignore

        try: handle_call_err(set_loop_mode)
        except: pass

    def get_length(self, id:int) -> int:
        sound:fmod.sound.Sound|None = self.__check_handle(id)

        def get_media_length() -> int:
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(sound is not None) or not safe_assert(channel is not None):
                return -1
            return int(sound.get_length(ltype=TIMEUNIT.MS) /1000)  # type: ignore

        try:
            return handle_call_err(get_media_length)
        except Exception as e:
            return -1

    def get_position(self, id:int) -> int:
        self.__check_handle(id)

        def get_channel_pos() -> int:
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return -1
            return int(channel.get_position(unit=TIMEUNIT.MS) /1000)  # type: ignore

        try:
            return handle_call_err(get_channel_pos)
        except Exception as e:
            return -1

    def get_play_state(self, id:int) -> AVPlaybackState:
        fmod_state = fmod_enums.OPENSTATE
        sound:fmod.sound.Sound|None  = self.__check_handle(id)

        def get_state() -> AVPlaybackState:
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(sound is not None):
                return AVPlaybackState.AV_STATE_NOTHING
            open_state: Structobject| None = None

            try: open_state = sound.open_state  # type: ignore
            except: return AVPlaybackState.AV_STATE_NOTHING
            
            if not safe_assert(open_state is not None):
                return AVPlaybackState.AV_STATE_NOTHING
            state:fmod_enums.OPENSTATE | None = getattr(open_state, "state", None)  # type: ignore

            if channel is None and state == fmod_state.BUFFERING: return AVPlaybackState.AV_STATE_BUFFERING
            elif channel is None and (state == fmod_state.LOADING or state == fmod_state.CONNECTING): return AVPlaybackState.AV_STATE_LOADING
            elif channel is None and state == fmod_state.READY: return AVPlaybackState.AV_STATE_STOPPED

            if not safe_assert(channel is not None):
                return AVPlaybackState.AV_STATE_NOTHING
            if channel.is_playing and channel.paused: return AVPlaybackState.AV_STATE_PAUSED  # type: ignore
            elif channel.is_playing and not channel.paused: return AVPlaybackState.AV_STATE_PLAYING  # type: ignore
            else: return AVPlaybackState.AV_STATE_NOTHING

        try:
            return handle_call_err(get_state)
        except FmodError as fmod_err:
            result = fmod_err.result 
            return AVPlaybackState.AV_STATE_STOPPED if result == fmod_res.CHANNEL_STOLEN or result == fmod_res.INVALID_HANDLE else AVPlaybackState.AV_STATE_NOTHING
        except:
            return AVPlaybackState.AV_STATE_NOTHING

    def get_mute_state(self, id:int) -> AVMuteState:
        MODE = fmod_flags.MODE
        self.__check_handle(id)

        def get_mute_state() -> AVMuteState:
            channel = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return AVMuteState.AV_AUDIO_UNMUTED
            return AVMuteState.AV_AUDIO_MUTED if channel.mute else AVMuteState.AV_AUDIO_UNMUTED  # type: ignore

        try:
            return handle_call_err(get_mute_state)
        except Exception as e:
            return AVMuteState.AV_AUDIO_UNMUTED

    def get_volume(self, id:int) -> float:
        self.__check_handle(id)

        def get_channel_volume() -> float:
            channel:fmod.channel.Channel | None = self.__check_channel(id)
            if not safe_assert(channel is not None):
                return -1
            return channel.volume  # type: ignore

        try:
            return handle_call_err(get_channel_volume)
        except Exception as e:
            return -1

    def get_loop(self, id:int) -> bool:
        MODE = fmod_flags.MODE
        sound:fmod.sound.Sound|None = self.__check_handle(id)

        def get_loop_mode():
            if not safe_assert(sound is not None):
                return False
            return True if bool(sound.mode & MODE.LOOP_OFF) else False  # type: ignore

        try:
            return handle_call_err(get_loop_mode)
        except:
            return False

    def apply_filter(self, id:int, filter_id:int, filter_struct:AVFilter):
        self.__check_handle(id)
        if filter_struct is None or not isinstance(filter_struct, FMODAudioFilter):
            raise AVError(AVErrorInfo.INVALID_MEDIA_FILTER)

        if filter_id not in self.__effect_structs or self.__effect_structs[filter_id] is None:
            self.__effect_structs[filter_id] = filter_struct
        else:
            self.__effect_structs[filter_id].set_parameters(filter_struct.get_parameters())

        if id not in self.__instance_effects or self.__instance_effects[id] is None:
            self.__instance_effects[id] = []
        if filter_id not in self.__instance_effects[id]:
            self.__instance_effects[id].append(filter_id)

        def apply_effect():
            dsp_type:fmod_enums.DSP_TYPE = filter_struct.info["fmod_dsp_type"]
            dsp_obj:fmod.dsp.DSP = self.__system.create_dsp_by_type(dsp_type)
            channel:fmod.channel.Channel|None = self.__check_channel(id)

            if not safe_assert(channel is not None):
                return
            

            self.__effects[filter_id] = dsp_obj
            channel.add_dsp(0, dsp_obj)  # type: ignore

            if "fixed_param_vals" in filter_struct.info:
                for param in filter_struct.info["fixed_param_vals"]:
                    param_data:Tuple[Enum, Enum, ParameterValue] = filter_struct.info["fixed_param_vals"][param]
                    param_type, param_val, param_val_type=param_data
                    if isinstance(param_val_type, int):
                        dsp_obj.set_parameter_int(param_type, param_val)
                    elif isinstance(param_val_type, float):
                        dsp_obj.set_parameter_float(param_type, param_val)
            for param in filter_struct.get_parameters():
                self.__set_parameter_value(dsp_obj, filter_struct, param, filter_struct.get_parameters()[param])


        if filter_id not in self.__effects:
            handle_call_err(apply_effect)

    def remove_filter(self, id:int, filter_id):
        self.__check_handle(id)

        def remove_effect():
            channel:fmod.channel.Channel|None = self.__check_channel(id)
            if filter_id not in self.__effects:
                return
            dsp_obj:fmod.dsp.DSP = self.__effects[filter_id]
            

            if not safe_assert(channel is not None):

                try:
                    dsp_obj.release()
                except:
                    pass
            else:

                try:
                    channel.remove_dsp(dsp_obj)  # type: ignore
                    dsp_obj.release()
                except FmodError as fmod_err:

                    if fmod_err.result == fmod_res.INVALID_HANDLE or fmod_err.result == fmod_res.CHANNEL_STOLEN:
                        try:
                            dsp_obj.release()
                        except:
                            pass
                    else:
                        raise
            

            del self.__effects[filter_id]
            if filter_id in self.__effect_structs: 
                self.__effect_structs.pop(filter_id)
            if id in self.__instance_effects and filter_id in self.__instance_effects[id]: 
                self.__instance_effects[id].remove(filter_id)

        try:
            handle_call_err(remove_effect)
        except AVError as av_err:

            if "INVALID_HANDLE" not in str(av_err):
                raise

    def set_parameter(self, id:int, filter_id:int, parameter_name:str, value:ParameterValue):
        self.__check_handle(id)

        def set_param():
            dsp_obj:fmod.dsp.DSP = self.__check_dsp(filter_id)
            if filter_id not in self.__effect_structs or self.__effect_structs[filter_id]is None:
                raise AVError(AVErrorInfo.INVALID_HANDLE)
            self.__set_parameter_value(dsp_obj, self.__effect_structs[filter_id], parameter_name, value)

        handle_call_err(set_param)

    def get_parameter(self, id:int, filter_id:int, parameter_name:str) -> ParameterValue |None:
        self.__check_handle(id)

        def get_param():
            if filter_id not in self.__effect_structs or self.__effect_structs[filter_id]is None:
                raise AVError(AVErrorInfo.INVALID_HANDLE)
            return self.__effect_structs[filter_id].get_parameters()[parameter_name]

        return handle_call_err(get_param)

    def __check_handle(self, id:int) -> fmod.sound.Sound | None:
        if id not in self.__instances or self.__instances[id] is None or not self.__instances[id]._ptr:
            raise AVError(AVErrorInfo.INVALID_HANDLE)
        return self.__instances[id]

    def __check_channel(self, id:int) -> fmod.channel.Channel | None:
        if id not in self.__channels or self.__channels[id] is None:
            return None
        return self.__channels[id]

    def __check_dsp(self, dsp_id:int) -> fmod.dsp.DSP:
        if dsp_id not in self.__effects or self.__effects[dsp_id] is None:
            raise AVError(AVErrorInfo.INVALID_HANDLE)
        return self.__effects[dsp_id]

    def __set_parameter_value(self, dsp_obj:fmod.dsp.DSP, effect_struct:AVFilter, parameter_name:str, parameter_value:ParameterValue):
        if parameter_name not in effect_struct.info["fmod_param_map"]:
            raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER)

        param_info:Tuple[Enum, type, Tuple[RangeType, RangeType, RangeType, RangeType]] = effect_struct.info["fmod_param_map"][parameter_name]
        dsp_param_type:Enum = param_info[0]
        param_type:type = param_info[1]
        param_range:Tuple[RangeType, RangeType, RangeType, RangeType] = param_info[2]
        param_val:ParameterValue = parameter_value


        if not isinstance(param_val, param_type):
            raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_TYPE)


        if isinstance(param_val, (float, int)) and not (param_val >= param_range[0] and param_val <= param_range[1]):
            raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_RANGE)

        if param_type is int:
            dsp_obj.set_parameter_int(dsp_param_type, param_val)
            effect_struct.set_parameter(parameter_name, param_val)
        elif param_type is float:
            dsp_obj.set_parameter_float(dsp_param_type, param_val)
            effect_struct.set_parameter(parameter_name, param_val)
        elif param_type is bool:
            dsp_obj.set_parameter_bool(dsp_param_type, param_val)
            effect_struct.set_parameter(parameter_name, param_val)
        else:
            raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_VALUE)


    def get_devices(self) -> int:
        def get_device_count() -> int:
            return self.__system.num_drivers

        return handle_call_err(get_device_count)

    def get_device_info(self, index:int) -> AVDevice:
        def device_info() -> AVDevice:
            device:Structobject = self.__system.get_driver_info(index)
            name:str = getattr(device, "name", "none")
            return AVDevice(AVMediaBackend.AV_BACKEND_FMOD, name)

        return handle_call_err(device_info)

    def set_device(self, index:int):
        def set_device_index():
            self.__system.driver = index

        handle_call_err(set_device_index)

    def get_current_device(self) -> int:
        def get_device() -> int:
            return self.__system.driver

        return handle_call_err(get_device)


class FMODAudioPlayer(AVPlayer):


    def __init__(self) -> None:
        self.__media_type = AVMediaType.AV_TYPE_AUDIO
        self.__media_backend = AVMediaBackend.AV_BACKEND_FMOD
        self._controler:AudioMediaInterface = AudioMediaInterface()
        super().__init__(self.__media_type, self.__media_backend, self.__controler)

    def init(self, *args, **kw):
        self._controler.init()

    def release(self):
        super().release()
        self._controler.free()

