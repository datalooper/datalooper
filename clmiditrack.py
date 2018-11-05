import cltrack
from consts import *


class ClMidiTrack(cltrack.ClTrack):

    def __init__(self, parent, track, trackNum, song):
        super(ClMidiTrack, self).__init__(parent, track, trackNum, song)
        self.__parent = parent
        self.song = song
        self.trackStore = []
        self.prevNotes = list()

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
        if self.clip != -1 and self.clip.is_recording:
            self.removeClip()
            self.__parent.send_message("Clearing Clip")
        else:
            self.onStopPressed()
            self.getNewClipSlot()

    def overdub(self):
        self.__parent.send_message("overdubbing")
        self.updateTrackStatus(OVERDUB_STATE)
        self.trackStore = []
        for track in self.song.tracks:
            if track.name != self.track.name and track.can_be_armed:
                self.trackStore.append(TempTrack(track.name, track.arm, track.current_monitoring_state))
                self.__parent.send_message(track.name + " " + str(track.current_monitoring_state))
                if track.arm == 1:
                    track.arm = 0
                    if track.current_monitoring_state == 1:
                        # TODO also need to check if clip is playing
                        track.current_monitoring_state = 0
        if self.clip != -1:
            self.clip.select_all_notes()
            self.prevNotes.append(self.clip.get_selected_notes())
        self.song.session_record = 1

    def undoOverdub(self):
        if len(self.prevNotes) > 0:
            self.__parent.send_message("removing overdub")
            self.clip.select_all_notes()
            self.clip.replace_selected_notes(self.prevNotes[-1])
            del self.prevNotes[-1]

    def endOverdub(self):
        self.__parent.send_message("ending overdubbing")
        self.song.session_record = 0
        self.updateTrackStatus(PLAYING_STATE)
        for track in self.song.tracks:
            if track.name != self.track.name:
                match = next((trackS for trackS in self.trackStore if track.name == trackS.name), None)
                if match is not None:
                    track.current_monitoring_state = match.current_monitoring_state
                if track.can_be_armed:
                    track.arm = match.arm


class TempTrack(object):
    def __init__(self, name, arm, current_monitoring_state):
        self.name = name
        self.arm = arm
        self.current_monitoring_state = current_monitoring_state
