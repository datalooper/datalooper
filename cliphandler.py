#Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
import Live
from consts import *
from _Generic.Devices import *
from math import *
from cltrack import ClTrack
class ClipHandler:
    """ Class handling clip triggering from DataLooper """

    def __init__(self, parent):
        self.__parent = parent
        self.clip_tracks = []
        self.last_clip = -1

    def disconnect(self):
        self.__parent.disconnect()

    def clearTracks(self):
        self.clip_tracks = []

    def appendTracks(self, track, trackNum):
        self.clip_tracks.append(ClTrack(self, track, trackNum))

    def receive_midi_note(self, note_num):
        control = (note_num - 1) % NUM_CONTROLS
        requestedTrackNum = int((floor((note_num - 1) / NUM_CONTROLS)))

        #redundant check, but wth
        if len(self.clip_tracks) > requestedTrackNum:
            self.handleClipAction(requestedTrackNum, control)

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

    def handleClipAction(self, requestedTrackNum, control):
        #finds correct track based on naming convention #
        track = next((track for track in self.clip_tracks if track.trackNum == requestedTrackNum), None)

        looper_status_sysex = -1


        if control == RECORD_CONTROL:
            track.clipSlot = self.findNextOpenSlot(track, requestedTrackNum)
            if not track.clipSlot.has_clip_has_listener(self.onClipChange):
                #Clip Playing Status Listener Not Working, so we use a 'add clip listener' then bind to the clip directly. Stupid workaround.
                track.clipSlot.add_has_clip_listener(lambda: self.onClipChange(requestedTrackNum))
            track.clipSlot.fire()
        elif control == STOP_CONTROL:
            if track.clipSlot == -1:
                track.clipSlot = self.findPlayingClip(track)
            track.clipSlot.stop()
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, requestedTrackNum, 0, 247)
        elif control == UNDO_CONTROL:
            if track.clipSlot != -1:
                track.clipSlot.fire()

        elif control == CLEAR_CONTROL:
            if track.clipSlot == -1:
                track.clipSlot = self.findLastClip(track)
            if track.clipSlot != -1 and track.clipSlot.has_clip:
                track.clipSlot.delete_clip()

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