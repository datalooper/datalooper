# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
from _Generic.Devices import *
from claudiotrack import ClAudioTrack
from clmiditrack import ClMidiTrack
from consts import *
from datalooper.cltrack import ClTrack
from dltrack import DlTrack
import Live


class TrackHandler:
    """ Class handling looper & clip tracks """

    def __init__(self, parent, song):
        self.__parent = parent
        self.song = song
        self.tracks = []
        self.new_session_mode = False
        self.metro = self.song.metronome
        self.trackStore = []
        self.taps = 0

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
                self.tracks.append(ClAudioTrack(self, track, trackNum, self.song))

    def send_midi(self, midi):
        self.__parent.send_midi(midi)

    def send_message(self, message):
        self.__parent.send_message(message)

    def get_track(self, instance, looper_num):
        req_track = instance * 3 + looper_num
        tracks = []
        for track in self.tracks:
            if track.trackNum == req_track:
                tracks.append(track)
        return tracks

    def record(self, instance, looper_num, looper):
        self.send_message("recording")
        req_track = instance * 3 + looper_num
        self.stopAll = True
        for track in self.tracks:
            if isinstance(track, looper) and track.trackNum == req_track:
                track.record()

    def stop(self, instance, looper_num):
        self.send_message("stop")
        for track in self.get_track(instance, looper_num):
            track.stop(True)

    def undo(self, instance, looper_num):
        for track in self.get_track(instance, looper_num):
            track.undo()
        self.send_message("undo")

    def clear(self, instance, looper_num):
        for track in self.get_track(instance, looper_num):
            track.clear()
        self.send_message("clear")

    def clear_all(self, instance, looper_num):
        if not self.new_session_mode:
            for track in self.tracks:
<<<<<<< HEAD
                track.clear()
        self.send_message("clear all")
=======
                if isinstance(track, ClTrack):
                    track.getNewClipSlot()
                    track.stop(False)
                else:
                    track.clear()
        self.send_message("clear all")

    def toggle_start_stop_all(self, instance, looper_num):
        if not self.new_session_mode and not self.check_uniform_state([CLEAR_STATE]):
            if self.check_uniform_state([STOP_STATE, CLEAR_STATE]):
                self.jump_to_next_bar(instance, looper_num)
                self.song.metronome = self.metro
                for track in self.tracks:
                    track.play(False)
            else:
                self.metro = self.song.metronome
                self.song.metronome = 0
                for track in self.tracks:
                    track.stop(False)
>>>>>>> 4bd5a188f69dc0b9287a6a0fe3130311a326c026

    def check_uniform_state(self, state):
        for track in self.tracks:
            self.send_message("track " + str(track.trackNum) + " State:" + str(track.lastState))
            if track.lastState not in state:
                return False
        return True

    def mute_all(self, instance, looper_num):
        if not self.new_session_mode:
            for track in self.tracks:
                if track.track.mute == 1:
                    track.track.mute = 0
                else:
                    track.track.mute = 1
            self.send_message("mute all")

    def new_session(self, instance, looper_num):
        self.send_message("New session")
        self.new_session_mode = not self.new_session_mode
        self.toggle_new_session()


    def exit_new_session(self, instance, looper_num):
        if self.new_session_mode:
            self.new_session_mode = False
            self.toggle_new_session()

    def toggle_new_session(self):
        if self.new_session_mode:
            self.send_sysex(0, 4, 1)
            self.metro = self.song.metronome
            self.song.metronome = 0
            self.taps = 0
        else:
            self.send_sysex(0, 4, 0)
            self.song.metronome = self.metro
        for track in self.tracks:
            track.toggle_new_session_mode(self.new_session_mode)

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def set_bpm(self, bpm):
        self.__parent.set_bpm(bpm)

    def enter_config(self, instance, looper_num):
        self.send_message("Config toggled")
        self.send_sysex(0, 5, 0)

    def record_looper(self, instance, looper_num):
        self.record(instance, looper_num, DlTrack)

    def record_clip(self, instance, looper_num):
        if not self.new_session_mode:
            self.record(instance, looper_num, ClTrack)

    def find_last_slot(self):
        index = []
        for cl_track in self.tracks:
            if isinstance(cl_track, ClTrack):
                index.append(cl_track.find_last_slot())
        return max(index)

    def jump_to_next_bar(self, instance, looper_num):
        rec_flag = self.song.record_mode
        time = int(self.song.current_song_time) + (self.song.signature_denominator - (
                    int(self.song.current_song_time) % self.song.signature_denominator))
        self.send_message("current time:" + str(self.song.current_song_time) + "time: " + str(time))
        self.song.current_song_time = time
        self.song.record_mode = rec_flag

    def exit_config(self, instance, looper_num):
<<<<<<< HEAD
=======
        self.send_message("exiting config")
>>>>>>> 4bd5a188f69dc0b9287a6a0fe3130311a326c026
        self.exit_new_session(instance, looper_num)

    def change_instance(self, instance, looper_num):
        self.send_message("changing instance to " + str(instance))
<<<<<<< HEAD
        for track in self.tracks:
            if instance * 3 <= track.trackNum <= instance * 3 + NUM_TRACKS:
                self.send_sysex(track.trackNum, CHANGE_STATE_COMMAND, track.lastState)

    def bank(self, instance, looper_num):
        self.__parent.send_program_change(looper_num )
=======
        i = 0
        while i < NUM_TRACKS:
            self.send_sysex(instance * NUM_TRACKS + i, CHANGE_STATE_COMMAND, CLEAR_STATE)
            i += 1
        new_tracks = [loop_track for loop_track in self.tracks if
                      instance * 3 <= loop_track.trackNum < instance * 3 + NUM_TRACKS]
        for loop_track in new_tracks:
            if isinstance(loop_track, ClTrack):
                for alt_track in self.tracks:
                    if alt_track != loop_track and alt_track.track.current_input_routing == loop_track.track.current_input_routing:
                        alt_track.track.arm = 0
                loop_track.track.arm = 1
                self.send_sysex(loop_track.trackNum, CHANGE_STATE_COMMAND, loop_track.lastState)

    def bank(self, instance, looper_num):
        self.__parent.send_program_change(looper_num)

    def new_clip(self, instance, looper_num):
        for track in self.get_track(instance, looper_num):
            track.new_clip()

    def session_record(self, overdubbing, curTrack):
        if overdubbing:
            for track in self.tracks:
                track.track.remove_arm_listener(track.set_arm)
            for track in self.song.tracks:
                if track.name != curTrack.name and track.can_be_armed:
                    self.trackStore.append(TempTrack(track.name, track.arm, track.current_monitoring_state))
                    if track.arm == 1:
                        track.arm = 0
                        if track.current_monitoring_state == 1 and track.playing_slot_index == -1:
                            track.current_monitoring_state = 0
        else:
            for track in self.song.tracks:
                if track.name != curTrack.name and track.can_be_armed:
                    match = next((trackS for trackS in self.trackStore if track.name == trackS.name), None)
                    if match is not None:
                        track.current_monitoring_state = match.current_monitoring_state
                        track.arm = match.arm
            for track in self.tracks:
                track.track.add_arm_listener(track.set_arm)

    def tap_tempo(self, looper, instance):
        if self.new_session_mode:
            self.song.tap_tempo()
            if self.taps >= 3:
                self.song.metronome = self.metro
            self.taps += 1



class TempTrack(object):
    def __init__(self, name, arm, current_monitoring_state):
        self.name = name
        self.arm = arm
        self.current_monitoring_state = current_monitoring_state
>>>>>>> 4bd5a188f69dc0b9287a6a0fe3130311a326c026
