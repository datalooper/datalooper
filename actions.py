# 0: "record",
# 1: "stop",
# 2: "undo",
# 3: "clear",
# 4: "mute_track",
# 5: "new_clip",
# 6: "bank",
# 7: "change_instance",
# 8: "record_bank",
# 9: "stop_bank",
# 10: "undo_bank",
# 11: "clear_bank",
# 12: "start_bank",
# 13: "mute_bank",
# 14: "record_all",
# 15: "stop_all",
# 16: "undo_all",
# 17: "clear_all",
# 18: "start_all",
# 19: "mute_all",
# 20: "toggle_stop_start",
# 21: "stop_all_playing_clips",
# 22: "mute_all_tracks_playing_clips",
# 23: "create_scene",
# 24: "metronome_control",
# 25: "tap_tempo",
# 26: "jump_to_next_bar",
# 27: "change_mode"


from consts import *
from cltrack import ClTrack
from dltrack import DlTrack
from track import Track
from state import State


class Actions:

    def __init__(self, parent, tracks, song):
        self.tracks = tracks
        self.state = State(song)
        self.song = song
        self.__parent = parent

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
        if data.mode == self.state.mode:
            self.__parent.send_message("track num: " + self.get_track_num_str(data))
            tracks = self.tracks.get(self.get_track_num_str(data))
            self.__parent.send_message(str(tracks))
            if tracks is not None:
                for track in tracks:
                    if isinstance(track, self.get_looper_type(track_type)):
                        getattr(track, method_name)(*args)

    def call_method_on_bank(self, data, track_type, method_name, *args):
        if data.mode == self.state.mode:
            x = 0
            while x < 3:
                tracks = self.tracks.get(str((data.instance * NUM_TRACKS * NUM_BANKS) + (data.bank * NUM_TRACKS) + x))
                if tracks is not None:
                    for track in tracks:
                        if isinstance(track, self.get_looper_type(track_type)):
                            getattr(track, method_name)(*args)
                x += 1

    def call_method_on_all_tracks(self, data, track_type, method_name, *args):
        if data.mode == self.state.mode:
            for tracks in self.tracks.values():
                for track in tracks:
                    self.__parent.send_message("track name: " + str(track.trackNum))
                    if isinstance(track, self.get_looper_type(track_type)):
                        getattr(track, method_name)(*args)

    def check_uniform_state(self, state):
        for tracks in self.tracks.values():
            for track in tracks:
                # self.send_message("track " + str(track.trackNum) + " State:" + str(track.lastState))
                if track.lastState not in state:
                    return False
        return True

    ##### TRACK ACTIONS #####

    def record(self, data):

        # If datalooper is in 'unquantized stop' state, turn on the metronome and jump to the downbeat
        if self.state.unquantized_stop:
            self.song.metronome = self.state.metro
            self.jump_to_next_bar(False)
            self.state.unquantized_stop = False

            # set record to unquantized
            data.data2 = False
        self.call_method_on_tracks(data, data.data1, "record", data.data2)

    def stop(self, data):
        self.call_method_on_tracks(data, data.data1, "stop", data.data2)

    def undo(self, data):
        self.call_method_on_tracks(data, data.data1, "undo")

    def clear(self, data):
        self.call_method_on_tracks(data, data.data1, "clear", data.data2)

    def mute(self, data):
        self.call_method_on_tracks(data, data.data1, "mute", data.data2)

    def new_clip(self, data):
        self.call_method_on_tracks(data, CLIP_TRACK, "new_clip")

    ##### BANKING ACTIONS #####

    def bank(self, data):
        self.call_method_on_bank(data, BOTH_TRACK_TYPES, "update_state", -1)

    def change_instance(self, data):
        pass

    ##### EFFECT ALL TRACKS ON BANK ACTIONS #####

    def record_bank(self, data):
        self.call_method_on_bank(data, data.data1, "record")

    def stop_bank(self, data):
        self.call_method_on_bank(data, data.data1, "stop")

    def undo_bank(self, data):
        self.call_method_on_bank(data, data.data1, "undo")

    def clear_bank(self, data):
        self.call_method_on_bank(data, data.data1, "clear")

    def start_bank(self, data):
        self.call_method_on_bank(data, data.data1, "start", data.data2)

    def mute_bank(self, data):
        self.call_method_on_bank(data, data.data1, "mute", data.data2)

    ##### EFFECT ALL DATALOOPER TRACKS ACTIONS #####

    def record_all(self, data):
        self.call_method_on_all_tracks(data, data.data1, "record")

    def stop_all(self, data):
        self.call_method_on_all_tracks(data, data.data1, "stop", data.data2)

    def undo_all(self, data):
        self.call_method_on_all_tracks(data, data.data1, "undo")

    def clear_all(self, data):
        self.call_method_on_all_tracks(data, data.data1, "clear", data.data2)

    def start_all(self, data):
        self.call_method_on_all_tracks(data, data.data1, "start", data.data2)

    def mute_all(self, data):
        self.call_method_on_all_tracks(data, data.data1, "mute", data.data2)

    def toggle_stop_start(self, data):
        if not self.check_uniform_state([CLEAR_STATE]) and self.check_uniform_state([STOP_STATE, CLEAR_STATE]):
            self.call_method_on_all_tracks(data, data.data1, "start", data.data2)
            if data.data2 == 0:
                self.jump_to_next_bar()
        else:
            self.call_method_on_all_tracks(data, data.data1, "stop", data.data2)

    def new_clips_on_all(self, data):
        self.call_method_on_all_tracks(data, CLIP_TRACK, "new_clip")

    ##### EFFECT ENTIRE SESSION #####

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
        pass

    def tap_tempo(self, data):
        pass

    def jump_to_next_bar(self):
        self.state.was_recording = self.song.record_mode
        time = int(self.song.current_song_time) + (self.song.signature_denominator - (
                int(self.song.current_song_time) % self.song.signature_denominator))
        self.state.bpm = self.song.tempo
        self.song.current_song_time = time
        self.song.record_mode = self.state.was_recording
        # if changeBPM:
        #     self.timerCounter = 0
        #     self.tempo_change_timer.start()

    def change_mode(self, data):
        self.state.mode = data.data1
        self.call_method_on_all_tracks(data, BOTH_TRACK_TYPES, "change_mode", data.data1)