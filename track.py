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
        self.led_disabled = False
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
        self.button_num = -1

    def clear_listener(self):
        pass

    def toggle_playback(self):
        pass

    def send_message(self, message):
        self.__parent.send_message(message)

    def stop(self, quantized):
        pass

    def undo(self):
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
                            self.clearTimer.start()
        else:
            self.clear_immediately()

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

    def clear_immediately(self):
        if self.parameter is not -1:
            self.parameter.value = self.preClearGain

    def start(self, start_type):
        if self.lastState != CLEAR_STATE:
            self.record(start_type)

    def record(self, quantized):
        pass

    def on_quantize_disabled(self):
        pass

    def update_state(self, state):
        # self.send_message("updating state on track num: " + str(self.trackNum) + " from state: " + str(self.lastState) + " to: " + str(state) + " track name: " + self.track.name)

        if state != -1:
            self.lastState = state
            if self.button_num is not -1 and not self.led_disabled:
                self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.button_num, self.lastState)
            if self.lastState == PLAYING_STATE or self.lastState == OVERDUB_STATE:
                self.global_state.mode = LOOPER_MODE
        # if self.trackNum not in self.__parent.duplicates or (
        #         self.trackNum in self.__parent.duplicates and "LED" in self.track.name):
        #     self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)

    def request_state(self):
        self.send_message("sending requested state on track num: " + str(self.trackNum) + " to state: " + str(self.lastState) + " track name: " + self.track.name + " button number:" + str(self.button_num))
        if self.button_num != -1 and not self.led_disabled:
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.button_num, self.lastState)

    def disable_led(self):
        self.send_message("disabling led on track name:" + str(self.track.name))
        self.led_disabled = True

    def remove_track(self):
        pass

    def change_mode(self):
        pass

    def record_quantized(self):
        self.record(True)

    def record_immediately(self):
        self.record(False)

    def stop_quantized(self):
        self.stop(True)

    def stop_immediately(self):
        self.stop(False)

    def quick_fade_clear(self):
        self.clear(500)

    def long_fade_clear(self):
        self.clear(1500)

    def execute_mute(self, mute_type):
        self.action_handler.execute_mute(mute_type, self.track)

    def link_button(self, button_num):
        self.send_message("linking button: " + str(button_num))
        self.button_num = button_num
        self.request_state()
