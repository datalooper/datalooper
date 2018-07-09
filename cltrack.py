from consts import *


class ClTrack(object):
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent, track, trackNum):
        self.__parent = parent
        self.clipSlot = -1
        self.lastClip = -1
        self.track = track
        self.trackNum = trackNum
        self.state = -1
        self.clip = -1

    def onStopPressed(self):
        self.__parent.send_message("Stopping Clip")
        if self.clipSlot == -1:
                self.clipSlot = self.findPlayingClip()
        self.clipSlot.stop()

    def updateTrackStatus(self, status):
        sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, self.trackNum - 1, status, 247)
        self.__parent.send_midi(sysex)

    def fireClip(self):
        if self.clipSlot != -1:
            self.clipSlot.fire()
        else:
            self.__parent.send_message("No Clip Slot Loaded, Cannot fire Clip")

    # manages clip listeners and loads the first empty clip slot location into memory
    def getNewClipSlot(self):
        if self.clipSlot != -1:
            if self.clipSlot.has_clip_has_listener(self.onClipChange):
                self.clipSlot.remove_has_clip_listener(self.onClipChange)
            self.clipSlot = -1
        for clip_slot in self.track.clip_slots:
            if not clip_slot.has_clip:
                self.clipSlot = clip_slot
                self.clipSlot.add_has_clip_listener(self.onClipChange)
                return

    # called when a clip shows up or is removed from a clip slot
    def onClipChange(self):

        if self.clipSlot.has_clip:
            self.clip = self.clipSlot.clip
            if self.clipSlot.clip.is_recording:
                self.updateTrackStatus(RECORDING_STATE)
            if not self.clipSlot.clip.playing_status_has_listener(self.onClipChange):
                self.clipSlot.clip.add_playing_status_listener(self.onClipStatusChange)
        else:
            self.updateTrackStatus(CLEAR_STATE)


    def onClipStatusChange(self):
        if self.clipSlot.is_playing:
            self.updateTrackStatus(PLAYING_STATE)
        elif not self.clipSlot.is_playing and not self.clipSlot.is_recording:
            self.updateTrackStatus(STOP_STATE)



