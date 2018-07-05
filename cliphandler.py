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

    def disconnect(self):
        self.__parent.disconnect()

    def clearTracks(self):
        self.clip_tracks = []

    def appendTracks(self, track, trackNum):
        #creates track objects
        self.clip_tracks.append(ClTrack(self, track, trackNum))

    #receives midi notes from parent class
    def receive_midi_note(self, note_num):

        #maps note num to track control # (1-4) on DL Pedal
        control = (note_num - 1) % NUM_CONTROLS

        #maps note num to track # on DL pedal
        requestedTrackNum = int((floor((note_num - 1) / NUM_CONTROLS))) + 1

        #checks if the requested track number is in clip_tracks list
        if len(self.clip_tracks) > requestedTrackNum:
            self.handleClipAction(requestedTrackNum, control)

    def handleClipAction(self, requestedTrackNum, control):

        #finds correct track object based on naming convention #
        clTrack = next((track for track in self.clip_tracks if track.trackNum == requestedTrackNum), None)
        self.__parent.send_message("requested " + str(requestedTrackNum) + " clip tracks len: " + str(len(self.clip_tracks)))
        looper_status_sysex = -1

        if control == RECORD_CONTROL:
            clTrack.clipSlot = self.findNextOpenSlot(clTrack)

            #adds listener to change status led's
            if not clTrack.clipSlot.has_clip_has_listener(self.onClipChange):
                #Clip Playing Status Listener Not Working, so we use a 'add clip listener' then bind to the clip directly. Stupid workaround.
                clTrack.clipSlot.add_has_clip_listener(lambda: self.onClipChange(clTrack))
            clTrack.clipSlot.fire()
        elif control == STOP_CONTROL:
            if clTrack.clipSlot == -1:
                clTrack.clipSlot = self.findPlayingClip(clTrack)
            clTrack.clipSlot.stop()
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, clTrack.trackNum-1, 0, 247)
        elif control == UNDO_CONTROL:
            if clTrack.clipSlot != -1:
                clTrack.clipSlot.fire()

        elif control == CLEAR_CONTROL:
            if clTrack.clipSlot == -1:
                clTrack.clipSlot = self.findLastClip(clTrack)
            if clTrack.clipSlot != -1 and clTrack.clipSlot.has_clip:
                clTrack.clipSlot.delete_clip()

        if looper_status_sysex != -1:
            self.__parent.send_midi(looper_status_sysex)

    def onClipStatusChange(self, clTrack):
        if clTrack.clipSlot.is_playing:
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, clTrack.trackNum-1, 2, 247)
            self.__parent.send_midi(looper_status_sysex)

    def onClipChange(self, clTrack):

        if clTrack.clipSlot.has_clip:
            if clTrack.clipSlot.clip.is_recording:
                looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, clTrack.trackNum-1 , 1, 247)
            if not clTrack.clipSlot.clip.playing_status_has_listener(self.onClipChange):
                clTrack.clipSlot.clip.add_playing_status_listener(lambda: self.onClipStatusChange(clTrack))
        else:
            looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, clTrack.trackNum-1, 4, 247)

        self.__parent.send_midi(looper_status_sysex)

    def findLastClip(self, clTrack):
        for clipSlot in clTrack.track.clip_slots:
            if clipSlot.has_clip:
                clTrack.lastClip = clipSlot
            else:
                return clTrack.lastClip
        return -1

    def findPlayingClip(self, clTrack):
        for clip_slot in clTrack.track.clip_slots:
            if clip_slot.is_playing or clip_slot.is_recording:
                return clip_slot
        return -1
    def findNextOpenSlot(self, clTrack):
        for clip_slot in clTrack.track.clip_slots:
            if not clip_slot.has_clip or (clip_slot.has_clip and clip_slot.is_recording):
                if clTrack.clipSlot != -1:
                    if clTrack.clipSlot != clip_slot and clTrack.clipSlot.has_clip_has_listener(self.onClipChange):
                        self.__parent.send_message("removing listener")
                        clTrack.clipSlot.remove_has_clip_listener(self.onClipChange)
                return clip_slot
        return -1
    def __on_device_parameters_changed(self):
        self.__parent.request_rebuild_midi_map()