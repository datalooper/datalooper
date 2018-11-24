import cltrack


### Controls ###
# 1. Record : Will record a new clip
# 2. Stop : Will stop the recorded clip
# 3. Undo : Since undo is not possible, this will function as a play button
# 4. Clear : Clear will clear the current clip
#################
class ClAudioTrack(cltrack.ClTrack):
    def __init__(self, parent, track, trackNum, song):
        super(ClAudioTrack, self).__init__(parent, track, trackNum, song)
        self.__parent = parent

    ### SCENARIOS ###
    # 1. Clip is empty, recording starts
    # 2. Clip is already in memory and recording, meaning clip will play
    # 3. Clip is playing, new clip found and recording starts
    #################
    def record(self, quantized):
        self.__parent.send_message("record pressed")
        if self.clipSlot == -1 or self.clipSlot.is_playing and not self.clipSlot.is_recording:
            self.getNewClipSlot()
        if not self.clipSlot.is_playing or self.clipSlot.is_recording:
            self.fireClip()

    def clear(self):
        if self.clipSlot != -1 and self.clipSlot.has_clip:
            self.clipSlot.delete_clip()

    def undo(self):
        self.getNewClipSlot()
