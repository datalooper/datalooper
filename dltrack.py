from consts import *


class DlTrack:
    """ Class handling looper track from DataLooper """

    def __init__(self, parent, track, device, trackNum):
        self.__parent = parent
        self.track = track
        self.device = device
        self.trackNum = trackNum
        self.state = device.parameters[1]
        self.state.add_value_listener(self._on_looper_param_changed)

    #some weird logic has to happen because Ableton doesn't differenciate between clear and stop state. We have to make an educated guess.
    def _on_looper_param_changed(self):
        self.__parent.send_message("Looper " + str(self.trackNum) + " state: " + str(self.device.parameters[1].value))
        if self.state == RECORDING_STATE and int(self.device.parameters[1].value) == STOP_STATE:
            self.state = CLEAR_STATE

        self.state = int(self.device.parameters[1].value)
        self.updateTrackStatus(self.state)

    def updateTrackStatus(self, status):
        sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, self.trackNum - 1, status, 247)
        self.__parent.send_midi(sysex)

