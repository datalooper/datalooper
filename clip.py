from consts import *
import Live


class Clip(object):
    def __init__(self, trackNum, sceneNum, buttonNum, song, state, parent):
        self.trackNum = trackNum
        self.sceneNum = sceneNum
        self.buttonNum = buttonNum
        self.song = song
        self.state = state
        self.__parent = parent
        self.init_listener()
        self.playStatus = -1
        self.muteTimer = Live.Base.Timer(callback=self.on_mute_timer, interval=1, repeat=False)

    def init_listener(self):
        trackNum = self.trackNum
        sceneNum = self.sceneNum
        if self.state.mode == CLIP_LAUNCH_MODE:
            trackNum += self.state.trackOffset
            sceneNum += self.state.sceneOffset

        clip_slot = self.song.tracks[trackNum].clip_slots[sceneNum]
        if clip_slot.has_clip and not clip_slot.clip.color_has_listener(self.on_color_change):
            self.song.tracks[trackNum].clip_slots[sceneNum].clip.add_color_listener(self.on_color_change)
        else:
            self.__parent.send_message("listener already added")
        self.update_color()

    def request_state(self):
        self.__parent.send_message("trying to update clip state")
        self.update_color()

    def on_color_change(self):
        self.update_color()

    def update_color(self):
        trackNum = self.trackNum
        sceneNum = self.sceneNum
        if self.state.mode == CLIP_LAUNCH_MODE:
            trackNum += self.state.trackOffset
            sceneNum += self.state.sceneOffset

        self.__parent.send_message("color array update button: " + str(self.buttonNum) + " trackNum: " + str(trackNum) + " sceneNum: " + str(sceneNum))
        if len(self.song.tracks) >= trackNum :
            track = self.song.tracks[trackNum]
            if len(track.clip_slots) >= sceneNum:
                clip_slot = track.clip_slots[sceneNum]
                if clip_slot is not None and clip_slot.has_clip:
                    carray = self.__parent.get_color_array(clip_slot.clip.color)
                    if carray is not None:
                        self.__parent.send_sysex(UPDATE_BUTTON_COLOR, self.buttonNum, carray[0], carray[1], carray[2], carray[3], carray[4], carray[5])
                    else:
                        self.__parent.send_message("color array none")
                elif clip_slot is None:
                    self.__parent.send_sysex(UPDATE_BUTTON_COLOR, self.buttonNum, 0, 0, 0, 0, 0, 0)
                    self.__parent.send_message("clip slot none")
                elif not clip_slot.has_clip:
                    self.__parent.send_sysex(UPDATE_BUTTON_COLOR, self.buttonNum, 0, 0, 0, 0, 0, 0)
                    self.__parent.send_message("clip slot no clip")

    def record(self, data):
        pass

    def play(self, data):
        self.__parent.send_message("triggering clip on track : " + str(self.trackNum + self.state.trackOffset) + " clip number: " + str(self.sceneNum + self.state.sceneOffset))
        clip_slot = self.song.tracks[self.trackNum].clip_slots[self.sceneNum]
        if clip_slot.has_clip:
            self.playStatus = clip_slot.clip.is_playing
            self.__parent.send_message("playing status: " + str(clip_slot.clip.is_playing))
            if not clip_slot.clip.playing_status_has_listener(self.on_clip_play_status_changed):
                clip_slot.clip.add_playing_status_listener(self.on_clip_play_status_changed)
            clip_slot.fire()
            self.__parent.send_sysex(BLINK, self.buttonNum, BlinkTypes.FAST_BLINK)
        else:
            self.__parent.send_message("cannot play, no clip in slot")

    def stop(self, data):
        clip_slot = self.song.tracks[self.trackNum].clip_slots[self.sceneNum]
        self.__parent.send_message("stopping, data 3 = " + str(data.data3))
        if data.data3 == 1:
            clip_slot.stop()
            self.__parent.send_sysex(BLINK, self.buttonNum, BlinkTypes.FAST_BLINK)
        elif clip_slot.has_clip:
            if not clip_slot.clip.muted_has_listener(self.on_clip_muted):
                clip_slot.clip.add_muted_listener(self.on_clip_muted)
                clip_slot.clip.muted = True

    def undo(self, data):
        pass

    def clear(self, data):
        pass

    def on_clip_muted(self):
        self.muteTimer.start()

    def on_mute_timer(self):
        clip = self.song.tracks[self.trackNum].clip_slots[self.sceneNum].clip
        clip.muted = False
        clip.remove_muted_listener(self.on_clip_muted)

    def on_clip_play_status_changed(self):
        clip_slot = self.song.tracks[self.trackNum].clip_slots[self.sceneNum]
        clip = clip_slot.clip
        # if clip.playing_status_has_listener(self.on_clip_play_status_changed):
        #     clip.remove_playing_status_listener(self.on_clip_play_status_changed)
        self.__parent.send_message("is playing: " + str(clip.is_playing))

        if clip_slot.clip.is_playing != self.playStatus:
            self.playStatus = clip.is_playing
            if self.playStatus is True:
                self.__parent.send_message("slow blink")
                self.__parent.send_sysex(BLINK, self.buttonNum, BlinkTypes.SLOW_BLINK)
            elif self.playStatus is False and not clip.is_triggered:
                self.__parent.send_message("no blink")
                self.__parent.send_sysex(BLINK, self.buttonNum, BlinkTypes.NO_BLINK)
            elif self.playStatus is False and clip.is_triggered:
                self.__parent.send_sysex(BLINK, self.buttonNum, BlinkTypes.FAST_BLINK)

