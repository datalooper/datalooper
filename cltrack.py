from consts import *
from track import Track


class ClTrack(Track):
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent, track, trackNum, song):
        super(ClTrack, self).__init__(parent, track, trackNum, song)
        self.__parent = parent
        self.clipSlot = -1
        self.lastClip = -1
        self.state = -1
        self.clipStopping = False
        self.track.add_arm_listener(self.set_arm)

        if not track.fired_slot_index_has_listener(self.on_slot_fired):
            track.add_fired_slot_index_listener(self.on_slot_fired)

        self.lastState = self.check_clip_slot_state()

        self.updateState(self.lastState)

    def set_arm(self):
        if self.track.arm:
            self.updateState(self.check_clip_slot_state())
        else:
            self.updateState(DISARMED_STATE)

    def on_slot_fired(self):
        # self.__parent.send_message(
        #     "fired on track : " + str(self.trackNum) + " slot #" + str(self.track.fired_slot_index))
        if self.track.fired_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.fired_slot_index]
            self.add_listeners()

    def add_listeners(self):
        if not self.clipSlot.has_clip_has_listener(self.onClipChange):
            self.clipSlot.add_has_clip_listener(self.onClipChange)
        if self.clipSlot.has_clip and not self.clipSlot.clip.playing_status_has_listener(self.onClipStatusChange):
            self.clipSlot.clip.add_playing_status_listener(self.onClipStatusChange)

    def stop(self):
        if self.clipSlot != -1 and self.clipSlot.has_clip:
            if self.clipSlot.clip.is_playing and not self.clipSlot.clip.is_recording:
                self.__parent.send_message("Stopping Clip")
                self.clipSlot.clip.stop()
                self.clipStopping = True
            elif self.clipSlot.clip.is_recording:
                self.removeClip()
        elif self.track.playing_slot_index > 0:
            self.track.clip_slots[self.track.playing_slot_index].stop()

    def toggle_playback(self):
        if self.clipSlot != -1 and self.clipSlot.has_clip:
            if self.clipSlot.clip.is_playing and not self.clipSlot.clip.is_recording:
                self.__parent.send_message("Stopping Clip")
                self.clipStopping = True
                self.clipSlot.clip.stop()
            elif not self.clipSlot.clip.is_playing:
                self.clipSlot.clip.fire()

    def removeClip(self):
        self.clipSlot.clip.remove_playing_status_listener(self.onClipStatusChange)
        self.clipSlot.remove_has_clip_listener(self.onClipChange)
        self.clipSlot.delete_clip()
        self.clipSlot = -1
        self.updateState(CLEAR_STATE)

    def check_clip_slot_state(self):
        self.__parent.send_message("Track: " + str(self.trackNum) + " Clip slot: " + str(self.clipSlot) + " Playing Slot Index: " + str(self.track.playing_slot_index) + " Firing Slot: " + str(self.track.fired_slot_index) )
        if self.clipSlot == -1 and self.track.playing_slot_index < 0:
            return CLEAR_STATE
        elif self.clipSlot == -1 and self.track.playing_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.playing_slot_index]
            self.add_listeners()
        elif self.clipSlot == -1 and self.track.fired_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.fired_slot_index]
        return self.check_clip_state()

    def check_clip_state(self):
        if self.clipSlot.has_clip:
            if self.clipSlot.clip.is_recording:
                return RECORDING_STATE
            elif self.clipSlot.clip.is_playing and not self.clipSlot.clip.is_recording:
                return PLAYING_STATE
            elif not self.clipSlot.clip.is_playing:
                return STOP_STATE
        else:
            return CLEAR_STATE

    def fireClip(self):
        if self.clipSlot != -1:
            self.clipSlot.fire()
        else:
            self.__parent.send_message("No Clip Slot Loaded, Cannot fire Clip")

    # manages clip listeners and loads the first empty clip slot location into memory
    def getNewClipSlot(self):
        self.__parent.send_message("Getting New Clip")
        if self.clipSlot != -1:
            if self.clipSlot.has_clip_has_listener(self.onClipChange):
                self.clipSlot.remove_has_clip_listener(self.onClipChange)
            self.clipSlot = -1

        for clip_slot in self.track.clip_slots:
            if not clip_slot.has_clip:
                self.clipSlot = clip_slot
                self.clip = -1
                if not self.clipSlot.has_clip_has_listener(self.onClipChange):
                    self.clipSlot.add_has_clip_listener(self.onClipChange)
                self.updateState(CLEAR_STATE)
                return

    def checkActiveClip(self):
        self.clipSlot = -1
        if not self.on_slot_fired():
            self.getNewClipSlot()

    # called when a clip shows up or is removed from a clip slot
    def onClipChange(self):
        self.__parent.send_message("On Clip Change State")
        if self.clipSlot != -1 and self.clipSlot.has_clip and self.clipSlot.clip.playing_status_has_listener(
                self.onClipStatusChange):
            self.clipSlot.clip.remove_playing_status_listener(self.onClipStatusChange)
        if self.clipSlot.has_clip:
            if self.clipSlot.clip.is_recording:
                self.updateState(RECORDING_STATE)
            if not self.clipSlot.clip.playing_status_has_listener(self.onClipStatusChange):
                self.clipSlot.clip.add_playing_status_listener(self.onClipStatusChange)
        else:
            self.updateState(CLEAR_STATE)
            self.checkActiveClip()

    def onClipStatusChange(self):
        self.__parent.send_message("On Clip Status Change State")

        if self.track.playing_slot_index > 0 and self.track.clip_slots[self.track.playing_slot_index] == self.clipSlot:
            if self.clipSlot.is_playing:
                self.updateState(PLAYING_STATE)
            elif not self.clipSlot.is_playing and not self.clipSlot.is_recording and not self.clipSlot.is_triggered:
                if self.clipSlot.has_clip and self.clipStopping:
                    self.updateState(STOP_STATE)
                    self.clipStopping = False
                else:
                    self.updateState(CLEAR_STATE)
                    self.getNewClipSlot()
        elif self.track.playing_slot_index > 0:
            self.clipSlot = self.track.clip_slots[self.track.playing_slot_index]
            self.updateState(self.check_clip_state())
            self.add_listeners()

    def updateState(self, state):
        self.__parent.send_message("updating state: " + str(state) + " Tracknum: " + str(self.trackNum))
        if self.track.can_be_armed and not self.track.arm:
            super(ClTrack, self).updateState(DISARMED_STATE)
        else:
            super(ClTrack, self).updateState(state)
