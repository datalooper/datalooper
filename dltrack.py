from consts import *
from time import time
import Live
from track import Track
import thread

class DlTrack(Track):
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, device, trackNum, song):
        super(DlTrack, self).__init__(parent, track, trackNum, song)
        self.device = device
        self.state = device.parameters[STATE]
        self.lastState = CLEAR_STATE
        self.state.add_value_listener(self._on_looper_param_changed)
        self.rectime = 0
        self.nextQuantize = -1
        self.__parent = parent
        self.quantizeTicks = -1
        self._notification_timer = -1

    def send_message(self, message):
        self.__parent.send_message(message)

    def updateState(self, state):
        if state == CLEAR_STATE:
            self.state.value = STOP_STATE
        else:
            self.state.value = state
        self.lastState = state
        self.send_message("updating LED " + str(self.lastState))
        self.send_sysex(self.trackNum, CHANGE_STATE_COMMAND, self.lastState)

    def record(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[STATE].value) + " rec pressed")
        self.quantizeTicks = self.convertToTicks(self.device.parameters[QUANTIZATION].value)
        if self.lastState == PLAYING_STATE:
            self.updateState(OVERDUB_STATE)
        elif self.lastState == OVERDUB_STATE:
            self.updateState(PLAYING_STATE)
        elif self.quantizeTicks == 0:
            self.trigger_record()
        else:
            self.quantizeTrigger()

    def stop(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " stop pressed")
        if self.lastState == RECORDING_STATE:
            self.updateState(CLEAR_STATE)
        else:
            self.updateState(STOP_STATE)
        # todo clean this up, follow tempo
        #self.device.parameters[TEMPO_CONTROL].value = NO_SONG_CONTROL

    def undo(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " undo pressed")

    def clear(self):
        self.__parent.send_message(
            "Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " clear pressed")
        self.updateState(CLEAR_STATE)

    def calculateBPM(self):
        recmin = self.rectime / 60
        bpm4 = 4 / recmin
        bpm8 = 8 / recmin
        bpm16 = 16 / recmin
        bpms = [bpm4, bpm8, bpm16]
        bpm = min(bpms, key=lambda x: abs(x - 120))
        # self.__parent.set_bpm(bpm)

    def quantizeTrigger(self):
        self.send_message("quantize trigger")
        ms = self.getMS()
        quantizeMS = self.quantizeTicks * 60000 / (self.song.tempo * 240.)
        nextQuantize = quantizeMS - (ms % quantizeMS)
        self.setTimer(nextQuantize)

    def getMS(self):
        time = self.song.get_current_smpte_song_time(Live.Song.TimeFormat.ms_time)
        ms = int(time.hours) * 3600000 + int(time.minutes) * 60000 + int(time.seconds) * 1000 + int(time.frames)
        return ms

    def setTimer(self, interval):
        self.send_message("setting timer for: " + str(interval) + " ms")
        self._notification_timer = Live.Base.Timer(callback=self.trigger_record, interval=int(interval),
                                                   repeat=False)
        self._notification_timer.start()

    def trigger_record(self):
        self.send_message("triggering record")
        if self.lastState == RECORDING_STATE:
            self.rectime = time() - self.rectime
            self.calculateBPM()
            self.updateState(PLAYING_STATE)
            #self.device.parameters[TEMPO_CONTROL].value = SET_AND_FOLLOW_SONG_TEMPO
        elif self.lastState == CLEAR_STATE:
            self.updateState(RECORDING_STATE)
            self.rectime = time()
        elif self.lastState == STOP_STATE:
            self.updateState(PLAYING_STATE)

    def on_quarter_note(self):
        if self.req_record == 1:
            thread.start_new_thread(self.record_now, ())
            self.req_record = 0
        elif self.req_record == 2:
            thread.start_new_thread(self.play_now, ())
            self.req_record = 0

    def record_now(self):
        self.updateState(RECORDING_STATE)

    def play_now(self):
        self.updateState(PLAYING_STATE)

    def convertToTicks(self, value):
        if value == NONE:
            return 0
        elif value == GLOBAL:
            return self.convertToTicks(self.song.clip_trigger_quantization)
        elif value == EIGHT_BARS:
            return 7680
        elif value == FOUR_BARS:
            return 3840
        elif value == TWO_BARS:
            return 1920
        elif value == ONE_BAR:
            return 960
        elif value == HALF_NOTE:
            return 480
        elif value == HALF_TRIPLET:
            return 360
        elif value == QUARTER_NOTE:
            return 240
        elif value == QUARTER_TRIPLET:
            return 180
        elif value == EIGHTH_NOTE:
            return 120
        elif value == EIGHTH_TRIPLET:
            return 90
        elif value == SIXTEENTH_NOTE:
            return 60
        elif value == SIXTEENTH_NOTE_TRIPLET:
            return 45
        elif value == THIRTY_SECOND_NOTE:
            return 30
