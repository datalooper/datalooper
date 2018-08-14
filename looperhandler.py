from consts import *
from dltrack import DlTrack


class LooperHandler:
    """ Class handling looper triggering from DataLooper """

    def __init__(self, parent):
        self.__parent = parent
        self.looper_tracks = []

    # unregisters listeners and clears looper track list
    def clearTracks(self):
        for dlTrack in self.looper_tracks:
            dlTrack.device.parameters[1].remove_value_listener(self._on_looper_param_changed)

        self.looper_tracks = []

    # adds to list of track objects and manages listeners
    def appendTracks(self, track, device, trackNum):
        self.__parent.send_message("Looper " + str(trackNum) + " added")
        looperObj = DlTrack(self, track, device, trackNum)
        self.looper_tracks.append(looperObj)

    def mute_loops(self):
        for looper in self.looper_tracks:
            self.__parent.send_message(looper.track.mute)
            if looper.track.mute == 1:
                looper.track.mute = 0
            else:
                looper.track.mute = 1

    def stop_all_loopers(self):
        for looper in self.looper_tracks:
            looper.device.parameters[1].value = 0

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
        if len(self.looper_tracks) >= requestedTrackNum:
            self.handleClipAction(requestedTrackNum, control)

    def handleClipAction(self, requestedTrackNum, control):

        #finds correct track object based on naming convention #
        clTrack = next((track for track in self.looper_tracks if track.trackNum == requestedTrackNum), None)

        if control == RECORD_CONTROL:
            clTrack.onRecordPressed()

        elif control == STOP_CONTROL:
            clTrack.onStopPressed()

        elif control == UNDO_CONTROL:
            clTrack.onUndoPressed()

        elif control == CLEAR_CONTROL:
            clTrack.onClearPressed()