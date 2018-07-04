#Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
import Live
from consts import *
from _Generic.Devices import *
from math import *

class ClipHandler:
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent):
        self.__parent = parent
        self.clip_tracks = [-1] * NUM_TRACKS
        self.last_clip = -1
        self.clipSlot = [-1] * NUM_TRACKS

    def disconnect(self):
        self.__parent.disconnect()

    def clearTracks(self):
        self.clip_tracks = []

    def appendTracks(self, t):
        self.clip_tracks.append(t)

    def receive_midi_note(self, note_num):
        control = (note_num - 1) % NUM_CONTROLS
        trackNum = int((floor((note_num - 1) / NUM_CONTROLS)) % NUM_TRACKS)

        #redundant check, but wth
        if len(self.clip_tracks) > trackNum:
            self.handleClipAction(trackNum, control)

    def onClipStatusChange(self, trackNum):
        if self.clipSlot[trackNum].is_playing:
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, trackNum , 2, 247)
            self.__parent.send_midi(looper_status_sysex)

    def onClipChange(self, trackNum):

        if self.clipSlot[trackNum].has_clip:
            if self.clipSlot[trackNum].clip.is_recording:
                looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, trackNum , 1, 247)
            if not self.clipSlot[trackNum].clip.playing_status_has_listener(self.onClipChange):
                self.clipSlot[trackNum].clip.add_playing_status_listener(lambda: self.onClipStatusChange(trackNum))
        else:
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, trackNum , 4, 247)

        self.__parent.send_midi(looper_status_sysex)

    def handleClipAction(self, trackNum, control):
        track = self.clip_tracks[trackNum]
        self.__parent.send_message(trackNum)
        looper_status_sysex = -1

        if control == RECORD_CONTROL:
            self.clipSlot[trackNum] = self.findNextOpenSlot(track, trackNum)
            if not self.clipSlot[trackNum].has_clip_has_listener(self.onClipChange):
                #Clip Playing Status Listener Not Working, so we use a 'add clip listener' then bind to the clip directly. Stupid workaround.
                self.clipSlot[trackNum].add_has_clip_listener(lambda: self.onClipChange(trackNum))
            self.clipSlot[trackNum].fire()
        elif control == STOP_CONTROL:
            if self.clipSlot[trackNum] == -1:
                self.clipSlot[trackNum] = self.findPlayingClip(track)
            self.clipSlot[trackNum].stop()
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, trackNum, 0, 247)
        elif control == UNDO_CONTROL:
            if self.clipSlot[trackNum] != -1:
                self.clipSlot[trackNum].fire()

        elif control == CLEAR_CONTROL:
            if self.clipSlot[trackNum] == -1:
                self.clipSlot[trackNum] = self.findLastClip(track)
            if self.clipSlot[trackNum] != -1 and self.clipSlot[trackNum].has_clip:
                self.clipSlot[trackNum].delete_clip()

        if looper_status_sysex != -1:
            self.__parent.send_midi(looper_status_sysex)

    def findLastClip(self, track):
        for clip_slot in track.clip_slots:
            if clip_slot.has_clip:
                self.last_clip = clip_slot
            else:
                return self.last_clip
        return -1
    def findPlayingClip(self, track):
        for clip_slot in track.clip_slots:
            if clip_slot.is_playing or clip_slot.is_recording:
                return clip_slot
        return -1
    def findNextOpenSlot(self, track, trackNum):
        for clip_slot in track.clip_slots:
            if not clip_slot.has_clip or (clip_slot.has_clip and clip_slot.is_recording):
                if self.clipSlot[trackNum] != -1:
                    if self.clipSlot[trackNum] != clip_slot and self.clipSlot[trackNum].has_clip_has_listener(self.onClipChange):
                        self.__parent.send_message("removing listener")
                        self.clipSlot[trackNum].remove_has_clip_listener(self.onClipChange)
                return clip_slot
        return -1
    def __on_device_parameters_changed(self):
        self.__parent.request_rebuild_midi_map()