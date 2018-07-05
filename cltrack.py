class ClTrack:
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent, track, trackNum):
        self.__parent = parent
        self.clipSlot = -1
        self.lastClip = -1
        self.track = track
        self.trackNum = trackNum
        self.state = -1
        self.clip = -1
