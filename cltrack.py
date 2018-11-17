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
        self.clip = -1
        self.clipStopping = False
        self.track.add_arm_listener(self.set_arm)
        if not track.fired_slot_index_has_listener(self.on_slot_fired):
            track.add_fired_slot_index_listener(self.on_slot_fired)

        if not track.arm:
            self.lastState = DISARMED_STATE
        else:
            self.lastState = self.getClipState()

        self.updateState(self.lastState)

    def set_arm(self):
        if super(ClTrack, self).set_arm():
            if self.track.arm:
                self.updateState(self.getClipState())
            else:
                self.updateState(DISARMED_STATE)

    # The fired slot index is kind of useless, as Ableton only sends out -1 if the slot plays from a stopped transport or if the slot plays immediately, so we scan
    # all the slots. Not the most efficient, sorry.

    def on_slot_fired(self):
        self.__parent.send_message(
            "fired on track : " + str(self.trackNum) + " slot #" + str(self.track.fired_slot_index))
        if self.clipSlot != -1 and (
                self.clipSlot.is_triggered or self.clipSlot.is_playing or self.clipSlot.is_recording or self.clipStopping == True):
            self.__parent.send_message("all good in the hood")
        else:
            # find currently playing clip_slot and link it to looper
            for clip_slot in self.track.clip_slots:
                if clip_slot.is_playing or clip_slot.is_recording:
                    self.__parent.send_message("found slot")
                    self.clipSlot = clip_slot
                    self.clip = self.clipSlot.clip
                    if not self.clipSlot.has_clip_has_listener(self.onClipChange):
                        self.clipSlot.add_has_clip_listener(self.onClipChange)
                    if not self.clip.playing_status_has_listener(self.onClipStatusChange):
                        self.clip.add_playing_status_listener(self.onClipStatusChange)
                    if clip_slot.is_playing:
                        self.updateState(PLAYING_STATE)
                    elif clip_slot.is_recording:
                        self.updateState(RECORDING_STATE)
                    return True
            return False

    def stop(self):
        if self.clip != -1:
            if self.clip.is_playing and not self.clip.is_recording:
                self.__parent.send_message("Stopping Clip")
                self.clip.stop()
                self.clipStopping = True
            elif self.clip.is_recording:
                self.removeClip()

    def removeClip(self):
        self.clipSlot.clip.remove_playing_status_listener(self.onClipStatusChange)
        self.clipSlot.remove_has_clip_listener(self.onClipChange)
        self.clipSlot.delete_clip()
        self.clipSlot = -1
        self.clip = -1
        self.updateState(CLEAR_STATE)

    def getClipState(self):
        if self.clip == -1:
            if self.track.playing_slot_index < 0:
                return CLEAR_STATE
            else:
                self.send_message("slut index:" + str(self.track.playing_slot_index))
                self.clipSlot = self.track.clip_slots[self.track.playing_slot_index]
                if self.clipSlot.clip:
                    self.clip = self.clipSlot.clip
                    if self.clip.is_recording:
                        return RECORDING_STATE
                    elif self.clip.is_playing and not self.clip.is_recording:
                        return PLAYING_STATE
                    elif not self.clip.is_playing:
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
            self.clip.remove_playing_status_listener(self.onClipStatusChange)
        if self.clipSlot.has_clip:
            self.clip = self.clipSlot.clip
            if self.clipSlot.clip.is_recording:
                self.updateState(RECORDING_STATE)
            if not self.clipSlot.clip.playing_status_has_listener(self.onClipStatusChange):
                self.clipSlot.clip.add_playing_status_listener(self.onClipStatusChange)
        elif not self.clipSlot.has_clip:
            self.__parent.send_message("Clear State")
            self.updateState(CLEAR_STATE)
            self.checkActiveClip()

    def onClipStatusChange(self):
        if self.clipSlot.is_playing:
            self.updateState(PLAYING_STATE)
        elif not self.clipSlot.is_playing and not self.clipSlot.is_recording:
            if self.clipSlot.has_clip and self.clipStopping:
                self.updateState(STOP_STATE)
                self.clipStopping = False
            else:
                self.updateState(CLEAR_STATE)
                self.getNewClipSlot()
