from consts import *


class Scene:
    def __init__(self, sceneNum, buttonNum, song, state, parent):
        self.sceneNum = sceneNum
        self.buttonNum = buttonNum
        self.song = song
        self.state = state
        self.__parent = parent
        self.init_listener()

    def init_listener(self):
        if not self.song.scenes[self.sceneNum].color_has_listener(self.on_color_change):
            self.song.scenes[self.sceneNum].add_color_listener(self.on_color_change)
        else:
            self.__parent.send_message("listener already added")
        self.update_color()

    def request_state(self):
        self.update_color()

    def on_color_change(self):
        self.update_color()

    def update_color(self):
        if self.state.mode == LOOPER_MODE :
            carray = self.__parent.get_color_array(self.song.scenes[self.sceneNum].color)
            self.__parent.send_sysex(CLIP_COLOR_COMMAND, self.buttonNum, carray[0], carray[1], carray[2], carray[3],carray[4], carray[5])

    def remove(self):
        if self.song.scenes[self.sceneNum].color_has_listener(self.on_color_change):
            self.song.scenes[self.sceneNum].remove_color_listener(self.on_color_change)