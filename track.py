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
        self.mute_button = -1
        self.track.add_mute_listener(self.on_mute)

    def clear_listener(self):
        pass

    def toggle_playback(self):
        pass

    def send_message(self, message):
        self.__parent.send_message(message)

    def stop(self, quantized):
        pass

    def undo(self, on_all = False):
        pass

    def clear(self, fadeTime):
        parameter = self.can_fade()
        if fadeTime > 0 and parameter:
            self.parameter = parameter
            self.preClearGain = parameter.value
            self.clearTimer = Live.Base.Timer(callback=lambda: self.fade(float(-self.parameter.min / float(fadeTime / 100)), fadeTime / 100), interval=100, repeat=True)
            self.clearTimer.start()
        else:
            self.clear_immediately()

    def can_fade(self):
        for device in self.track.devices:
            if device.name == "Utility":
                for parameter in device.parameters:
                    if parameter.name == "Gain":
                        return parameter
        return False

    def fade(self, increment, numRepeats):
        self.send_message("gain min:" + str(self.parameter.min))
        if self.parameter is not -1 and self.parameter.value >= self.parameter.min + increment:
            self.parameter.value = float(self.parameter.value) - increment
        else:

            self.parameter.value = -1
            self.clearTimer.stop()
            self.clearTimerCounter = 0
            self.clear_immediately()

        if self.clearTimerCounter >= numRepeats:
            self.clearTimer.stop()
            self.clearTimerCounter = 0
        else:
            self.clearTimerCounter += 1

    def clear_immediately(self, on_all = False):
        if self.parameter is not -1:
            self.parameter.value = self.preClearGain

    def start(self, start_type, on_all = False):
        if self.lastState != CLEAR_STATE:
            self.record(start_type, on_all)

    def record(self, quantized):
        pass

    def on_quantize_disabled(self):
        pass

    def update_state(self, state):
        if self.track and state != -1 :
            # self.send_message("current monitoring state: " + str(self.track.current_monitoring_state))
            if self.lastState != state and self.global_state.mode != NEW_SESSION_MODE and self.button_num is not -1:
                self.__parent.send_sysex(BLINK, self.button_num, BlinkTypes.SLOW_BLINK)
            self.send_message("in update state, updating lastState to " + str(state))
            self.lastState = state
            if self.button_num is not -1 and not self.led_disabled and ( self.track.arm or self.track.current_monitoring_state is 0):
                self.send_message("updating state on track num: " + str(self.trackNum) + " from state: " + str(self.lastState) + " to: " + str(state) + " track name: " + self.track.name)
                self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.button_num, self.lastState)
            if self.lastState == PLAYING_STATE or self.lastState == OVERDUB_STATE:
                self.global_state.mode = LOOPER_MODE
        # if self.trackNum not in self.__parent.duplicates or (
        #         self.trackNum in self.__parent.duplicates and "LED" in self.track.name):
        #     self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)

    def request_state(self):
        self.send_message("sending requested state on track num: " + str(self.trackNum) + " to state: " + str(self.lastState) + " track name: " + self.track.name + " button number:" + str(self.button_num))
        if self.button_num != -1 and not self.led_disabled and ( self.track.arm or self.track.current_monitoring_state is 0):
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.button_num, self.lastState)
        if self.mute_button != -1:
            if self.track.mute:
                mute_state = 5
            else:
                mute_state = 4
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.mute_button, mute_state)

    def disable_led(self):
        self.send_message("disabling led on track name:" + str(self.track.name))
        self.led_disabled = True

    def remove_track(self, on_all = False):
        pass

    def change_mode(self, on_all = False):
        pass

    def record_quantized(self, on_all = False):
        self.record(True)

    def record_immediately(self, on_all = False):
        self.record(False)

    def record_ignoring_state(self, on_all = False):
        pass

    def stop_quantized(self, on_all = False):
        self.stop(True, on_all)

    def stop_immediately(self, on_all = False):
        self.stop(False, on_all)

    def quick_fade_clear(self, on_all = False):
        self.clear(500)

    def long_fade_clear(self, on_all = False):
        self.clear(1500)

    def link_button(self, button_num, action):
        if action == 'record_quantized' or action == 'record_unquantized' :
            self.send_message("linking button: " + str(button_num))
            self.button_num = button_num
            self.request_state()
        elif action == 'toggle_mute':
            self.mute_button = button_num
            self.request_state()

    def toggle_mute(self, on_all = False):
        self.track.mute = not self.track.mute

    def on_mute(self):
        self.send_message("track mute changed")
        self.request_state()

    def remove_clip_slot(self, on_all = False):
        pass