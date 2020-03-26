from consts import *
from dltrack import DlTrack
from cltrack import ClTrack
from track import Track

class Solo:
    def __init__(self, parent, song, tracks):
        self.looper_tracks = tracks
        self.__parent = parent
        self.song = song
        self.tracks = song.tracks
        self.muted_tracks = []
        self.soloed_tracks = []
        self.linked_buttons = {}
        #solo what:
        # 0 = tracks playing clips
        # 1 = all tracks
        # 2 = all dl# tracks
        # 3 = all cl# tracks
        # 4 = all cl# and dl# tracks

        #solo type:
        # 0 = solo
        # 1 = unsolo
        # 2 = toggle

    def request_state(self, track_number):
        if track_number in self.linked_buttons:
            button_number = self.linked_buttons[track_number]
            self.__parent.send_message("sending solo state")
            requested_tracks = self.looper_tracks.get(str(track_number))
            for requested_track in requested_tracks:
                if requested_track in self.soloed_tracks:
                    self.__parent.send_sysex(CHANGE_STATE_COMMAND, button_number, CLEAR_STATE)
                    return
                else:
                    self.__parent.send_sysex(CHANGE_STATE_COMMAND, button_number, OFF_STATE)

    def execute_solo(self, track_num, mute_all, exclusive_solo):

        self.__parent.send_message("executing solo on track number: " + str(track_num))
        requested_solo_tracks = self.looper_tracks.get(str(track_num))

        for requested_solo_track in requested_solo_tracks:
            if requested_solo_track in self.soloed_tracks:
                self.unsolo_track(requested_solo_tracks)
                self.request_state(track_num)
                return
            if requested_solo_track.track in self.muted_tracks:
                requested_solo_track.track.mute = False

        if mute_all:
            skip_track = False
            for track in self.tracks:
                if not track.mute:
                    for requested_solo_track in requested_solo_tracks:
                        if requested_solo_track.track == track:
                            skip_track = True
                    for soloed_track in self.soloed_tracks:
                        if soloed_track.track == track:
                            skip_track = True
                    if skip_track:
                        skip_track = False
                    else:
                        track.mute = True
                        self.muted_tracks.append(track)
        else:
            for looper_track in self.looper_tracks.values():
                for single_looper_track in looper_track:
                    track = single_looper_track.track
                    if not track.mute and single_looper_track not in requested_solo_tracks and single_looper_track not in self.soloed_tracks:
                        track.mute = True
                        self.muted_tracks.append(track)

        if exclusive_solo:
            for soloed_track in self.soloed_tracks:
                soloed_track.track.mute = True
                self.muted_tracks.append(soloed_track.track)
                self.soloed_tracks = []
                self.request_state(soloed_track.trackNum)
        for requested_solo_track in requested_solo_tracks:
            self.soloed_tracks.append(requested_solo_track)

        self.request_state(track_num)

    def unsolo_track(self, requested_solo_tracks):

        self.__parent.send_message("unsoloing tracks")
        for requested_solo_track in requested_solo_tracks:
            self.soloed_tracks.remove(requested_solo_track)

        if not self.soloed_tracks:
            for track in self.muted_tracks:
                track.mute = False
            self.muted_tracks = []
        else:
            for requested_solo_track in requested_solo_tracks:
                requested_solo_track.track.mute = True
                self.muted_tracks.append(requested_solo_track.track)

    def link_button(self, button_number, track_number):
        self.linked_buttons[track_number] = button_number
        self.__parent.send_message("linking button number: " + str(button_number) + " to track number: " + str(track_number) + " solo control")