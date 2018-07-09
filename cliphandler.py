#Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
import Live
from consts import *
from _Generic.Devices import *
from math import *
from claudiotrack import ClAudioTrack
from clmiditrack import ClMidiTrack
class ClipHandler:
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent, song):
        self.__parent = parent
        self.song = song
        self.clip_tracks = []

    def disconnect(self):
        self.__parent.disconnect()

    def clearTracks(self):
        self.clip_tracks = []

    def appendTracks(self, track, trackNum):
        #creates track objects
        if track.has_midi_input:
            self.send_message("adding midi track")
            self.clip_tracks.append(ClMidiTrack(self, track, trackNum, self.song))
        elif track.has_audio_input:
            self.send_message("adding audio track")
            self.clip_tracks.append(ClAudioTrack(self, track, trackNum))

    #receives midi notes from parent class
    def receive_midi_note(self, note_num):

        #maps note num to track control # (1-4) on DL Pedal
        control = (note_num - 1) % NUM_CONTROLS

        #maps note num to track # on DL pedal
        requestedTrackNum = int((floor((note_num - 1) / NUM_CONTROLS))) + 1

        #checks if the requested track number is in clip_tracks list
        if len(self.clip_tracks) >= requestedTrackNum:
            self.handleClipAction(requestedTrackNum, control)

    def send_midi(self, midi):
        self.__parent.send_midi(midi)

    def send_message(self, message):
        self.__parent.send_message(message)
    def handleClipAction(self, requestedTrackNum, control):

        #finds correct track object based on naming convention #
        clTrack = next((track for track in self.clip_tracks if track.trackNum == requestedTrackNum), None)
        #self.__parent.send_message("requested " + str(requestedTrackNum) + " clip tracks len: " + str(len(self.clip_tracks)))

        if control == RECORD_CONTROL:
            clTrack.onRecordPressed()

        elif control == STOP_CONTROL:
            clTrack.onStopPressed()

        elif control == UNDO_CONTROL:
            clTrack.onUndoPressed()

        elif control == CLEAR_CONTROL:
            clTrack.onClearPressed()

