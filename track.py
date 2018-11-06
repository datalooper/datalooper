from consts import *
import math

class Track(object):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, trackNum, song):
        self.__parent = parent
        self.track = track
        self.trackNum = trackNum
        self.lastState = CLEAR_STATE
        self.song = song
        self.req_record = 0

    def _on_looper_param_changed(self):
        self.update_track_status(self.lastState)

    def update_track_status(self, status):
        pass

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def clearListener(self):
        pass

    def send_message(self, message):
        self.__parent.send_message(message)

    def update_state(self, state):
        self.lastState = state

    def record(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + "record pressed")

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
