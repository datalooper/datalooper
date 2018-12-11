from consts import *

class State:

    def __init__(self, song):
        self.metro = -1
        self.tap_tempo_counter = 0
        self.new_scene = False
        self.unquantized_stop = False
        self.bpm = song.tempo
        self.mode = LOOPER_MODE
        self.muted_tracks = []