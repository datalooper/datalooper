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
        self.lastQuantization = -1
        self.muteTimer = Live.Base.Timer(callback=self.on_mute_timer, interval=1, repeat=False)
        self.fire_requested = False
        self.add_listeners()

        self.lastState = self.check_clip_slot_state()

        self.update_state(self.lastState)

    ###### HELPER METHODS ######

    # manages clip listeners and loads the first empty clip slot location into memory
    def get_new_clip_slot(self, new_scene = False):
        #self.__parent.send_message("Getting New Clip")
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
        self.send_message("adding listener from get_new_clip_slot, track #" + str(self.trackNum) + " track name: " + self.track.name)
        self.add_listeners()

    def on_quantize_disabled(self):
        if self.fire_requested:
            self.fire_clip(True)
            self.fire_requested = False

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
            #self.send_message("value error")
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
            self.send_message("adding listener from check_clip_slot_state 1")
            self.add_listeners()
        # clip is fired
        elif self.clipSlot == -1 and self.track.fired_slot_index >= 0:
            self.clipSlot = self.track.clip_slots[self.track.fired_slot_index]
            self.send_message("adding listener from check_clip_slot_state 2")
            self.add_listeners()

        return self.check_clip_state()

    ###### LISTENER CALLBACKS ######

    # called when a clip shows up or is removed from a clip slot
    def on_clip_change(self):
        #self.__parent.send_message("On Clip Change")
        if self.clipSlot != -1 and not self.clipSlot.has_clip:
            self.remove_clip()

    def on_clip_status_change(self):
        state = self.check_clip_state()
        if state == STOP_STATE and self.clipStopping:
            self.send_message("changing to stop from clip status change")
            self.clipStopping = False
            self.update_state(state)
        else:
            self.update_state(state)
        #self.__parent.send_message("Clip status change on track # : " + str(self.trackNum) + " CLIP STATE: " + str(state))

    def on_slot_fired(self):
        #self.send_message("On slot fired. Track # " + str(self.trackNum) + " Track Name: " +  self.track.name + " State: " + str(self.check_clip_state()) + " Fired Slot Index: " + str(self.track.fired_slot_index) + " Playing Slot Index" + str(self.track.playing_slot_index) )
        if (self.track.fired_slot_index >= 0 and self.clipSlot != self.track.clip_slots[self.track.fired_slot_index]) or (self.track.playing_slot_index >= 0 and self.clipSlot != self.track.clip_slots[self.track.playing_slot_index]):
            self.clipSlot = self.track.clip_slots[self.track.playing_slot_index]
            self.send_message("adding listener from on_slot_fired. track #" + str(self.trackNum) + " track name: " + self.track.name)
            self.add_listeners()
        self.update_state(self.check_clip_state())

    def add_listeners(self):
        # add listeners
        if not self.track.fired_slot_index_has_listener(self.on_slot_fired):
            self.track.add_fired_slot_index_listener(self.on_slot_fired)

        if not self.track.arm_has_listener(self.on_track_arm_change):
            self.track.add_arm_listener(self.on_track_arm_change)

        if self.clipSlot != -1:
            msg = "Adding cl listeners: "
            if not self.clipSlot.has_clip_has_listener(self.on_clip_change):
                msg += "on_clip_change, "
                self.clipSlot.add_has_clip_listener(self.on_clip_change)
            if self.clipSlot.has_clip and not self.clipSlot.clip.playing_status_has_listener(self.on_clip_status_change):
                msg += "on_clip_status_change,"
                self.clipSlot.clip.add_playing_status_listener(self.on_clip_status_change)
            msg += " on track #" + str(self.trackNum) + " with track name: " + self.track.name
            self.send_message(msg)

    def remove_track(self):
        if self.track in self.song.tracks:
            self.remove_listeners()
        else:
            self.update_state(OFF_STATE)

    def on_track_arm_change(self):
        if self.lastState != CLEAR_STATE and not self.track.arm:
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.button_num, CLEAR_STATE)
        if self.track.arm and self.clipSlot != -1 and self.clipSlot.has_clip and self.clipSlot.clip.is_playing:
            self.get_new_clip_slot(False)

    def remove_listeners(self):
        if self.track.fired_slot_index_has_listener(self.on_slot_fired):
            self.track.remove_fired_slot_index_listener(self.on_slot_fired)
        if self.track.arm_has_listener(self.on_track_arm_change):
            self.track.remove_arm_listener(self.on_track_arm_change)
        if self.clipSlot != -1:
            msg = "Removing cl listeners: "
            if self.clipSlot.has_clip_has_listener(self.on_clip_change):
                msg += "on_clip_change,"
                self.clipSlot.remove_has_clip_listener(self.on_clip_change)
            if self.clipSlot.has_clip and self.clipSlot.clip.playing_status_has_listener(self.on_clip_status_change):
                msg += " on_clip_status_change"
                self.clipSlot.clip.remove_playing_status_listener(self.on_clip_status_change)
            msg += " from track #" + str(self.trackNum) + " with track name: " + self.track.name
            self.send_message(msg)
    ###### ACTIONS ######

    def stop(self, quantized):
        if self.track and self.track.playing_slot_index >= 0:
            self.send_message("stopping clip track")
            clip_slot = self.track.clip_slots[self.track.playing_slot_index]
            if clip_slot.clip.is_recording and not clip_slot.clip.is_overdubbing:
                self.send_message("clip is recording, clearing now")
                self.clipSlot.delete_clip()
            if self.clipSlot == clip_slot and quantized and self.clipSlot.has_clip:
                if self.button_num != -1:
                    self.__parent.send_sysex(BLINK, self.button_num, BlinkTypes.FAST_BLINK)
                self.clipStopping = True
                clip_slot.clip.stop()
            elif clip_slot.has_clip:
                self.send_message("muting")
                self.clipStopping = True
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

    def play(self, quantized = True):
        if self.clipSlot != -1 and self.clipSlot.has_clip and (not self.clipSlot.clip.is_playing or self.clipSlot.clip.is_recording):
            if self.button_num != -1:
                self.__parent.send_sysex(BLINK, self.button_num, BlinkTypes.FAST_BLINK)
            self.clipSlot.clip.fire()

    def clear_immediately(self):
        super(ClTrack, self).clear_immediately()
        self.send_message("clearing...")
        self.remove_clip()

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

    def fire_clip(self, quantized):
        if self.clipSlot != -1 and quantized and not self.track.implicit_arm:
            if self.song.clip_trigger_quantization != Live.Song.Quantization.q_no_q and self.button_num != -1:
                self.__parent.send_sysex(BLINK, self.button_num, BlinkTypes.FAST_BLINK)
            self.clipSlot.fire()
        elif not quantized:
            self.action_handler.disable_quantization()
            self.fire_requested = True
        elif self.track.arm:
            self.__parent.send_message("No Clip Slot Loaded, Cannot fire Clip")

    def delete_all(self):
        for clip_slot in self.track.clip_slots:
            self.clipSlot = clip_slot
            self.remove_clip()

    def record_ignoring_state(self):
        if self.clipSlot == -1 or (self.clipSlot.has_clip and not self.clipSlot.clip.is_recording):
            self.get_new_clip_slot(False)
        elif self.clipSlot.has_clip and self.clipSlot.clip.is_recording:
            self.clipSlot.delete_clip()
        self.fire_clip(True)
