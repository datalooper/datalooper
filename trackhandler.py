# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
from _Generic.Devices import *
from claudiotrack import ClAudioTrack
from clmiditrack import ClMidiTrack
from consts import *
from dltrack import DlTrack


class TrackHandler:
    """ Class handling looper & clip tracks """

    def __init__(self, parent, song):
        self.__parent = parent
        self.song = song
        self.tracks = []

    def disconnect(self):
        self.__parent.disconnect()

    def clear_tracks(self):
        self.tracks = []

    def append_tracks(self, track, trackNum, track_key):
        if track_key == DATALOOPER_KEY:
            # adds a listener to tracks detected as DataLoopers to rescan for looper when a devices is added
            if not track.devices_has_listener(self.__parent.scan_tracks):
                track.add_devices_listener(self.__parent.scan_tracks)
            # checks for devices
            if track.devices:
                for device in track.devices:
                    if device.name == "Looper":
                        self.send_message("adding looper track")
                        self.tracks.append(DlTrack(self, track, device, trackNum, self.song))
                    else:
                        self.send_message("Looper Device Does Not Exist on Track: " + track.name)
        elif track_key == CLIPLOOPER_KEY:
            if track.has_midi_input:
                self.send_message("adding clip midi track")
                self.tracks.append(ClMidiTrack(self, track, trackNum, self.song))
            elif track.has_audio_input:
                self.send_message("adding clip audio track")
                self.tracks.append(ClAudioTrack(self, track, trackNum))

    def send_midi(self, midi):
        self.__parent.send_midi(midi)

    def send_message(self, message):
        self.__parent.send_message(message)

    def get_track(self, instance, looper_num):
        req_track = instance * 3 + looper_num + 1
        for track in self.tracks:
            self.send_message(str(req_track) + " :" + str(track.trackNum))
            if track.trackNum == req_track:
                return track

    def record(self, instance, looper_num):
        self.get_track(instance, looper_num).record()
        self.send_message("recording")

    def stop(self, instance, looper_num):
        self.send_message("stop")
        self.get_track(instance, looper_num).stop()

    def undo(self, instance, looper_num):
        self.get_track(instance, looper_num).undo()
        self.send_message("undo")

    def clear(self, instance, looper_num):
        self.get_track(instance, looper_num).clear()
        self.send_message("clear")

    def clear_all(self, instance, looper_num):
        self.send_message("clear all")

    def new_session(self, instance, looper_num):
        self.send_message("new session")
        pass

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)


    # def master_commands(self, datalooper_num, command):
    #     address_map = {
    #         0: stop_pressed,
    #         1: clear_pressed,
    #         2: toggle_mute
    #     }
    #     func = address_map.get(command, lambda: "Invalid Data")
    #     for track in self.tracks:
    #         print track.func(datalooper_num)

    # receives midi notes from parent class
    # def receive_midi_note(self, note_num):
    #
    #     # maps note num to track control # (1-4) on DL Pedal
    #     control = (note_num - 1) % NUM_CONTROLS
    #
    #     # maps note num to track # on DL pedal
    #     requestedTrackNum = int((floor((note_num - 1) / NUM_CONTROLS))) + 1
    #
    #     # checks if the requested track number is in clip_tracks list
    #
    #     for clipTrack in self.clip_tracks:
    #         if clipTrack.trackNum == requestedTrackNum:
    #             self.handleClipAction(requestedTrackNum, control)
    #             return

    # def handleClipAction(self, requestedTrackNum, control):
    #
    #     # finds correct track object based on naming convention #
    #     clTrack = next((track for track in self.clip_tracks if track.trackNum == requestedTrackNum), None)
    #     # self.__parent.send_message("requested " + str(requestedTrackNum) + " clip tracks len: " + str(len(self.clip_tracks)))
    #
    #     if control == RECORD_CONTROL:
    #         clTrack.onRecordPressed()
    #
    #     elif control == STOP_CONTROL:
    #         clTrack.onStopPressed()
    #
    #     elif control == UNDO_CONTROL:
    #         clTrack.onUndoPressed()
    #
    #     elif control == CLEAR_CONTROL:
    #         clTrack.onClearPressed()

    # def mute_clips(self):
    #     if len(self.clip_tracks) > 0:
    #         for clip_track in self.clip_tracks:
    #             if clip_track.track.mute == 1:
    #                 clip_track.track.mute = 0
    #             else:
    #                 clip_track.track.mute = 1
    #
    # def stop_all_clips(self):
    #     if len(self.clip_tracks) > 0:
    #         for clip_track in self.clip_tracks:
    #             clip_track.onStopPressed()
