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
<<<<<<< HEAD
        self.track_arm = self.track.arm
        #self.track.add_arm_listener(self.set_arm)

    def set_arm(self):
        self.track_arm = self.track.arm

    def reset_arm(self):
        self.track.arm = self.track_arm

    def arm_track(self):
        self.track_arm = self.track.arm
        self.track.arm = 1
=======
        self.artificial_arm = -1
        self.orig_arm = self.track.arm
        self.new_session_mode = False
        self.lastState = CLEAR_STATE

    def new_clip(self):
        pass
>>>>>>> 4bd5a188f69dc0b9287a6a0fe3130311a326c026

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
        self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)