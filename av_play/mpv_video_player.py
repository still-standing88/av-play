import mpv
import os
from typing import Dict, Any, Union, List, Callable
from .__AV_Common import *
from .__AV_Instance import AVMediaInstance
from .__AV_Interface import AVMediaInterface
from .__AV_Player import AVPlayer
from .mpv_audio_filter import MPVAudioFilter

def handle_mpv_error(call_func: Callable) -> Any:
    try:
        return call_func()
    except mpv.PropertyUnavailableError as e:
        raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER, f"Property unavailable: {str(e)}")
    except AttributeError as e:
        if "mpv property does not exist" in str(e) or "does not exist" in str(e):
            raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER, f"Property not available: {str(e)}")
        raise AVError(AVErrorInfo.UNKNOWN_ERROR, f"Attribute error: {str(e)}")
    except mpv.ShutdownError:
        raise AVError(AVErrorInfo.INVALID_HANDLE, "MPV core has been shutdown")
    except RuntimeError as e:
        if "loading failed" in str(e).lower():
            raise AVError(AVErrorInfo.FILE_NOTFOUND, f"File loading failed: {str(e)}")
        raise AVError(AVErrorInfo.UNKNOWN_ERROR, f"Runtime error: {str(e)}")
    except SystemError as e:
        raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER, f"Command error: {str(e)}")
    except TypeError as e:
        raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_TYPE, f"Type error: {str(e)}")
    except ValueError as e:
        raise AVError(AVErrorInfo.INVALID_FILTER_PARAMETER_VALUE, f"Value error: {str(e)}")
    except Exception as e:
        raise AVError(AVErrorInfo.UNKNOWN_ERROR, f"Unknown error: {str(e)}")

class MPVMediaInterface(AVMediaInterface):
    
    def __init__(self) -> None:
        super().__init__(AVMediaType.AV_TYPE_VIDEO, AVMediaBackend.AV_BACKEND_MPV)
        self.__instances:dict[int, str] = {}
        self.__mpv: mpv.MPV | None = None
        self.__current_id: int | None = None
        self.__applied_filters: Dict[int, MPVAudioFilter] = {}
        self.__is_initialized = False
        self.__stopped = False
        self.__end_reached = False

    def init(self, *args, **kw):
        try:
            config = kw.get("config", {})
            window = kw.get("window", None)
            
            if window is not None:
                config['wid'] = str(int(window))
            
            config.setdefault('ytdl', True)
            config.setdefault('input_default_bindings', True)
            
            self.__mpv = mpv.MPV(**config)
            
            ytdl_path = kw.get("ytdl_path", None)
            if ytdl_path:
                def set_ytdl_path():
                    assert self.__mpv is not None
                    self.__mpv.script_opts["ytdl_hook-ytdl_path"] = ytdl_path
                handle_mpv_error(set_ytdl_path)
            
            self.__is_initialized = True
            self.__stopped = False
            self.__end_reached = False
            
        except Exception as e:
            raise AVError(AVErrorInfo.INITIALIZATION_ERROR, f"Failed to initialize MPV: {str(e)}")

    def free(self):
        if self.__mpv is not None:
            try:
                if not self.__mpv.core_shutdown:
                    self.__mpv.terminate()
                self.__mpv = None
                self.__current_id = None
                self.__applied_filters.clear()
                self.__is_initialized = False
                self.__stopped = False
                self.__end_reached = False
            except Exception:
                pass

    def _check_initialized(self):
        if not self.__is_initialized or self.__mpv is None:
            raise AVError(AVErrorInfo.UNINITIALIZED, "MPV not initialized")
        if self.__mpv.core_shutdown:
            raise AVError(AVErrorInfo.INVALID_HANDLE, "MPV core has been shutdown")

    def _check_instance(self, id: int):
        self._check_initialized()
        if self.__current_id != id:
            raise AVError(AVErrorInfo.INVALID_HANDLE, f"Invalid instance ID: {id}")

    def get_mpv_instance(self):
        self._check_initialized()
        return self.__mpv

    def load_file(self, id: int, path: str):
        self._check_initialized()

        def loadfile():
            assert self.__mpv is not None
            self.__mpv.command("loadfile", path)
        
        if path and is_path(path) and os.path.exists(path):
            self.__current_id = id
            self.__instances[id] = path
            self.__stopped = False
            self.__end_reached = False
            self._load_subtitles(path)
            handle_mpv_error(loadfile)

    def load_url(self, id: int, url: str):
        self._check_initialized()
        
        def loadurl():
            assert self.__mpv is not None
            self.__mpv.command("loadfile", url)
        
        if url and is_url(url):
            self.__current_id = id
            self.__instances[id] = url
            self.__stopped = False
            self.__end_reached = False
            handle_mpv_error(loadurl)

    def _load_subtitles(self, path: str):
        subtitle_formats = ["idx", "sub", "srt", "rt", "ssa", "ass", "mks", "vtt", "sup", "scc", "smi", "lrc", "pgs"]
        dir_path = os.path.dirname(path)
        filename = os.path.splitext(os.path.basename(path))[0]
        
        for format in subtitle_formats:
            subtitle_path = os.path.join(dir_path, f"{filename}.{format}")
            if os.path.exists(subtitle_path):
                def add_subtitle():
                    assert self.__mpv is not None
                    self.__mpv.sub_add(subtitle_path)
                handle_mpv_error(add_subtitle)
                break

    def release(self, id: int):
        if self.__current_id == id:
            self._check_initialized()
            
            def stop():
                assert self.__mpv is not None
                self.__mpv.stop()
            handle_mpv_error(stop)
            self.__current_id = None
            self.__applied_filters.clear()
            self.__stopped = True
            self.__end_reached = False

    def play(self, id: int):
        self._check_instance(id)
        
        def resume():
            assert self.__mpv is not None
            if self.__end_reached or self.__mpv.time_pos is None:
                self.__mpv.command("loadfile", self.__instances[id])
                self.__end_reached = False
                self.__stopped = False
            self.__mpv.pause = False
        
        self.__stopped = False
        handle_mpv_error(resume)

    def pause(self, id: int):
        self._check_instance(id)
        
        def pause_play():
            assert self.__mpv is not None
            self.__mpv.pause = True
        handle_mpv_error(pause_play)

    def mute(self, id: int):
        self._check_instance(id)
        
        def toggle_mute():
            assert self.__mpv is not None
            self.__mpv.mute = not self.__mpv.mute
        handle_mpv_error(toggle_mute)

    def unmute(self, id: int):
        self._check_instance(id)
        
        def unmute_audio():
            assert self.__mpv is not None
            self.__mpv.mute = False
        handle_mpv_error(unmute_audio)

    def stop(self, id: int):
        self._check_instance(id)
        
        def halt():
            assert self.__mpv is not None
            self.__mpv.stop()
        
        handle_mpv_error(halt)
        self.__stopped = True
        self.__end_reached = False

    def set_volume(self, id: int, offset: float):
        self._check_instance(id)
        
        def set_vol():
            assert self.__mpv is not None
            self.__mpv.volume = offset
        handle_mpv_error(set_vol)

    def set_position(self, id: int, offset: int):
        self._check_instance(id)
        
        def seek():
            assert self.__mpv is not None
            self.__mpv.seek(offset, "absolute")
        handle_mpv_error(seek)

    def set_loop(self, id: int, loop: bool):
        self._check_instance(id)
        loop_value = "inf" if loop else "no"
        
        def set_loop_mode():
            assert self.__mpv is not None
            self.__mpv.loop = loop_value
        handle_mpv_error(set_loop_mode)

    def get_length(self, id: int) -> int:
        self._check_instance(id)
        
        def get_duration():
            assert self.__mpv is not None
            return self.__mpv.duration
        duration = handle_mpv_error(get_duration)
        return int(duration) if duration is not None else 0

    def get_position(self, id: int) -> int:
        self._check_instance(id)
        
        def get_time():
            assert self.__mpv is not None
            return self.__mpv.time_pos
        pos = handle_mpv_error(get_time)
        return int(pos) if pos is not None else 0

    def get_play_state(self, id: int) -> AVPlaybackState:
        self._check_instance(id)
        try:
            def get_pause():
                assert self.__mpv is not None
                return self.__mpv.pause
            def get_time_pos():
                assert self.__mpv is not None
                return self.__mpv.time_pos
            def get_duration():
                assert self.__mpv is not None
                return self.__mpv.duration
            
            if self.__stopped:
                return AVPlaybackState.AV_STATE_STOPPED
            
            is_paused = handle_mpv_error(get_pause)
            time_pos = handle_mpv_error(get_time_pos)
            duration = handle_mpv_error(get_duration)
            
            if duration is not None and time_pos is not None:
                if time_pos >= duration - 0.1:
                    self.__end_reached = True
                    return AVPlaybackState.AV_STATE_NOTHING
            elif time_pos is None and duration is not None:
                self.__end_reached = True
                return AVPlaybackState.AV_STATE_NOTHING
            
            if is_paused:
                return AVPlaybackState.AV_STATE_PAUSED
            else:
                return AVPlaybackState.AV_STATE_PLAYING
                
        except AVError:
            return AVPlaybackState.AV_STATE_NOTHING

    def get_mute_state(self, id: int) -> AVMuteState:
        self._check_instance(id)
        
        def get_mute():
            assert self.__mpv is not None
            return self.__mpv.mute
        muted = handle_mpv_error(get_mute)
        return AVMuteState.AV_AUDIO_MUTED if muted else AVMuteState.AV_AUDIO_UNMUTED

    def get_volume(self, id: int) -> float:
        self._check_instance(id)
        
        def get_vol():
            assert self.__mpv is not None
            return self.__mpv.volume
        volume = handle_mpv_error(get_vol)
        return float(volume) if volume is not None else 0.0

    def get_loop(self, id: int) -> bool:
        self._check_instance(id)
        
        def get_loop_state():
            assert self.__mpv is not None
            return self.__mpv.loop
        loop_val = handle_mpv_error(get_loop_state)
        return loop_val == "inf" if loop_val is not None else False

    def _rebuild_filter_chain(self):
        filter_strings = []
        
        for filter_obj in self.__applied_filters.values():
            filter_string = filter_obj.construct()
            if filter_string:
                filter_strings.append(filter_string)
        
        return ",".join(filter_strings) if filter_strings else ""

    def apply_filter(self, id: int, filter_id: int, filter_struct: AVFilter):
        self._check_instance(id)
        if not isinstance(filter_struct, MPVAudioFilter):
            raise AVError(AVErrorInfo.INVALID_MEDIA_FILTER, "Filter must be MPVAudioFilter")
        
        self.__applied_filters[filter_id] = filter_struct
        
        filter_chain = self._rebuild_filter_chain()
        
        def set_af_chain():
            assert self.__mpv is not None
            self.__mpv.af = filter_chain
        
        handle_mpv_error(set_af_chain)

    def remove_filter(self, id: int, filter_id: int):
        self._check_instance(id)
        if filter_id in self.__applied_filters:
            del self.__applied_filters[filter_id]
            
            filter_chain = self._rebuild_filter_chain()
            
            def set_af_chain():
                assert self.__mpv is not None
                self.__mpv.af = filter_chain
            
            handle_mpv_error(set_af_chain)

    def set_parameter(self, id: int, filter_id: int, parameter_name: str, value: ParameterValue):
        self._check_instance(id)
        if filter_id in self.__applied_filters:
            filter_struct = self.__applied_filters[filter_id]
            filter_struct.set_parameter(parameter_name, value)
            
            filter_chain = self._rebuild_filter_chain()
            
            def set_af_chain():
                assert self.__mpv is not None
                self.__mpv.af = filter_chain
            
            handle_mpv_error(set_af_chain)

    def get_parameter(self, id: int, filter_id: int, parameter_name: str) -> ParameterValue | None:
        self._check_instance(id)
        if filter_id in self.__applied_filters:
            return self.__applied_filters[filter_id].get_parameter(parameter_name)
        return None

    def get_devices(self) -> int:
        self._check_initialized()
        
        def get_device_list():
            assert self.__mpv is not None
            return self.__mpv.audio_device_list
        audio_devices = handle_mpv_error(get_device_list) or []
        return len(audio_devices)

    def get_device_info(self, index: int) -> AVDevice:
        self._check_initialized()
        
        def get_device_list():
            assert self.__mpv is not None
            return self.__mpv.audio_device_list
        audio_devices = handle_mpv_error(get_device_list) or []
        if 0 <= index < len(audio_devices):
            device = audio_devices[index]
            return AVDevice(AVMediaBackend.AV_BACKEND_MPV, device.get('description', device.get('name', 'Unknown')))
        raise IndexError("Device index out of range")

    def set_device(self, index: int):
        self._check_initialized()
        
        def get_device_list():
            assert self.__mpv is not None
            return self.__mpv.audio_device_list
        def set_audio_device(device_name):
            assert self.__mpv is not None
            self.__mpv.audio_device = device_name
        audio_devices = handle_mpv_error(get_device_list) or []
        if 0 <= index < len(audio_devices):
            device_name = audio_devices[index]['name']
            handle_mpv_error(lambda: set_audio_device(device_name))
        else:
            raise IndexError("Device index out of range")

    def get_current_device(self) -> int:
        self._check_initialized()
        
        def get_audio_device():
            assert self.__mpv is not None
            return self.__mpv.audio_device
        def get_device_list():
            assert self.__mpv is not None
            return self.__mpv.audio_device_list
        current_device = handle_mpv_error(get_audio_device)
        audio_devices = handle_mpv_error(get_device_list) or []
        
        for i, device in enumerate(audio_devices):
            if device['name'] == current_device:
                return i
        return 0


class MPVVideoPlayer(AVPlayer):
    
    def __init__(self) -> None:
        self.__mpv_interface:MPVMediaInterface = MPVMediaInterface()
        super().__init__(AVMediaType.AV_TYPE_VIDEO, AVMediaBackend.AV_BACKEND_MPV, self.__mpv_interface)

    def init(self, *args, **kw):
        self._controler.init(*args, **kw)

    def release(self):
        if self._primary_instance is not None:
            self._primary_instance.release()
            self._primary_instance = None
        self._controler.free()

    def create_file_instance(self, file_path:str) -> AVMediaInstance:
        if self._primary_instance is None:
            self._primary_instance = AVMediaInstance(self._controler)
        self._primary_instance.load_file(file_path)
        return self._primary_instance

    def create_url_instance(self, url:str) -> AVMediaInstance:
        if self._primary_instance is None:
            self._primary_instance = AVMediaInstance(self._controler)
        self._primary_instance.load_url(url)
        return self._primary_instance

    def set_window(self, window):
        def set_wid():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                mpv_instance._set_property("wid", str(int(window)))
        handle_mpv_error(set_wid)

    def forward(self, offset):
        def seek_forward():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                mpv_instance.seek(+offset, reference='relative')
        handle_mpv_error(seek_forward)

    def backward(self, offset):
        def seek_backward():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                mpv_instance.seek(-offset, reference='relative')
        handle_mpv_error(seek_backward)

    def set_volume_relative(self, direction, offset):
        def adjust_volume():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                current_volume = mpv_instance.volume
                if direction == "up":
                    mpv_instance.volume = current_volume + offset
                elif direction == "down":
                    mpv_instance.volume = current_volume - offset
        handle_mpv_error(adjust_volume)


    def set_fullscreen(self, state):
        def toggle_fullscreen():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                mpv_instance.fullscreen = state
        handle_mpv_error(toggle_fullscreen)

    def get_fullscreen(self):
        def get_fs_state():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                return mpv_instance.fullscreen
            return False
        return handle_mpv_error(get_fs_state)

    def set_playback_speed(self, speed):
        def set_speed():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                mpv_instance.speed = speed
        handle_mpv_error(set_speed)

    def set_resolution(self, width, height):
        def set_res():
            mpv_instance = self.__mpv_interface.get_mpv_instance()
            if mpv_instance:
                mpv_instance.vf = f"scale={width}:{height}"
        handle_mpv_error(set_res)