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
        self.track_arm = self.track.arm
        #self.track.add_arm_listener(self.set_arm)

    def set_arm(self):
        self.track_arm = self.track.arm

    def reset_arm(self):
        self.track.arm = self.track_arm

    def arm_track(self):
        self.track_arm = self.track.arm
        self.track.arm = 1

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def clearListener(self):
        pass

    def send_message(self, message):
        self.__parent.send_message(message)

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

    def toggle_new_session_mode(self, on):
        pass
