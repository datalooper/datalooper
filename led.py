from consts import *


class Led(object):
    def __init__(self, parent, ledNumber):
        self.ledNumber = ledNumber
        self.__parent = parent

    def link_led(self, ledNumber):
        self.ledNumber = ledNumber

    def update_state(self, *data):
        if self.ledNumber != -1:
            self.__parent.send_sysex(CHANGE_STATE_COMMAND, self.ledNumber, *data)


