import cltrack
import Live
from consts import *
class ClMidiTrack(cltrack.ClTrack):

    def __init__(self, parent, track, trackNum, song):
        super(ClMidiTrack, self).__init__(parent, track, trackNum)
        self.__parent = parent
        self.song = song
        self.trackStore = []

    ### SCENARIOS ###
    # 1. No clip in memory, record starts recording and a new clip is made and selected
    # 2. Clip is already in memory and playing, meaning overdubbing will begin
    # 3. Clip is already in memory and stopped, meaning clip will play
    # 4. Clip is already in memory and recording, meaning clip will play
    #################
    def onRecordPressed(self):
        self.__parent.send_message("in record pressed")

        if self.clipSlot == -1:
            self.__parent.send_message("starting recording in new slot")
            # Scenario # 1
            self.getNewClipSlot()
            self.fireClip()

        elif self.clipSlot.has_clip:
            if self.clip.is_playing and not self.clip.is_recording:
                self.__parent.send_message("going to overdub")
                self.overdub()
                # Scenario 2
            elif not self.clip.is_playing and not self.clip.is_recording:
                self.__parent.send_message("playing clip from stopped state")
                # Scenario 3
                self.fireClip()
            elif self.clip.is_recording and not self.clip.is_overdubbing:
                # Scenario 4
                self.__parent.send_message("ending recording")
                self.fireClip()
            elif self.clip.is_overdubbing:
                self.endOverdub()
        elif self.clipSlot != -1 and not self.clipSlot.has_clip:
            self.__parent.send_message("recording new clip")
            # Scenario 3
            self.fireClip()

    def onUndoPressed(self):
        self.undoOverdub()

    def onClearPressed(self):
        self.__parent.send_message("clear pressed")
        self.getNewClipSlot()

    def overdub(self):
        self.__parent.send_message("overdubbing")
        self.updateTrackStatus(OVERDUB_STATE)
        for track in self.song.tracks:
            if track.name != self.track.name:
                self.trackStore.append(TempTrack(track.name, track.arm, track.current_monitoring_state))
                if track.current_monitoring_state == 1 and track.arm == 1:
                    track.current_monitoring_state = 0
                track.arm = 0
        self.song.session_record = 1

    def undoOverdub(self):
        pass

    def endOverdub(self):
        self.__parent.send_message("ending overdubbing")
        self.song.session_record = 0
        self.updateTrackStatus(PLAYING_STATE)
        for track in self.song.tracks:
            if track.name != self.track.name:
                match = next((trackS for trackS in self.trackStore if track.name == trackS.name), None)
                track.arm = match.arm
                track.current_monitoring_state = match.current_monitoring_state

class TempTrack(object):
    def __init__(self, name, arm, current_monitoring_state):
        self.name = name
        self.arm = arm
        self.current_monitoring_state = current_monitoring_state