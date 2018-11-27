from consts import *
from track import Track


class ClTrack(Track):
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent, track, trackNum, song):
        super(ClTrack, self).__init__(parent, track, trackNum, song)
        self.__parent = parent
        self.clipSlot = -1
        self.lastClip = -1
        self.clipStopping = False
        if self.track.can_be_armed:
            self.track.add_arm_listener(self.set_arm)
        self.ignoreState = False
        if not track.fired_slot_index_has_listener(self.on_slot_fired):
            track.add_fired_slot_index_listener(self.on_slot_fired)

        self.lastState = self.check_clip_slot_state()

        self.updateState(self.lastState)

    def find_last_slot(self):
        has_clip_list = []
        for clip_slot in self.track.clip_slots:
            has_clip_list.append(clip_slot.has_clip)
        try:
            last_slot = len(has_clip_list) - 1 - has_clip_list[::-1].index(True)
        except ValueError:
            self.send_message("value error")
            last_slot = 0
        return last_slot

    def set_arm(self):
        if self.track.arm:
            self.updateState(self.check_clip_slot_state())

    def on_slot_fired(self):
        self.send_message("On slot fired: " + str(self.trackNum))
        if self.clipSlot == -1 or self.track.clip_slots[self.track.playing_slot_index] != self.clipSlot:
            for idx, clip_slot in enumerate(self.track.clip_slots):
                state = self.check_clip_state(clip_slot)
                if state != CLEAR_STATE and state != STOP_STATE and clip_slot != self.clipSlot:
                    self.send_message("adding slot: " + str(idx))
                    self.clipSlot = clip_slot
                    self.updateState(state)
                    self.add_listeners(clip_slot)

    def add_listeners(self, clip_slot):
        if not clip_slot.has_clip_has_listener(self.on_clip_change):
            clip_slot.add_has_clip_listener(self.on_clip_change)
        if clip_slot.has_clip and not clip_slot.clip.playing_status_has_listener(self.on_clip_status_change):
            clip_slot.clip.add_playing_status_listener(self.on_clip_status_change)

    def stop(self, quantized):
        if self.track.playing_slot_index >= 0:
            clip_slot = self.track.clip_slots[self.track.playing_slot_index]
            if clip_slot.clip.is_recording:
                self.removeClip()
            else:
                if self.clipSlot == clip_slot:
                    self.clipStopping = True
                clip_slot.clip.stop()

    def toggle_playback(self):
        if self.clipSlot != -1 and self.clipSlot.has_clip:
            if self.clipSlot.clip.is_playing and not self.clipSlot.clip.is_recording:
                self.__parent.send_message("Stopping Clip")
                self.clipStopping = True
                self.clipSlot.clip.stop()
            elif not self.clipSlot.clip.is_playing:
                self.clipSlot.clip.fire()

    def play(self, quantized):
        if self.clipSlot != -1 and self.clipSlot.has_clip and not self.clipSlot.clip.is_playing:
            self.clipSlot.clip.fire()

    def removeClip(self):
        if self.clipSlot.has_clip:
            self.clipSlot.clip.remove_playing_status_listener(self.on_clip_status_change)
            self.clipSlot.remove_has_clip_listener(self.on_clip_change)
            self.clipSlot.delete_clip()
        self.clipSlot = -1
        self.updateState(CLEAR_STATE)

    def check_clip_slot_state(self):
        self.__parent.send_message("Track: " + str(self.trackNum) + " Clip slot: " + str(self.clipSlot) + " Playing Slot Index: " + str(self.track.playing_slot_index) + " Firing Slot: " + str(self.track.fired_slot_index) )
        if self.clipSlot == -1 and self.track.playing_slot_index < 0:
            return CLEAR_STATE
        elif self.clipSlot == -1 and self.track.playing_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.playing_slot_index]
            self.add_listeners(self.clipSlot)
        elif self.clipSlot == -1 and self.track.fired_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.fired_slot_index]
        return self.check_clip_state(self.clipSlot)

    def check_clip_state(self, clip_slot):
        if clip_slot != -1 and clip_slot.has_clip:
            if clip_slot.clip.is_recording:
                return RECORDING_STATE
            elif clip_slot.clip.is_playing and not clip_slot.clip.is_recording:
                return PLAYING_STATE
            elif not clip_slot.clip.is_playing:
                return STOP_STATE
            else:
                return CLEAR_STATE
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
            if self.clipSlot.has_clip_has_listener(self.on_clip_change):
                self.clipSlot.remove_has_clip_listener(self.on_clip_change)
            if self.clipSlot.has_clip and self.clipSlot.clip.is_recording:
                self.clipSlot.delete_clip()
            self.clipSlot = -1
        last_slot = self.__parent.find_last_slot()
        self.send_message("last slot: " + str(last_slot))
        if not self.track.clip_slots[last_slot].has_clip and not self.__parent.new_scene:
            self.clipSlot = self.track.clip_slots[last_slot]
        else:
            self.clipSlot = self.track.clip_slots[last_slot + 1]


        if not self.clipSlot.has_clip_has_listener(self.on_clip_change):
            self.clipSlot.add_has_clip_listener(self.on_clip_change)
        self.updateState(CLEAR_STATE)

        # for clip_slot in self.track.clip_slots:
        #     if not clip_slot.has_clip:
        #         self.clipSlot = clip_slot
        #         if not self.clipSlot.has_clip_has_listener(self.on_clip_change):
        #             self.clipSlot.add_has_clip_listener(self.on_clip_change)
        #         self.updateState(CLEAR_STATE)
        #         return

    def checkActiveClip(self):
        self.clipSlot = -1
        if not self.on_slot_fired():
            self.getNewClipSlot()

    # called when a clip shows up or is removed from a clip slot
    def on_clip_change(self):
        self.__parent.send_message("On Clip Change State")
        if self.clipSlot != -1 and self.clipSlot.has_clip and self.clipSlot.clip.playing_status_has_listener(
                self.on_clip_status_change):
            self.clipSlot.clip.remove_playing_status_listener(self.on_clip_status_change)
        if self.clipSlot.has_clip:
            if self.clipSlot.clip.is_recording:
                self.updateState(RECORDING_STATE)
            if not self.clipSlot.clip.playing_status_has_listener(self.on_clip_status_change):
                self.clipSlot.clip.add_playing_status_listener(self.on_clip_status_change)
        else:
            self.updateState(CLEAR_STATE)
            self.checkActiveClip()

    def on_clip_status_change(self):
        state = self.check_clip_state(self.clipSlot)
        if state == STOP_STATE and self.clipStopping:
            self.clipStopping = False
            self.updateState(state)
        elif state == STOP_STATE and not self.clipStopping:
            state = CLEAR_STATE
            self.getNewClipSlot()
        else:
            self.updateState(state)

        self.__parent.send_message("Checking clip status on track # : " + str(self.trackNum) + " CLIP STATE: " + str(state))

    def updateState(self, state):
        self.__parent.send_message("updating state: " + str(state) + " Tracknum: " + str(self.trackNum))
        super(ClTrack, self).updateState(state)
