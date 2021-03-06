from consts import *
from time import time
import Live
from track import Track


class DlTrack(Track):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, device, trackNum, song, state, action_handler):
        super(DlTrack, self).__init__(parent, track, trackNum, song, state, action_handler)
        self.updateReq = False
        self.name_timer = Live.Base.Timer(callback=self.change_name, interval=1, repeat=False)
        self.tempo_control = -1
        self.device = device
        self.state = device.parameters[STATE]
        self.rectime = 0
        self.ignore_stop = False
        self.req_record = True
        self.__parent = parent
        self.tempState = ""
        self.undoState = False
        self.send_message("initializing new track num: " + str(self.trackNum))
        self.update_state(self.lastState)
        self.ignore_name_change = False
        self.device.parameters[TEMPO_CONTROL].add_value_listener(self.on_tempo_control_change)
        self.device.add_name_listener(self.on_name_change)
        if self.track.can_be_armed:
            self.track.add_arm_listener(self.set_arm)

        if not self.state.value_has_listener(self._on_looper_param_changed):
            self.state.add_value_listener(self._on_looper_param_changed)

    def set_arm(self):
        self.update_state(CLEAR_STATE)

    def _on_looper_param_changed(self):
        if self.lastState == CLEAR_STATE and self.state.value == STOP_STATE:
            return
        if self.state.value == STOP_STATE and str(self.device.name) == str(CLEAR_STATE):
            self.update_state(CLEAR_STATE)
        elif self.lastState != self.state.value:
            self.send_message("Looper param changed. Last State: " + str(self.lastState) + " New State: " + str(self.state.value))
            self.send_message("device name:" + str(self.device.name))
            self.update_state(int(self.state.value))

    def send_message(self, message):
        self.__parent.send_message(message)

    def on_tempo_control_change(self):
        if not self.global_state.ignore_tempo_control:
            # self.send_message("changing mode via listener")
            if self.device.parameters[TEMPO_CONTROL].value == 0:
                self.__parent.send_sysex(CHANGE_MODE_COMMAND, 1)
            else:
                self.__parent.send_sysex(CHANGE_MODE_COMMAND, 0)

    def stop_play_toggle(self, on_all = False):
        if self.lastState == STOP_STATE:
            self.request_control(MASTER_CONTROL)
        elif self.lastState == PLAYING_STATE:
            self.request_control(STOP_CONTROL)


    def request_control(self, controlNum):
        self.send_message("Requesting control: ")
        self.updateReq = True
        self.__parent.send_sysex(REQUEST_CONTROL_COMMAND, self.trackNum, (self.trackNum * NUM_CONTROLS) + controlNum)

    def record(self, quantized, on_all = False):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[STATE].value) + " rec pressed")
        if self.rectime == 0 or (time() - self.rectime) > .5:
            if not quantized and self.song.is_playing and self.lastState == CLEAR_STATE:
                self.send_message("updating to record state")
                self.updateReq = True
                self.state.value = RECORDING_STATE
                self.rectime = time()
            elif not quantized and self.song.is_playing and self.lastState == RECORDING_STATE:
                self.state.value = STOP_STATE
                self.calculateBPM(time() - self.rectime)
            elif not quantized and self.lastState == STOP_STATE:
                self.updateReq = True
                self.state.value = PLAYING_STATE
            else:
                # self.send_message("rectime: " + str(time() - self.rectime))
                self.rectime = time()
                if self.button_num != -1:
                    self.__parent.send_sysex(BLINK, self.button_num, BlinkTypes.FAST_BLINK)
                self.request_control(MASTER_CONTROL)

    def exclusive_record(self, quantized = True, on_all = False, looperNum = -1):
        self.send_message("exclusive record looperNum: " + str(looperNum) + " Track Num: " + str(self.trackNum))
        if looperNum == self.trackNum:
            self.record(quantized)
        elif self.lastState == RECORDING_STATE or self.lastState == OVERDUB_STATE:
            self.record(quantized)

    def record_ignoring_state(self, on_all = False):
        self.request_control(RECORD_CONTROL)

    def play(self, quantized):
        if self.lastState == STOP_STATE:
            # self.send_message("attempting play")
            if quantized:
                self.request_control(MASTER_CONTROL)
            else:
                self.state.value = PLAYING_STATE
            self.update_state(PLAYING_STATE)

    def stop(self, quantized, on_all = False):
        # self.__parent.send_message(
        #     "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " stop pressed")
        if self.lastState == RECORDING_STATE:
            self.request_control(CLEAR_CONTROL)
            self.ignore_stop = True
            self.update_state(CLEAR_STATE)
        elif self.lastState != STOP_STATE and self.lastState != CLEAR_STATE:
            if quantized or not self.song.is_playing:
                self.request_control(STOP_CONTROL)
                if self.song.is_playing and self.button_num != -1:
                    self.__parent.send_sysex(BLINK, self.button_num, BlinkTypes.FAST_BLINK)
            else:
                # self.send_message("entering stop state")
                self.updateReq = True
                self.update_state(STOP_STATE)
                self.state.value = STOP_STATE

        # SEND OUT CONTROL NO MATTER WHAT IF SONG IS NOT PLAYING, FOR MAPPING PARAMS
        elif not self.song.is_playing:
            self.request_control(STOP_CONTROL)

    def toggle_playback(self):
        if self.lastState == STOP_STATE:
            self.request_control(MASTER_CONTROL)
        elif self.lastState == PLAYING_STATE:
            self.request_control(STOP_CONTROL)

    def undo(self, on_all = False, fadeTime = 0):
        if (self.lastState != CLEAR_STATE and self.lastState != RECORDING_STATE) or not self.song.is_playing:
            self.send_message("requesting undo command")
            self.request_control(UNDO_CONTROL)
            self.undoState = not self.undoState
        else:
            self.clear_immediately(on_all)
            # if self.undoState:
            #     self.__parent.send_sysex(CLIP_COLOR_COMMAND, self.undo_button, 127, 127, 127, 127, 127, 127)
            # else:
            #     self.__parent.send_sysex(CLIP_COLOR_COMMAND, self.undo_button, 0, 0, 0, 0, 0, 0)



        # self.__parent.send_message(
        #     "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " undo pressed")

    def clear_immediately(self, on_all = False):
        super(DlTrack, self).clear_immediately()
        if self.lastState == OVERDUB_STATE:
            self.state.value = STOP_STATE
        self.request_control(CLEAR_CONTROL)
        # self.__parent.send_message(
        #     "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " clear pressed")
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
        self.global_state.queued = self
        self.rectime = 0
        self.global_state.bpm = bpm
        self.action_handler.jump_to_next_bar()

    def change_mode(self, on_all = False):
        # self.send_message("changing mode")
        if self.device:
            if self.global_state.mode == LOOPER_MODE:
                self.device.parameters[TEMPO_CONTROL].value = SET_AND_FOLLOW_SONG_TEMPO
            elif self.global_state.mode == NEW_SESSION_MODE:
                self.tempo_control = self.device.parameters[TEMPO_CONTROL].value
                self.device.parameters[TEMPO_CONTROL].value = NO_TEMPO_CONTROL

    def remove_track(self, on_all = False):
        if self.track in self.song.tracks:
            if self.track.can_be_armed and self.track.arm_has_listener(self.set_arm):
                self.track.remove_arm_listener(self.set_arm)
            if self.state is not None and self.state.value_has_listener(self._on_looper_param_changed):
                self.state.remove_value_listener(self._on_looper_param_changed)
        else:
            self.send_message("removing track: " + str(self.trackNum))
            self.update_state(OFF_STATE)

    def play(self, on_all = False):
        self.request_control(PLAY_CONTROL)

    def update_state(self, state):
        if state == CLEAR_STATE:
            self.undoState = False

        if self.device and self.device.name != str(state) and not (state is STOP_STATE and self.device.name is str(CLEAR_STATE)) and self.updateReq:
            self.updateReq = False
            self.tempState = state
            self.name_timer.start()
        super(DlTrack, self).update_state(state)

    def change_name(self):
        self.send_message("changing name on dl#" + str(self.trackNum) + " to: " + str(self.lastState)  )
        self.ignore_name_change = True
        self.device.name = str(self.tempState)

    def on_name_change(self):
        if not self.ignore_name_change and str(self.device.name) == str(CLEAR_STATE):
            self.send_message("updating state based on device name")
            self.update_state(int(self.device.name))
        self.ignore_name_change = False

    def clear(self, on_all = False, fadeTime = 0):
        if self.lastState == CLEAR_STATE or self.lastState == RECORDING_STATE:
            self.clear_immediately()
        else:
            super(DlTrack, self).clear(on_all, fadeTime)