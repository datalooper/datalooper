from consts import *
from time import time
import Live
from track import Track


class DlTrack(Track):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, device, trackNum, song, state, action_handler):
        super(DlTrack, self).__init__(parent, track, trackNum, song, state, action_handler)
        self.tempo_control = -1
        self.device = device
        self.state = device.parameters[STATE]
        self.rectime = 0
        self.ignore_stop = False
        self.req_record = True
        self.__parent = parent
        self.req_bpm = False
        self.update_state(self.lastState)

        if self.track.can_be_armed:
            self.track.add_arm_listener(self.set_arm)

        if not self.state.value_has_listener(self._on_looper_param_changed):
            self.state.add_value_listener(self._on_looper_param_changed)

        self.song.add_tempo_listener(self.on_tempo_change)
        self.timer = Live.Base.Timer(callback=self.on_tempo_change_callback, interval=1, repeat=False)

    def set_arm(self):
        self.update_state(CLEAR_STATE)

    def _on_looper_param_changed(self):
        if self.lastState == CLEAR_STATE and self.state.value == STOP_STATE:
            return

        self.send_message("Looper param changed. Last State: " + str(self.lastState) + " New State: " + str(self.state.value))
        self.update_state(int(self.state.value))

    def send_message(self, message):
        self.__parent.send_message(message)

    def request_control(self, control):
        self.send_message("Requesting control: " + str(control))
        self.__parent.send_sysex(self.trackNum, REQUEST_CONTROL_COMMAND, control)

    def record(self, quantized):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[STATE].value) + " rec pressed")
        if not quantized:
            if self.lastState == RECORDING_STATE:
                self.state.value = STOP_STATE
                self.calculateBPM(time() - self.rectime)
            elif self.lastState == CLEAR_STATE:
                self.update_state(RECORDING_STATE)
                self.rectime = time()
                self.state.value = RECORDING_STATE
            elif self.lastState == STOP_STATE:
                self.state.value = PLAYING_STATE
        else:
            if self.rectime == 0 or (time() - self.rectime) > .5:
                self.send_message("rectime: " + str(time() - self.rectime))
                self.rectime = time()
                self.request_control(RECORD_CONTROL)

    def play(self, quantized):
        if self.lastState == STOP_STATE:
            self.send_message("attempting play")
            if quantized:
                self.request_control(RECORD_CONTROL)
            else:
                self.state.value = PLAYING_STATE

            self.update_state(PLAYING_STATE)

    def stop(self, quantized):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " stop pressed")
        if self.lastState == RECORDING_STATE:
            self.update_state(CLEAR_STATE)
            self.request_control(CLEAR_CONTROL)
            self.ignore_stop = True
        elif self.lastState != STOP_STATE and self.lastState != CLEAR_STATE:
            if quantized or not self.song.is_playing:
                self.request_control(STOP_CONTROL)
            else:
                self.send_message("entering stop state")
                self.update_state(STOP_STATE)
                self.state.value = STOP_STATE

        # SEND OUT CONTROL NO MATTER WHAT IF SONG IS NOT PLAYING, FOR MAPPING PARAMS
        elif not self.song.is_playing:
            self.request_control(STOP_CONTROL)

    def toggle_playback(self):
        if self.lastState == STOP_STATE:
            self.request_control(RECORD_CONTROL)
        elif self.lastState == PLAYING_STATE:
            self.request_control(STOP_CONTROL)

    def undo(self):
        if self.lastState != CLEAR_STATE or not self.song.is_playing:
            self.request_control(UNDO_CONTROL)

        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " undo pressed")

    def clear(self, clearType):
        self.request_control(CLEAR_CONTROL)
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " clear pressed")
        self.update_state(CLEAR_STATE)

    def calculateBPM(self, loop_length):
        loop_length_in_minutes = loop_length / 60
        i = 1
        bpms = []
        closest_to_tempo = 120

        while i <= 64:
            i *= 2
            bpm = i / loop_length_in_minutes
            if 140 > bpm > 50:
                bpms.append(bpm)

        bpm = min(bpms, key=lambda x: abs(x - closest_to_tempo))
        self.send_message("bpm: " + str(bpm))
        self.req_bpm = True
        self.rectime = 0
        self.global_state.updateBPM(bpm)

    def change_mode(self):
        if self.global_state.mode == LOOPER_MODE:
            self.device.parameters[TEMPO_CONTROL].value = self.tempo_control
        elif self.global_state.mode == NEW_SESSION_MODE:
            self.tempo_control = self.device.parameters[TEMPO_CONTROL].value
            self.device.parameters[TEMPO_CONTROL].value = NO_TEMPO_CONTROL

    def on_tempo_change(self):
        self.timer.start()

    def on_tempo_change_callback(self):
        self.send_message("on tempo change callback")
        self.send_message(str(self.req_bpm))
        if self.req_bpm:
            self.update_state(PLAYING_STATE)
            self.state.value = PLAYING_STATE
            self.action_handler.jump_to_next_bar(True)
            self.req_bpm = False
            self.action_handler.update_mode(LOOPER_MODE)

    def remove_track(self):
        if self.state.value_has_listener(self._on_looper_param_changed):
            self.state.remove_value_listener(self._on_looper_param_changed)
        if self.track.can_be_armed and self.track.arm_has_listener(self.set_arm):
            self.track.remove_arm_listener(self.set_arm)
