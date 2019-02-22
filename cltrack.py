from consts import *
from track import Track
import Live


class ClTrack(Track):
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent, track, trackNum, song, state, action_handler):
        super(ClTrack, self).__init__(parent, track, trackNum, song, state, action_handler)
        self.__parent = parent
        self.clipSlot = -1
        self.lastClip = -1
        self.clipStopping = False
        self.ignoreState = False
        self.mutedClip = -1
        self.muteTimer = Live.Base.Timer(callback=self.on_mute_timer, interval=1, repeat=False)

        # add listeners
        if not track.fired_slot_index_has_listener(self.on_slot_fired):
            track.add_fired_slot_index_listener(self.on_slot_fired)

        self.lastState = self.check_clip_slot_state()

        self.update_state(self.lastState)

    ###### HELPER METHODS ######

    # manages clip listeners and loads the first empty clip slot location into memory
    def get_new_clip_slot(self, new_scene):
        self.__parent.send_message("Getting New Clip")
        # clear current clip slot
        self.remove_clip_slot()

        # find last clip slot in session that has a clip
        last_slot = self.__parent.find_last_slot()

        if not self.track.clip_slots[last_slot].has_clip and not new_scene:
            self.clipSlot = self.track.clip_slots[last_slot]
        else:
            if last_slot + 1 >= len(self.track.clip_slots):
                self.create_scene()
            else:
                self.send_message("last slot: " + str(last_slot) + " len clipslots: " + str(len(self.track.clip_slots)))
                self.clipSlot = self.track.clip_slots[last_slot + 1]

        self.add_listeners()

    def create_scene(self):
        self.song.create_scene(-1)

    def check_active_clip(self):
        self.clipSlot = -1
        if not self.on_slot_fired():
            self.get_new_clip_slot(False)

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

    def check_clip_state(self):
        if self.clipSlot != -1 and self.clipSlot.has_clip:
            if self.clipSlot.clip.is_recording:
                return RECORDING_STATE
            elif self.clipSlot.clip.is_playing and not self.clipSlot.clip.is_recording:
                return PLAYING_STATE
            elif not self.clipSlot.clip.is_playing:
                return STOP_STATE
            else:
                return CLEAR_STATE
        else:
            return CLEAR_STATE

    def check_clip_slot_state(self):

        if self.clipSlot == -1 and self.track.playing_slot_index < 0:
            return CLEAR_STATE
        # clip is playing
        elif self.clipSlot == -1 and self.track.playing_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.playing_slot_index]
            self.lastState = self.check_clip_state()
            self.add_listeners()
        # clip is fired
        elif self.clipSlot == -1 and self.track.fired_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.fired_slot_index]
            self.add_listeners()

        return self.check_clip_state()

    ###### LISTENER CALLBACKS ######

    # called when a clip shows up or is removed from a clip slot
    def on_clip_change(self):
        self.__parent.send_message("On Clip Change")
        if self.clipSlot != -1 and not self.clipSlot.has_clip:
            self.remove_clip()

    def on_clip_status_change(self):
        state = self.check_clip_state()
        if state == STOP_STATE and self.clipStopping:
            self.clipStopping = False
            self.update_state(state)
        elif state == STOP_STATE and not self.clipStopping:
            self.update_state(CLEAR_STATE)
        else:
            self.update_state(state)
        self.__parent.send_message("Clip status change on track # : " + str(self.trackNum) + " CLIP STATE: " + str(state))

    def on_slot_fired(self):
        self.send_message("On slot fired: " + str(self.trackNum) + " State: " + str(self.check_clip_state()) + " Fired Slot Index: " + str(self.track.fired_slot_index) + " Playing Slot Index" + str(self.track.playing_slot_index) )
        if (self.track.fired_slot_index >= 0 and self.clipSlot != self.track.clip_slots[self.track.fired_slot_index]) or (self.track.playing_slot_index >= 0 and self.clipSlot != self.track.clip_slots[self.track.playing_slot_index]):
            self.clipSlot = self.track.clip_slots[self.track.playing_slot_index]
            self.add_listeners()
        self.update_state(self.check_clip_state())

    def add_listeners(self):
        if self.clipSlot != -1:
            if not self.clipSlot.has_clip_has_listener(self.on_clip_change):
                self.clipSlot.add_has_clip_listener(self.on_clip_change)
            if self.clipSlot.has_clip and not self.clipSlot.clip.playing_status_has_listener(self.on_clip_status_change):
                self.clipSlot.clip.add_playing_status_listener(self.on_clip_status_change)

    def remove_listeners(self):
        if self.clipSlot != -1:
            if self.clipSlot.has_clip_has_listener(self.on_clip_change):
                self.clipSlot.remove_has_clip_listener(self.on_clip_change)
            if self.clipSlot.has_clip and self.clipSlot.clip.playing_status_has_listener(self.on_clip_status_change):
                self.clipSlot.clip.remove_playing_status_listener(self.on_clip_status_change)

    ###### ACTIONS ######

    def stop(self, quantized):
        self.send_message("stopping")
        if self.track.playing_slot_index >= 0:
            clip_slot = self.track.clip_slots[self.track.playing_slot_index]
            if clip_slot.clip.is_recording:
                self.clipSlot.delete_clip()
            if self.clipSlot == clip_slot and quantized and self.clipSlot.has_clip:
                self.clipStopping = True
                clip_slot.clip.stop()
            elif clip_slot.has_clip:
                self.send_message("muting")
                clip_slot.clip.add_muted_listener(self.clip_muted)
                clip_slot.clip.muted = True
                self.mutedClip = clip_slot.clip

    def clip_muted(self):
        self.muteTimer.start()

    def on_mute_timer(self):
        self.mutedClip.remove_muted_listener(self.clip_muted)
        self.mutedClip.muted = False
        self.mutedClip = -1

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

    def clear(self, clearType):
        self.send_message("clearing...")
        self.remove_clip()
        # if clearType == DELETE_CLIP:
        #
        # elif clearType == NEW_SCENE_KEEP_PLAYING:
        #     self.get_new_clip_slot(True)
        # elif clearType == NEW_SCENE_STOP:
        #     self.stop(False)
        #     self.get_new_clip_slot(True)
        # elif clearType == STOP_CLIP:
        #     self.stop(False)
        # self.__parent.send_message("clear pressed")
        # if self.clipSlot != -1 and self.clipSlot.has_clip:
        #     self.remove_clip()
        # self.__parent.send_message("Clearing Clip")

    def remove_clip(self):
        self.remove_listeners()
        if self.clipSlot != -1 and self.clipSlot.has_clip:
            self.clipSlot.delete_clip()
        self.get_new_clip_slot(False)

    def remove_clip_slot(self):
        if self.clipSlot != -1:
            if self.clipSlot.has_clip_has_listener(self.on_clip_change):
                self.clipSlot.remove_has_clip_listener(self.on_clip_change)
            if self.clipSlot.has_clip and self.clipSlot.clip.is_recording and not self.clipSlot.clip.is_overdubbing:
                self.clipSlot.delete_clip()
            elif self.clipSlot.has_clip and self.clipSlot.clip.is_overdubbing:
                self.clipSlot.clip.add_muted_listener(self.clip_muted)
                self.clipSlot.clip.muted = True
                self.mutedClip = self.clipSlot.clip
            self.clipSlot = -1
            self.update_state(CLEAR_STATE)

    def fire_clip(self):
        if self.clipSlot != -1:
            self.clipSlot.fire()
        else:
            self.__parent.send_message("No Clip Slot Loaded, Cannot fire Clip")

    def delete_all(self):
        for clip_slot in self.track.clip_slots:
            self.clipSlot = clip_slot
            self.remove_clip()
