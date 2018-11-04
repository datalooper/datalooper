from consts import *
from time import time
import Live
class DlTrack:
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, device, trackNum, song):
        self.__parent = parent
        self.track = track
        self.device = device
        self.trackNum = trackNum
        self.state = device.parameters[STATE]
        self.lastState = CLEAR_STATE
        self.state.add_value_listener(self._on_looper_param_changed)
        self.rectime = 0
        self.song = song
        self.nextQuantize = -1
        self.quantizeTicks = -1
        self._notification_timer = -1

    #some weird logic has to happen because Ableton doesn't differenciate between clear and stop state. We have to make an educated guess.
    def _on_looper_param_changed(self):
        self.__parent.send_message("Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[STATE].value))
        self.updateTrackStatus(self.lastState)

    def updateTrackStatus(self, status):
        sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, self.trackNum - 1, status, 247)
        self.__parent.send_midi(sysex)

    def clearListener(self):
        self.send_message(self.track.name)
        if self.device.parameters[STATE].value_has_listener(self._on_looper_param_changed):
            self.device.parameters[STATE].remove_value_listener(self._on_looper_param_changed)

    def send_message(self, message):
        self.__parent.send_message(message)


    def updateState(self, state):
        if state == CLEAR_STATE:
            self.state.value = STOP_STATE
        else:
            self.state.value = state
        self.lastState = state

    def onRecordPressed(self):
        self.__parent.send_message("Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[STATE].value) + " rec pressed")
        self.quantizeTicks = self.convertToTicks(self.device.parameters[QUANTIZATION].value)
        if self.lastState == PLAYING_STATE:
            self.updateState(OVERDUB_STATE)
        elif self.lastState == OVERDUB_STATE:
            self.updateState(PLAYING_STATE)
        elif self.quantizeTicks == 0:
            self.trigger_record()
        else:
            self.quantizeTrigger()

    def onStopPressed(self):
        self.__parent.send_message("Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " stop pressed")
        if self.lastState == RECORDING_STATE:
            self.updateState(CLEAR_STATE)
        else:
            self.updateState(STOP_STATE)
        #todo clean this up, follow tempo
        self.device.parameters[TEMPO_CONTROL].value = NO_SONG_CONTROL

    def onUndoPressed(self):
        self.__parent.send_message("Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " undo pressed")

    def onClearPressed(self):
        self.__parent.send_message("Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value) + " clear pressed")
        self.updateState(CLEAR_STATE)

    def calculateBPM(self):
        recmin = self.rectime / 60
        bpm4 = 4 / recmin
        bpm8 = 8 / recmin
        bpm16 = 16 / recmin
        bpms = [bpm4, bpm8, bpm16]
        bpm = min(bpms, key=lambda x:abs(x-120))
        #self.__parent.set_bpm(bpm)

    def quantizeTrigger(self):
        ms = self.getMS()
        quantizeMS = self.quantizeTicks * 60000 / (self.song.tempo * 240.)
        self.nextQuantize = quantizeMS - (ms % quantizeMS)
        self.setTimer()

    def getMS(self):
        time = self.song.get_current_smpte_song_time(Live.Song.TimeFormat.ms_time)
        ms = int(time.hours) * 3600000 + int(time.minutes) * 60000 + int(time.seconds) * 1000 + int(time.frames)
        return ms

    def setTimer(self):
        self._notification_timer = Live.Base.Timer(callback=self.trigger_record, interval=int(self.nextQuantize), repeat=False)
        self._notification_timer.start()

    def trigger_record(self):
        if self.lastState == RECORDING_STATE:
            self.rectime = time() - self.rectime
            self.calculateBPM()
            self.updateState(PLAYING_STATE)
            self.device.parameters[TEMPO_CONTROL].value = SET_AND_FOLLOW_SONG_TEMPO
        elif self.lastState == CLEAR_STATE:
            self.updateState(RECORDING_STATE)
            self.rectime = time()
        elif self.lastState == STOP_STATE:
            self.updateState(PLAYING_STATE)

    def onTimeChange(self, ticks):
        pass

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

