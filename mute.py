from consts import *
from dltrack import DlTrack
from cltrack import ClTrack
from track import Track

class Mute:
    def __init__(self, parent, buttonNum, mute_type, mute_what, song, tracks):
        self.tracks = tracks
        self.__parent = parent
        self.song = song
        self.mute_type = mute_type
        self.buttonNum = buttonNum
        self.mute_what = mute_what
        self.is_muted = False

        #mute what:
        # 0 = tracks playing clips
        # 1 = all tracks
        # 2 = all dl# tracks
        # 3 = all cl# tracks
        # 4 = all cl# and dl# tracks

        #mute type:
        # 0 = mute
        # 1 = unmute
        # 2 = toggle

    def request_state(self):
        self.__parent.send_message("sending mute state")
        if self.is_muted:
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.buttonNum, OFF_STATE)
        else:
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.buttonNum, CLEAR_STATE)

    def execute_mute(self):
        self.__parent.send_message("executing mute on buttonNum: " + str(self.buttonNum) + " mute_type: " + str(self.mute_type) + " mute what: " + str(self.mute_what))
        # Get the function from switcher dictionary

        if self.mute_type == 2:
            self.is_muted = not self.is_muted
        else:
            self.is_muted = self.mute_type  

        getattr(self, self.get_method(self.mute_what))(self.is_muted)

        self.request_state()

    def mute_tracks_playing_clips(self, shouldMute):
        for track in self.song.tracks:
            if track.playing_slot_index > -1:
                track.mute = shouldMute

    def mute_all_tracks(self, shouldMute):
        for track in self.song.tracks:
            track.mute = shouldMute

    def mute_all_dl_tracks(self, shouldMute):
        for tracks in self.tracks.values():
            for track in tracks:
                if isinstance(track, DlTrack):
                    track.track.mute = shouldMute

    def mute_all_cl_tracks(self, shouldMute):
        for tracks in self.tracks.values():
            for track in tracks:
                if isinstance(track, ClTrack):
                    track.track.mute = shouldMute

    def mute_all_looper_tracks(self, shouldMute):
        for tracks in self.tracks.values():
            for track in tracks:
                track.track.mute = shouldMute

    @staticmethod
    def get_method(argument):
        action_map = {
            0: "mute_tracks_playing_clips",
            1: "mute_all_tracks",
            2: "mute_all_dl_tracks",
            3: "mute_all_cl_tracks",
            4: "mute_all_looper_tracks"
        }
        return action_map.get(argument, "Invalid Action")

    def remove(self):
        pass