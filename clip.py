from consts import *


class Clip:
    def __init__(self, trackNum, sceneNum, buttonNum, song, state, parent):
        self.trackNum = trackNum
        self.sceneNum = sceneNum
        self.buttonNum = buttonNum
        self.song = song
        self.state = state
        self.__parent = parent
        self.init_listener()

    def init_listener(self):
        if self.state.mode == CLIP_LAUNCH_MODE:
            trackNum = self.trackNum + self.state.trackOffset
            sceneNum = self.sceneNum + self.state.sceneOffset
        else:
            trackNum = self.trackNum
            sceneNum = self.sceneNum

        if not self.song.tracks[trackNum].clip_slots[sceneNum].clip.color_has_listener(self.on_color_change):
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
        if self.state.mode == CLIP_LAUNCH_MODE:
            trackNum = self.trackNum + self.state.trackOffset
            sceneNum = self.sceneNum + self.state.sceneOffset
        else:
            trackNum = self.trackNum
            sceneNum = self.sceneNum

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
