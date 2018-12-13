from consts import *
import math
from consts import *


class Track(object):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, trackNum, song, state, action_handler):
        self.__parent = parent
        self.track = track
        self.trackNum = trackNum
        self.song = song
        self.global_state = state
        self.action_handler = action_handler

        if self.track.can_be_armed:
            self.orig_arm = self.track.arm
        else:
            self.orig_arm = 1
        self.lastState = CLEAR_STATE

    def clear_listener(self):
        pass

    def toggle_playback(self):
        pass

    def send_message(self, message):
        self.__parent.send_message(message)

    def stop(self, quantized):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + "stop pressed")

    def undo(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + "undo pressed")

    def clear(self, clear_type):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + "clear pressed")

    def start(self, start_type):
        if self.lastState != CLEAR_STATE:
            self.record(start_type)

    def mute(self, mute_type):
        if mute_type == OFF:
            self.track.mute = 1
        elif mute_type == ON:
            self.track.mute = 0
        else:
            if self.track.mute == 1:
                self.track.mute = 0
            elif self.track.mute == 0:
                self.track.mute = 1

    def update_state(self, state):
        if state != -1:
            self.lastState = state
        self.__parent.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)
        # if self.trackNum not in self.__parent.duplicates or (
        #         self.trackNum in self.__parent.duplicates and "LED" in self.track.name):
        #     self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)

    def remove_track(self):
        pass

    def change_mode(self):
        pass