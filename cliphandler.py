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
        self.clipSlotState = [-1] * NUM_TRACKS

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

    def onClipChange(self):
        self.__parent.send_message("clip status: ")
        for trackNum in range(len(self.clip_tracks)):
            if self.clipSlot[trackNum].playing_status != self.clipSlotState[trackNum]:
                self.clipSlot[trackNum].playing_status = self.clipSlotState[trackNum]
                looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, trackNum , self.clipSlotState[trackNum], 247)
                self.__parent.send_midi(looper_status_sysex)

    def handleClipAction(self, trackNum, control):
        track = self.clip_tracks[trackNum]
        self.__parent.send_message(trackNum)
        looper_status_sysex = -1

        if control == RECORD_CONTROL:
            self.clipSlot[trackNum] = self.findNextOpenSlot(track, trackNum)
            self.clipSlotState[trackNum] = self.clipSlot[trackNum].playing_status
            if not self.clipSlot[trackNum].playing_status_has_listener(self.onClipChange):
                self.__parent.send_message("adding playing status listener")
                self.clipSlot[trackNum].add_playing_status_listener(self.onClipChange)
            self.clipSlot[trackNum].fire()
        elif control == STOP_CONTROL:
            if self.clipSlot[trackNum] == -1:
                self.clipSlot[trackNum] = self.findPlayingClip(track)
            self.clipSlot[trackNum].stop()
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, trackNum, 0, 247)

        elif control == UNDO_CONTROL:
            pass

        elif control == CLEAR_CONTROL:
            if self.clipSlot[trackNum] == -1:
                self.clipSlot[trackNum] = self.findLastClip(track)
            if self.clipSlot[trackNum] != -1:
                self.clipSlot[trackNum].delete_clip()
                looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, trackNum, 0, 247)

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
                #if self.clipSlot[trackNum] != -1:
                    #if self.clipSlot[trackNum] != clip_slot and self.clipSlot[trackNum].playing_status_has_listener(self.onClipChange):
                        #self.__parent.send_message("removing listener")
                        #self.clipSlot[trackNum].remove_playing_status_listener(self.onClipChange)
                return clip_slot
        return -1
    def __on_device_parameters_changed(self):
        self.__parent.request_rebuild_midi_map()