from consts import *
from dltrack import DlTrack
class LooperHandler:
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent):
        self.__parent = parent
        self.looper_tracks = []

    #unregisters listeners and clears looper track list
    def clearTracks(self):
        for dlTrack in self.looper_tracks:
            dlTrack.device.parameters[1].remove_value_listener(self._on_looper_param_changed)

        self.looper_tracks = []

    #adds to list of track objects and manages listeners
    def appendTracks(self, track, device, trackNum):
        self.__parent.send_message("Looper " + str(trackNum) + " added")
        looperObj = DlTrack(self, track, device, trackNum)
        self.looper_tracks.append(looperObj)
        state = device.parameters[1]
        state.add_value_listener(lambda : self._on_looper_param_changed(looperObj))

    def _on_looper_param_changed(self, looperObj):
        self.__parent.send_message("Looper " + str(looperObj.trackNum) + " state: " + str(looperObj.device.parameters[1].value))
        looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, looperObj.trackNum-1, int(looperObj.device.parameters[1].value),247)
        self.__parent.send_midi(looper_status_sysex)

    def mute_loops(self):
        for looper in self.looper_tracks:
            self.__parent.send_message(looper.track.mute)
            if looper.track.mute == 1:
                looper.track.mute = 0
            else:
                looper.track.mute = 1
