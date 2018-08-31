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
            dlTrack.clearListener()

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

