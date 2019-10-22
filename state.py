from consts import *


class State:

    def __init__(self, song):
        self.metro = song.metronome
        self.curBeats = 0
        self.tap_tempo_counter = 0
        self.new_scene = False
        self.unquantized_stop = False
        self.bpm = song.tempo
        self.mode = LOOPER_MODE
        self.muted_tracks = []
        self.was_recording = False
        self.ignoreMetroCallback = False
        self.song = song
        self.sceneOffset = 0
        self.trackOffset = 0
        self.mute_toggled = False
        self.queued = False
        self.req_tempo_change = False
        self.should_record = song.record_mode

    def updateBPM(self, bpm):
        self.bpm = bpm

    def change_mode(self, parent, mode):
        self.mode = mode
        if mode == LOOPER_MODE:
            self.song.metronome = self.metro
            self.tap_tempo_counter = 0
            parent._set_session_highlight(-1, -1, -1, -1, False)
        elif mode == NEW_SESSION_MODE:
            self.metro = self.song.metronome
            self.song.metronome = 0
        elif mode == CLIP_LAUNCH_MODE:
            parent._set_session_highlight(self.sceneOffset, self.trackOffset, 3, 3, False)

    def restore_metro(self):
        self.song.metronome = self.metro
        self.metro = -1
        self.tap_tempo_counter = 0
