from consts import *
from dltrack import DlTrack
from math import *



class LooperHandler:
    """ Class handling looper triggering from DataLooper """

    def __init__(self, parent):
        self.__parent = parent
        self.looper_tracks = []

    # unregisters listeners and clears looper track list
    def clearTracks(self):
        self.looper_tracks = []
        looper_status_sysex = (240, 1, 2, 3, RESET_COMMAND, 4, 0, 247)
        self.send_midi(looper_status_sysex)

    # adds to list of track objects and manages listeners
    def appendTracks(self, track, device, trackNum, song):
        for looper in self.looper_tracks:
            if looper.track.name == track.name:
                self.__parent.send_message("Looper " + str(trackNum) + " already exists")
                return
        looperObj = DlTrack(self, track, device, trackNum, song)
        self.__parent.send_message("Looper " + str(trackNum) + " added")
        self.looper_tracks.append(looperObj)

    def mute_loops(self):
        self.__parent.send_message("muting loops")
        for looper in self.looper_tracks:
            if looper.track.mute == 1:
                looper.track.mute = 0
            else:
                looper.track.mute = 1

    def stop_all_loopers(self):
        for looper in self.looper_tracks:
            looper.onStopPressed()

    def send_message(self, message):
        self.__parent.send_message(message)

    def send_midi(self, midi):
        self.__parent.send_midi(midi)

    #receives midi notes from parent class
    def receive_midi_note(self, note_num):

        #maps note num to track control # (1-4) on DL Pedal
        control = (note_num - 1) % NUM_CONTROLS

        #maps note num to track # on DL pedal
        requestedTrackNum = int((floor((note_num - 1) / NUM_CONTROLS))) + 1

        #checks if the requested track number is in clip_tracks list

        for looperTrack in self.looper_tracks:
            if looperTrack.trackNum == requestedTrackNum:
                self.handleAction(requestedTrackNum, control)
                return
    def set_bpm(self, bpm):
        self.__parent.set_bpm(bpm)

    def handleAction(self, requestedTrackNum, control):
        #finds correct track object based on naming convention #
        loop_track = next((track for track in self.looper_tracks if track.trackNum == requestedTrackNum), None)
        #self.__parent.send_message("requested " + str(requestedTrackNum) + " clip tracks len: " + str(len(self.clip_tracks)))

        if control == RECORD_CONTROL:
            loop_track.onRecordPressed()

        elif control == STOP_CONTROL:
            loop_track.onStopPressed()

        elif control == UNDO_CONTROL:
            loop_track.onUndoPressed()

        elif control == CLEAR_CONTROL:
            loop_track.onClearPressed()
