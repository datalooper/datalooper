from consts import *
import math

class Track(object):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, trackNum, song):
        self.__parent = parent
        self.track = track
        self.trackNum = trackNum
        self.song = song
        self.req_record = 0
        self.artificial_arm = -1
        if self.track.can_be_armed:
            self.orig_arm = self.track.arm
        else:
            self.orig_arm = 1
        self.new_session_mode = False
        self.lastState = CLEAR_STATE

    def new_clip(self):
        pass

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def clearListener(self):
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

    def clear(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + "clear pressed")

    def toggle_mute(self):
        pass

    def toggle_new_session_mode(self, on):
        pass

    def updateState(self, state):
        self.send_message("updating state: " + str(state))
        self.lastState = state
        if self.trackNum not in self.__parent.duplicates or (self.trackNum in self.__parent.duplicates and "LED" in self.track.name):
            self.send_message("really updating state")
            self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)

    def removeTrack(self):
        pass