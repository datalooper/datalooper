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
        self.linked_buttons = {}
        self.group_tracks = []

        self.song.add_tracks_listener(self.on_tracks_changed)
        self.song.remove_tracks_listener(self.on_tracks_changed)
        self.on_tracks_changed()

    def on_tracks_changed(self):
        self.group_tracks = []
        for track in self.tracks:
            if track.group_track and track.group_track not in self.group_tracks:
                self.group_tracks.append(track.group_track)
            if "NO-SOLO" in track.name:
                self.group_tracks.append(track)

    def request_state(self, track_number):
        pass
        # if track_number in self.linked_buttons:
        #     button_number = self.linked_buttons[track_number]
        #     self.__parent.send_message("sending solo state")
        #     requested_tracks = self.looper_tracks.get(str(track_number))
        #     for requested_track in requested_tracks:
        #         if requested_track in self.soloed_tracks:
        #             self.__parent.send_sysex(CHANGE_STATE_COMMAND, button_number, CLEAR_STATE)
        #             return
        #         else:
        #             self.__parent.send_sysex(CHANGE_STATE_COMMAND, button_number, OFF_STATE)

    def execute_solo(self, track_num, mute_all, exclusive_solo):

        self.__parent.send_message("executing solo on track number: " + str(track_num))

        if track_num is -1:
            for track in self.tracks:
                track.solo = False
            return

        requested_solo_tracks = self.looper_tracks.get(str(track_num))

        for requested_solo_track in requested_solo_tracks:
            if requested_solo_track.track.solo:
                self.unsolo_track(requested_solo_tracks)
                return
            else:
                requested_solo_track.track.solo = True

        if not mute_all:
            for track in self.tracks:
                solo = False
                if track not in self.group_tracks:
                    solo = True
                for looper_track_list in self.looper_tracks.values():
                    for looper_track in looper_track_list:
                        if looper_track.track == track and not track.solo:
                            solo = False

                track.solo = solo

    def unsolo_track(self, requested_solo_tracks):
        self.__parent.send_message("unsoloing tracks")
        for requested_solo_track in requested_solo_tracks:
            requested_solo_track.track.solo = False

        unsolo_all = True

        for looper_track in self.looper_tracks.values():
            for track in looper_track:
                if track.track.solo:
                    unsolo_all = False

        if unsolo_all:
            for track in self.tracks:
                track.solo = False

    def link_button(self, button_number, track_number):
        if track_number >= 0:
            self.linked_buttons[track_number] = Solo.SoloTrack(self.__parent, button_number, self.looper_tracks.get(str(track_number)))
            self.__parent.send_message("linking button number: " + str(button_number) + " to track number: " + str(track_number) + " solo control")

    class SoloTrack:
        def __init__(self, __parent, button_number, looper_tracks):
            self.looper_tracks = looper_tracks
            self.__parent = __parent
            self.button_number = button_number
            for looper_track in looper_tracks:
                looper_track.track.add_solo_listener(self.on_solo_change)

        def on_solo_change(self):
            light_on = False
            for looper_track in self.looper_tracks:
                if looper_track.track.solo:
                    light_on = True
            if light_on:
                self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.button_number, CLEAR_STATE)
            else:
                self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.button_number, OFF_STATE)

