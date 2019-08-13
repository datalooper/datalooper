from consts import *
from cltrack import ClTrack
from dltrack import DlTrack
from track import Track
import Live
import math
from scene import Scene
from clip import Clip
from mute import Mute

class Actions:

    def __init__(self, parent, tracks, song, state):
        self.tracks = tracks
        self.state = state
        self.song = song
        self.__parent = parent
        self.timerCounter = 0
        self.tempo_change_timer = Live.Base.Timer(callback=self.execute_tempo_change, interval=1, repeat=True)
        self.quantize_timer = Live.Base.Timer(callback=self.on_quantize_changed_timer_callback, interval=1, repeat=False)
        # self.song.add_tempo_listener(self.on_tempo_change)
        self.song.add_current_song_time_listener(self.after_jump)
        # self.timer = Live.Base.Timer(callback=self.on_tempo_change_callback, interval=1, repeat=False)
        self.jumpTimer = Live.Base.Timer(callback=self.on_jump_callback, interval=1, repeat=False)

        self.scenes = []
        self.clips = []
        self.mutes = []
        self.song.add_scenes_listener(self.on_scene_change)
        self.lastQuantization = -1

    ##### HELPER FUNCTIONS #####

    @staticmethod
    def get_looper_type(type):
        types = {
            0: DlTrack,
            1: ClTrack,
            2: Track
        }
        return types.get(type)

    def update_tracks(self, tracks):
        # self.__parent.send_message("updating tracks")
        self.tracks = tracks

    @staticmethod
    def get_track_num(data):
        return data.instance * (NUM_TRACKS * NUM_BANKS) + (data.bank * NUM_TRACKS) + data.looper_num

    def get_track_num_str(self, data):
        return str(self.get_track_num(data))

    def call_method_on_tracks(self, track_num, track_type, method_name, *args):
        tracks = self.tracks.get(str(track_num))
        if tracks is not None:
            for track in tracks:
                if isinstance(track, self.get_looper_type(track_type)):
                    # self.__parent.send_message("calling method " + method_name + " on track name: " + track.track.name + " track num: " + str(track.trackNum))
                    getattr(track, method_name)(*args)

    def call_method_on_all_tracks(self, track_type, method_name, *args):
        for tracks in self.tracks.values():
            for track in tracks:
                if isinstance(track, self.get_looper_type(track_type)):
                    # self.send_message("calling method" + method_name + " on track: " + track.track.name)
                    getattr(track, method_name)(*args)

    def check_uniform_state(self, state):
        for tracks in self.tracks.values():
            for track in tracks:
                # self.send_message("track " + str(track.trackNum) + " State:" + str(track.lastState))
                if track.lastState not in state:
                    return False
        return True

    def check_track_clear(self, tracks):
        if tracks is None:
            self.__parent.send_message("no tracks present")
            return True
        for track in tracks:
            if track.lastState != CLEAR_STATE:
                return False
        return True

    ##### TRACK ACTIONS #####

    def new_clip(self, data):
        self.call_method_on_tracks(data.data1-1, CLIP_TRACK, "new_clip")

    def looper_control(self, data):
        self.send_message("looper control: " + str(data.data3) + "looper type: " + str(data.data3))
        #data1 = looper #, 0 is all
        #data2 = looper action (rec, stop, undo, clear, mute, get new slot)
        #data3 = looper type (CL# or DL#)

        action = LOOPER_ACTIONS.get(data.data2)
        if data.data1 == 0:
            self.call_method_on_all_tracks(data.data3, action)
        else:
            self.call_method_on_tracks(data.data1-1, data.data3, action)

    def clip_control(self, data):
        # 0, 1, 2 || 4, 5, 6 || 8, 9, 10
        trackNum = data.data1 - 1
        sceneNum = data.data3 - 1
        self.__parent.send_message("clip control called")
        for clip in self.clips:
            if clip.trackNum == trackNum and clip.sceneNum == sceneNum:
                action = CLIP_ACTIONS.get(data.data2)
                getattr(clip, action)(data)

    def scene_control(self, data):
        self.song.scenes[data.data1-1].fire()

    def change_instance(self, data):
        self.send_message("changing instance")
        for scene in self.scenes:
            scene.remove()
            scene.buttonNum = -1
        self.scenes = []

        for clip in self.clips:
            clip.remove()
            clip.buttonNum = -1
        self.clips = []

        for tracks in self.tracks.values():
            for track in tracks:
                track.button_num = -1

        for mute in self.mutes:
            mute.remove()
            mute.buttonNum = -1
        self.mutes = []

    def request_midi_map_rebuild(self, data):
        self.send_message("midi map rebuild requested")
        self.__parent.request_rebuild_midi_map()

    def request_state(self, data):
        # data1 = buttonNum
        # data2 = command
        # data3 = data1
        # data4 = data2, etc...
        method = self.__parent.get_method(data.data2)
        if method == "scene_control":
            linkedScene = self.is_scene_linked(data.data3-1, data.data1)
            if not linkedScene:
                linkedScene = Scene(data.data3-1, data.data1, self.song, self.state, self)
                self.scenes.append(linkedScene)
            linkedScene.request_state()
        elif method == "clip_control":
            # self.send_message("requesting state on button number: " + str(data.data1) + " track #" + str(data.data3-1) + " clip #" + str(data.data5-1))
            linkedClip = self.is_clip_linked(data.data3-1, data.data5-1)
            if not linkedClip:
                linkedClip = Clip(data.data3-1, data.data5-1, data.data1, self.song, self.state, self)
                self.clips.append(linkedClip)
            linkedClip.request_state()
        elif method == "looper_control":
            self.call_method_on_tracks(data.data3-1, data.data5, "link_button", data.data1, LOOPER_ACTIONS.get(data.data4))
            # self.send_message("requesting state looper control track num:" + str(data.data3))
        elif method == "mute_control":
            # self.send_message("found mute control mute type:" + str(data.data3))
            mute = self.is_mute_linked(data.data1)
            if not mute:
                mute = Mute(self, data.data1, data.data3, data.data4, self.song, self.tracks)
                self.mutes.append(mute)
            mute.request_state()

        # # button #
        # self.__parent.send_message(data.data1)
        # # action #
        # self.__parent.send_message(data.data2)
        # # data #
        # self.__parent.send_message(data.data3)

    def is_mute_linked(self, buttonNum):
        for mute in self.mutes:
            if mute.buttonNum == buttonNum:
                return mute
        return False

    def is_clip_linked(self, trackNum, sceneNum):
        for clip in self.clips:
            if clip.trackNum == trackNum and clip.sceneNum == sceneNum:
                return clip

        return False

    def is_scene_linked(self, sceneNum, buttonNum):
        for scene in self.scenes:
            if scene.sceneNum == sceneNum and scene.buttonNum == buttonNum:
                return scene

        return False

    def get_color_array(self, color):
        if color is not None:
            blue = color & 255
            green = (color >> 8) & 255
            red = (color >> 16) & 255
            return red >> 1, 1 & red, green >> 1, 1 & green, blue >> 1, 1 & blue
        else:
            return None

    ##### BANKING ACTIONS #####

    # def update_bank(self, data):
    #     self.__parent.send_message("updating bank: " + str(data.looper_num))
    #     self.check_arm_conflicts(data)
    #     data.bank = data.looper_num
    #     if self.song.is_playing:
    #         self.__parent.send_sysex(CHANGE_BANK_COMMAND,data.looper_num, data.looper_num)
    #     self.call_method_on_bank(data, BOTH_TRACK_TYPES, "update_state", -1)
    #
    # def check_arm_conflicts(self, data):
    #     old_bank = data.bank
    #     new_bank = data.looper_num
    #     x = 0
    #     while x < 3:
    #         new_tracks = self.tracks.get(str((data.instance * NUM_TRACKS * NUM_BANKS) + (new_bank * NUM_TRACKS) + x))
    #         old_tracks = self.tracks.get(str((data.instance * NUM_TRACKS * NUM_BANKS) + (old_bank * NUM_TRACKS) + x))
    #         if old_tracks is not None:
    #             for old_track in old_tracks:
    #                 if new_tracks is not None:
    #                     for new_track in new_tracks:
    #                         if new_track.track.input_routing_type.display_name == old_track.track.input_routing_type.display_name:
    #                             old_track.track.arm = False
    #                         new_track.track.arm = True
    #         x += 1

    ##### EFFECT ALL DATALOOPER TRACKS ACTIONS #####

    def disable_quantization(self):
        if not self.song.clip_trigger_quantization_has_listener(self.on_quantize_changed):
            self.song.add_clip_trigger_quantization_listener(self.on_quantize_changed)
            self.lastQuantization = self.song.clip_trigger_quantization
            self.song.clip_trigger_quantization = Live.Song.Quantization.q_no_q

    def on_quantize_changed(self):
        self.send_message("quantization disabled")
        self.quantize_timer.start()

    def on_quantize_changed_timer_callback(self):
        self.song.remove_clip_trigger_quantization_listener(self.on_quantize_changed)
        self.call_method_on_all_tracks(CLIP_TRACK, "on_quantize_disabled")
        self.song.clip_trigger_quantization = self.lastQuantization

    def toggle_stop_start(self, data):
        self.send_message("Fade time: " + str(data.data4))
        if data.data1 == 4:
            track_type = 0
        elif data.data1 == 3:
            track_type = 1
        else:
            track_type = data.data1

        self.__parent.send_message("toggling stop/start")

        if not self.check_uniform_state([CLEAR_STATE]) and self.check_uniform_state([STOP_STATE, CLEAR_STATE]):
            self.__parent.send_message("toggling start")
            if data.data2 == 0:
                self.jump_to_next_bar()
            self.call_method_on_all_tracks(track_type, "start", data.data2)

        else:
            self.__parent.send_message("toggling stop")
            self.call_method_on_all_tracks(track_type, "stop", data.data2)
            if data.data1 == 4 or data.data1 == 3:
                self.song.stop_all_clips()

    def new_clips_on_all(self, data):
        self.call_method_on_all_tracks(data, CLIP_TRACK, "new_clip")

    def mute_control(self, data):
        for mute in self.mutes:
            if mute.mute_type is data.data1 and mute.mute_what is data.data2:
                mute.execute_mute()

    # def execute_mute(self, mute_type, track):
    #     # mute = 0
    #     # unmute = 1
    #     # toggle = 2
    #     self.send_message("mute requested on :" + str(track.name) + " mute type:" + str(mute_type))
    #     if mute_type is 0:
    #         self.state.muted_tracks.append(track)
    #         track.mute = True
    #     elif mute_type is 1:
    #         if track in self.state.muted_tracks:
    #             self.state.muted_tracks.remove(track)
    #         track.mute = False
    #     elif mute_type is 2:
    #         if track in self.state.muted_tracks:
    #             self.state.muted_tracks.remove(track)
    #             track.mute = False
    #         else:
    #             track.mute = True
    #             self.state.muted_tracks.append(track)

    ##### EFFECT ENTIRE SESSION #####

    def on_scene_change(self):
        self.__parent.send_message("scene changed")
        for x, scene in enumerate(self.scenes):
            scene.init_listener()

    def move_session_highlight(self, data):
        self.__parent.send_message("moving session highlight:" + str(data.data1))
        for clip in self.clips:
            clip.remove()
        if data.data1 == 0 and self.state.sceneOffset > 0:
            self.state.sceneOffset -= 1
        elif data.data1 == 1:
            self.state.sceneOffset += 1
        elif data.data1 == 2 and self.state.trackOffset > 0 :
            self.state.trackOffset -= 1
        elif data.data1 == 3:
            self.state.trackOffset += 1
        for clip in self.clips:
            clip.init_listener()
            clip.update_color()
        self.__parent._set_session_highlight(self.state.trackOffset, self.state.sceneOffset, 3, 3, False)

    def stop_all_playing_clips(self, data):
        self.song.stop_all_clips()
        self.stop_all(data)

    # def mute_all_tracks_playing_clips(self, data):
    #     if data.data1 == OFF:
    #         self.ex_mute_all_tracks_playing_clips()
    #
    #     elif data.data1 == ON:
    #         self.unmute_all_tracks_playing_clips()
    #
    #     elif data.data1 == TOGGLE:
    #         if len(self.state.muted_tracks) == 0:
    #             self.ex_mute_all_tracks_playing_clips()
    #         else:
    #             self.unmute_all_tracks_playing_clips()
    #
    # def ex_mute_all_tracks_playing_clips(self):
    #     for track in self.song.tracks:
    #         if track.playing_slot_index != -1:
    #             self.state.muted_tracks.append(track)
    #             track.mute = 1
    #
    # def unmute_all_tracks_playing_clips(self):
    #     for track in self.state.muted_tracks:
    #         track.mute = 0
    #         self.state.muted_tracks = []

    def create_scene(self, data):
        self.song.create_scene(-1)

    def metronome_control(self, data):
        if data.data1 is 0:
            self.song.metronome = 0
        elif data.data1 is 1:
            self.song.metronome = 1
        elif data.data1 is 2:
            self.song.metronome = not self.state.metro
            self.state.metro = not self.state.metro

    def transport_control(self, data):
        if data.data1 is 0:
            self.song.stop_playing()
        elif data.data1 is 1:
            self.song.start_playing()
        elif data.data1 is 2:
            if self.song.is_playing:
                self.song.stop_playing()
            else:
                self.song.start_playing()

    def tap_tempo(self, data):
        self.song.tap_tempo()
        if data.data1:
            self.send_message(str(self.state.tap_tempo_counter))
            if self.state.tap_tempo_counter is 0:
                self.state.metro = self.song.metronome
                self.state.ignoreMetroCallback = True
                self.song.metronome = 0
            if self.state.tap_tempo_counter >= data.data2:
                self.state.restore_metro()
            elif self.state.metro is not False:
                self.state.tap_tempo_counter += 1

    def jump_to_next_bar(self):
        self.send_message("jumping to next bar")
        self.state.was_recording = self.song.record_mode
        self.song.record_mode = 0
        time = int(self.song.current_song_time) + (self.song.signature_denominator - (
                int(self.song.current_song_time) % self.song.signature_denominator))
        self.state.bpm = self.song.tempo
        self.send_message("song time: " + str(time))
        self.state.req_tempo_change = True
        self.song.current_song_time = time - ((self.state.bpm / 60000) * 200)
        self.song.tempo = self.state.bpm

        ## 100 ms ; 100 beats per minute ; 100/60000 beats per ms
        self.send_message("trying playing queued looper " + str(self.state.queued))

    def after_jump(self):
        self.jumpTimer.start()

    def on_jump_callback(self):
        if self.state.req_tempo_change:
            self.song.record_mode = self.state.was_recording
            if self.state.queued is not False:
                self.state.queued.request_control(MASTER_CONTROL)
                self.state.queued = False
        self.state.req_tempo_change = False

    def change_mode(self, data=False):
        if not data:
            mode = LOOPER_MODE
        else:
            mode = data.data1
        self.state.change_mode(self.__parent, mode)
        self.call_method_on_all_tracks(BOTH_TRACK_TYPES,"change_mode")
        self.__parent.send_message("mode change to: " + str(mode))

    def send_sysex(self, *data):
        self.__parent.send_sysex(*data)

    def execute_tempo_change(self):
    # kills timer after 50ms just in case it wants to run forever for some reason
        self.timerCounter += 1
        if self.song.tempo != self.state.bpm:
            self.song.tempo = self.state.bpm
            self.tempo_change_timer.stop()
        elif self.timerCounter > 50:
            self.tempo_change_timer.stop()

    def send_message(self, m):
        self.__parent.send_message(m)
