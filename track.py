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
        self.orig_arm = self.track.arm
        self.new_session_mode = False
        self.lastState = CLEAR_STATE


    def set_arm(self):
        if self.track.arm != self.artificial_arm:
            self.orig_arm = self.track.arm
            return True
        else:
            return False

    def new_clip(self):
        pass

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def clearListener(self):
        pass

    def send_message(self, message):
        self.__parent.send_message(message)

    def stop(self):
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
        if self.new_session_mode:
            if state == CLEAR_STATE:
                self.state.value = STOP_STATE
            else:
                self.state.value = state
        self.lastState = state
        self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)