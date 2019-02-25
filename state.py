from consts import *


class State:

    def __init__(self, song):
        self.metro = -1
        self.curBeats = 0
        self.tap_tempo_counter = 0
        self.new_scene = False
        self.unquantized_stop = False
        self.bpm = song.tempo
        self.mode = LOOPER_MODE
        self.muted_tracks = []
        self.was_recording = False
        self.song = song

    def updateBPM(self, bpm):
        self.bpm = bpm
        self.song.tempo = self.bpm

    def change_mode(self, mode):
        self.mode = mode
        if mode == LOOPER_MODE:
            self.song.metronome = self.metro
            self.tap_tempo_counter = 0
        elif mode == NEW_SESSION_MODE:
            self.metro = self.song.metronome
            self.song.metronome = 0

    def restore_metro(self):
        self.song.metronome = self.metro
        self.metro = -1
        self.tap_tempo_counter = 0
