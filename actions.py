from consts import *
from cltrack import ClTrack
from dltrack import DlTrack
from track import Track
import Live
import math
from scene import Scene
from clip import Clip

class Actions:

    def __init__(self, parent, tracks, song, state):
        self.tracks = tracks
        self.state = state
        self.song = song
        self.__parent = parent
        self.timerCounter = 0
        self.tempo_change_timer = Live.Base.Timer(callback=self.execute_tempo_change, interval=1, repeat=True)
        self.scenes = []
        self.clips = []
        self.song.add_scenes_listener(self.on_scene_change)


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

    def call_method_on_tracks(self, data, track_type, method_name, *args):
        tracks = self.tracks.get(str(data.data1-1))
        if tracks is not None:
            for track in tracks:
                if isinstance(track, self.get_looper_type(track_type)):
                    self.__parent.send_message("calling method on track name: " + track.track.name + " track num: " + str(track.trackNum))
                    getattr(track, method_name)(*args)

    def call_method_on_all_tracks(self, track_type, method_name, *args):
        for tracks in self.tracks.values():
            for track in tracks:
                if isinstance(track, self.get_looper_type(track_type)):
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
        self.call_method_on_tracks(data, CLIP_TRACK, "new_clip")

    def looper_control(self, data):
        self.send_message("looper control: " + str(data.data3))
        #data1 = looper #, 0 is all
        #data2 = looper action (rec, stop, undo, clear, mute, get new slot)
        #data4 = looper type (CL# or DL#)

        if data.data1 == 0:
            self.call_method_on_all_tracks(data.data3, LOOPER_ACTIONS.get(data.data2))
        else:
            self.call_method_on_tracks(data, data.data3, LOOPER_ACTIONS.get(data.data2))

    def clip_control(self, data):
        # 0, 1, 2 || 4, 5, 6 || 8, 9, 10
        trackNum = data.data1 - 1
        sceneNum = data.data4 - 1

        if self.state.mode == CLIP_LAUNCH_MODE:
            trackNum += self.state.trackOffset
            sceneNum += self.state.sceneOffset

        for clip in self.clips:
            if clip.trackNum == trackNum and clip.sceneNum == sceneNum:
                action = CLIP_ACTIONS.get(data.data2)
                getattr(clip, action)(data)

    def scene_control(self, data):
        self.song.scenes[data.data1-1].fire()

    def request_state(self, data):
        method = self.__parent.get_method(data.data2)
        if method == "scene_control":
            linkedScene = self.is_scene_linked(data.data3-1, data.data1)
            if not linkedScene:
                newScene = Scene(data.data3-1, data.data1, self.song, self.state, self)
                self.scenes.append(newScene)
                newScene.request_state()
            elif isinstance(linkedScene, Scene):
                linkedScene.request_state()
        elif method == "clip_control":
            linkedClip = self.is_clip_linked(data.data3-1, data.data4)
            if not linkedClip:
                newClip = Clip(data.data3-1, data.data6-1, data.data1, self.song, self.state, self)
                self.clips.append(newClip)
            elif isinstance(linkedClip, Clip):
                linkedClip.request_state()

        # # button #
        # self.__parent.send_message(data.data1)
        # # action #
        # self.__parent.send_message(data.data2)
        # # data #
        # self.__parent.send_message(data.data3)

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

    def toggle_stop_start(self, data):
        self.send_message("Fade time: " + data.data4)
        if data.data1 == 4:
            track_type = 0
        elif data.data1 == 3:
            track_type = 1
        else:
            track_type = data.data1

        self.__parent.send_message("toggling stop/start")

        if not self.check_uniform_state([CLEAR_STATE]) and self.check_uniform_state([STOP_STATE, CLEAR_STATE]):
            self.__parent.send_message("toggling start")
            self.call_method_on_all_tracks(track_type, "start", data.data2)
            if data.data2 == 0:
                self.jump_to_next_bar(False)
        else:
            self.__parent.send_message("toggling stop")
            self.call_method_on_all_tracks(track_type, "stop", data.data2)
            if data.data1 == 4 or data.data1 == 3:
                self.song.stop_all_clips()

    def new_clips_on_all(self, data):
        self.call_method_on_all_tracks(data, CLIP_TRACK, "new_clip")

    def mute_control(self, data):
        mute_type = data.data1
        mute_what = data.data2
        if mute_what == 0:
            for track in self.song.tracks:
                if track.playing_slot_index is not -1 and track.clip_slots[track.playing_slot_index].is_playing:
                    self.execute_mute(mute_type, track)
        elif mute_what == 1:
            for track in self.song.tracks:
                self.execute_mute(mute_type, track)
        elif mute_what == 2:
            self.call_method_on_all_tracks(LOOPER_TRACK, "execute_mute", mute_type)
        elif mute_what == 3:
            self.call_method_on_all_tracks(CLIP_TRACK, "execute_mute", mute_type)
        elif mute_what == 4:
            self.call_method_on_all_tracks(BOTH_TRACK_TYPES, "execute_mute", mute_type)

    def execute_mute(self, mute_type, track):
        # mute = 0
        # unmute = 1
        # toggle = 2
        if mute_type is 0:
            track.mute = True
        elif mute_type is 1:
            track.mute = False
        elif mute_type is 2:
            track.mute = not track.mute

    ##### EFFECT ENTIRE SESSION #####

    def on_scene_change(self):
        self.__parent.send_message("scene changed")
        for x, scene in enumerate(self.scenes):
            scene.init_listener()

    def move_session_highlight(self, data):
        self.__parent.send_message("moving session highlight:" + str(data.data1))
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

    def mute_all_tracks_playing_clips(self, data):
        if data.data1 == OFF:
            self.ex_mute_all_tracks_playing_clips()

        elif data.data1 == ON:
            self.unmute_all_tracks_playing_clips()

        elif data.data1 == TOGGLE:
            if len(self.state.muted_tracks) == 0:
                self.ex_mute_all_tracks_playing_clips()
            else:
                self.unmute_all_tracks_playing_clips()

    def ex_mute_all_tracks_playing_clips(self):
        for track in self.song.tracks:
            if track.playing_slot_index != -1:
                self.state.muted_tracks.append(track)
                track.mute = 1

    def unmute_all_tracks_playing_clips(self):
        for track in self.state.muted_tracks:
            track.mute = 0
            self.state.muted_tracks = []

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


    def jump_to_next_bar(self, changeBPM):
        self.state.was_recording = self.song.record_mode
        time = int(self.song.current_song_time) + (self.song.signature_denominator - (
                int(self.song.current_song_time) % self.song.signature_denominator))
        self.state.bpm = self.song.tempo
        self.song.current_song_time = time
        self.song.record_mode = self.state.was_recording
        if changeBPM:
            self.timerCounter = 0
            self.tempo_change_timer.start()

    def change_mode(self, data):
        self.state.change_mode(self.__parent, data.data1)
        self.__parent.send_message("mode change to: " + str(data.data1))


    def send_color_dump(self):
        pass
        # x0 = 0
        # y0 = 0
        # self.__parent.send_sysex(CLIP_COLOR_COMMAND, 127, 127, 0)
        # for x in range(self.state.sceneOffset, self.state.sceneOffset+3):
        #     for y in range(self.state.trackOffset, self.state.trackOffset + 3):
        #         if self.song.tracks[y].clip_slots[x].has_clip:
        #             color = self.song.tracks[y].clip_slots[x].clip.color
        #             carray = self.get_color_array(color)
        #             buttonNum = y0 + x0 * NUM_CONTROLS
        #             self.__parent.send_sysex(CLIP_COLOR_COMMAND, buttonNum, carray[0], carray[1], carray[2], carray[3], carray[4], carray[5])
        #         y0+=1
        #     x0+=1
        #     y0 = 0

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
