from consts import *
import math
from consts import *
import Live

class Track(object):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, trackNum, song, state, action_handler):
        self.__parent = parent
        self.track = track
        self.trackNum = trackNum
        self.song = song
        self.global_state = state
        self.action_handler = action_handler
        self.clearTimerCounter = 0
        self.parameter = -1
        self.preClearGain = 0
        self.clearTimer = -1
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
        pass

    def undo(self, quantized):
        pass

    def clear(self, fadeTime):
        if fadeTime > 0 :
            for device in self.track.devices:
                if device.name == "Utility":
                    for parameter in device.parameters:
                        if parameter.name == "Gain":
                            self.parameter = parameter
                            self.preClearGain = parameter.value
                            self.clearTimer = Live.Base.Timer(callback=lambda: self.fade(float(1 / float(fadeTime / 100)), fadeTime / 100), interval=100, repeat=True)
                            self.send_message(parameter.min)
                            self.clearTimer.start()
        else:
            self.clear_immediately(0)

    def fade(self, increment, numRepeats):
        if self.parameter is not -1 and self.parameter.value >= self.parameter.min + increment:
            self.parameter.value = float(self.parameter.value) - increment
        else:
            self.parameter.value = -1
            self.clearTimer.stop()
            self.clearTimerCounter = 0
            self.clear_immediately(0)

        if self.clearTimerCounter >= numRepeats:
            self.clearTimer.stop()
            self.clearTimerCounter = 0
        else:
            self.clearTimerCounter += 1

    def clear_immediately(self, data):
        if self.parameter is not -1:
            self.parameter.value = self.preClearGain

    def start(self, start_type):
        if self.lastState != CLEAR_STATE:
            self.record(start_type)

    def record(self, quantized):
        pass

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
            self.send_message("updating state on track num: " + str(self.trackNum) + " track name: " + self.track.name)
            self.lastState = state
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.trackNum, self.lastState)
        # if self.trackNum not in self.__parent.duplicates or (
        #         self.trackNum in self.__parent.duplicates and "LED" in self.track.name):
        #     self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)

    def remove_track(self):
        pass

    def change_mode(self):
        pass

    def record_quantized(self, data):
        self.record(True)

    def record_immediately(self, data):
        self.record(False)

    def stop_quantized(self, data):
        self.stop(True)

    def stop_immediately(self, data):
        self.stop(False)

    def quick_fade_clear(self, data):
        self.clear(500)

    def long_fade_clear(self, data):
        self.clear(1500)