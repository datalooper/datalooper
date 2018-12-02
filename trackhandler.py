# Embedded file name: /Users/versonator/Jenkins/live/output/mac_64_static/Release/python-bundle/MIDI Remote Scripts/_Axiom/Encoders.py
from _Generic.Devices import *
from claudiotrack import ClAudioTrack
from clmiditrack import ClMidiTrack
from consts import *
from cltrack import ClTrack
from dltrack import DlTrack
import Live
from track import Track


class TrackHandler:
    """ Class handling looper & clip tracks """

    def __init__(self, parent, song):
        self.__parent = parent
        self.song = song
        self.tracks = []
        self.new_session_mode = False
        self.metro = -1
        self.trackStore = []
        self.tap_tempo_counter = 0
        self.new_scene = False
        self.stopAll = False
        self.bpm = self.song.tempo
        self.muted_tracks = []

        # ensures timer never gets called more than 50 times
        self.timerCounter = 0

        self.createSceneStarted = False
        self.duplicates = []
        self.tempo_change_timer = Live.Base.Timer(callback=self.execute_tempo_change, interval=1, repeat=True)
        self.createScene = Live.Base.Timer(callback=self.create_scene_callback, interval=1, repeat=False)

    def disconnect(self):
        self.__parent.disconnect()

    def clear_tracks(self):
        for track in self.tracks:
            track.remove_track()
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

    def record(self, instance=0, looper_num=0, looper=Track):
        req_track = instance * 3 + looper_num
        # check if all tracks are stopped by stop all button
        if self.stopAll:
            self.song.metronome = self.metro
            self.jump_to_next_bar(False)
            self.stopAll = False
            for track in self.tracks:
                if isinstance(track, looper) and track.trackNum == req_track:
                    track.record(False)
        else:
            for track in self.tracks:
                if isinstance(track, looper) and track.trackNum == req_track:
                    track.record(True)

    def stop(self, instance=0, looper_num=0):
        self.send_message("stop")
        for track in self.get_track(instance, looper_num):
            track.stop(True)

    def undo(self, instance=0, looper_num=0):
        for track in self.get_track(instance, looper_num):
            track.undo()
        self.send_message("undo")

    def clear(self, instance=0, looper_num=0):
        for track in self.get_track(instance, looper_num):
            track.clear()
        self.send_message("clear")

    def clear_all(self, instance=0, looper_num=0):
        self.send_message("clearing all")
        if not self.new_session_mode and not self.check_uniform_state([CLEAR_STATE]):
            self.new_scene = True
            for track in self.tracks:
                if isinstance(track, ClTrack):
                    track.getNewClipSlot()
                    track.stop(False)
                else:
                    track.clear()
            self.new_scene = False

    def toggle_start_stop_all(self, instance=0, looper_num=0):
        if not self.new_session_mode and not self.check_uniform_state([CLEAR_STATE]):
            # if all loopers are stopped or clear, start all
            if self.check_uniform_state([STOP_STATE, CLEAR_STATE]):
                self.start_all()
            else:
                self.stop_all()

    def start_all(self):
        self.jump_to_next_bar(True)
        self.song.metronome = self.metro
        self.metro = -1
        self.stopAll = False
        for track in self.tracks:
            track.play(False)

    def stop_all(self):
        self.metro = self.song.metronome
        self.stopAll = True
        self.song.metronome = 0
        for track in self.tracks:
            if track.lastState == PLAYING_STATE:
                track.stop(False)

    def check_uniform_state(self, state):
        for track in self.tracks:
            # self.send_message("track " + str(track.trackNum) + " State:" + str(track.lastState))
            if track.lastState not in state:
                return False
        return True

    def mute_all(self, instance=0, looper_num=0):
        if not self.new_session_mode:
            for track in self.tracks:
                if track.track.mute == 1:
                    track.track.mute = 0
                else:
                    track.track.mute = 1
            self.send_message("mute all")

    def enter_new_session(self, instance=0, looper_num=0):
        self.new_session_mode = True
        self.stopAll = False
        self.send_message("New session")
        self.send_sysex(0, 4, 1)
        if self.metro == -1:
            self.metro = self.song.metronome
        self.song.metronome = 0
        self.tap_tempo_counter = 0
        self.toggle_new_session()

    def exit_new_session(self, instance=0, looper_num=0):
        if self.new_session_mode:
            self.new_session_mode = False
            self.send_message("exiting new session mode")
            self.send_sysex(0, 4, 0)
            self.song.metronome = self.metro
            self.toggle_new_session()

    def toggle_new_session(self):
        for track in self.tracks:
            if isinstance(track, DlTrack):
                track.toggle_new_session_mode(self.new_session_mode)

    def send_sysex(self, looper, control, data):
        self.__parent.send_sysex(looper, control, data)

    def set_bpm(self, bpm):
        self.__parent.set_bpm(bpm)

    def enter_config(self, instance=0, looper_num=0):
        self.send_message("Config toggled")
        self.send_sysex(0, 5, 0)

    def record_looper(self, instance=0, looper_num=0):
        self.send_message("in record looper")
        self.record(instance, looper_num, DlTrack)

    def record_clip(self, instance=0, looper_num=0):
        self.send_message("in record clip")
        if not self.new_session_mode:
            self.record(instance, looper_num, ClTrack)

    def find_last_slot(self):
        index = []
        for cl_track in self.tracks:
            if isinstance(cl_track, ClTrack):
                index.append(cl_track.find_last_slot())
        return max(index)

    def jump_to_next_bar(self, changeBPM):
        rec_flag = self.song.record_mode
        time = int(self.song.current_song_time) + (self.song.signature_denominator - (
                int(self.song.current_song_time) % self.song.signature_denominator))
        self.send_message("current time:" + str(self.song.current_song_time) + "time: " + str(time))
        self.bpm = self.song.tempo
        self.song.current_song_time = time
        self.song.record_mode = rec_flag
        if changeBPM:
            self.timerCounter = 0
            self.tempo_change_timer.start()

    def execute_tempo_change(self):
        # kills timer after 50ms just in case it wants to run forever for some reason
        self.timerCounter += 1
        if self.song.tempo != self.bpm:
            self.song.tempo = self.bpm
            self.tempo_change_timer.stop()
        elif self.timerCounter > 50:
            self.tempo_change_timer.stop()

    def exit_config(self, instance=0, looper_num=0):
        self.send_message("exiting config")
        self.exit_new_session(instance, looper_num)

    def change_instance(self, instance=0, looper_num=0):
        self.send_message("changing instance to " + str(instance))

        self.reset_state(instance)

        new_tracks = [loop_track for loop_track in self.tracks if
                      instance * 3 <= loop_track.trackNum < instance * 3 + NUM_TRACKS]
        for loop_track in new_tracks:
            # for each new track, check if any other tracks match the input routing and disarm
            if isinstance(loop_track, ClTrack):
                for alt_track in self.tracks:
                    if isinstance(alt_track,
                                  ClTrack) and alt_track not in new_tracks and alt_track.track.current_input_routing == loop_track.track.current_input_routing:
                        alt_track.track.arm = 0
                loop_track.track.arm = 1
            self.send_sysex(loop_track.trackNum, CHANGE_STATE_COMMAND, loop_track.lastState)

    def reset_state(self, instance):
        i = 0
        while i < NUM_TRACKS:
            self.send_sysex(instance * NUM_TRACKS + i, CHANGE_STATE_COMMAND, CLEAR_STATE)
            i += 1

    def bank(self, instance=0, looper_num=0):
        self.__parent.send_program_change(looper_num)

    def bank_if_clear(self, instance=0, looper_num=0):
        for track in self.get_track(instance, looper_num):
            if track.lastState != CLEAR_STATE:
                return
        self.bank(instance, looper_num)

    def session_record(self, overdubbing, curTrack):
        if overdubbing:
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

    def tap_tempo(self, looper=0, instance=0):
        if self.new_session_mode:
            self.song.tap_tempo()
            if self.tap_tempo_counter >= 3:
                self.song.metronome = self.metro
            self.tap_tempo_counter += 1

    def create_scene(self):
        if not self.createSceneStarted:
            self.createSceneStarted = True
            self.createScene.start()

    def create_scene_callback(self):
        self.song.create_scene(-1)
        self.createSceneStarted = False
        for track in self.tracks:
            if isinstance(track, ClTrack) and track.outOfScenes:
                track.outOfScenes = False
                self.new_scene = True
                track.getNewClipSlot()
        self.new_scene = False

    def delete_all(self, looper, instance):
        for track in self.tracks:
            if isinstance(track, ClTrack):
                track.delete_all()

    def mute_all_playing_clips(self, looper, instance):
        self.send_message("muting all clips, length: " + str(len(self.muted_tracks)))
        if len(self.muted_tracks) == 0:
            for track in self.song.tracks:
                if track.playing_slot_index != -1:
                    self.muted_tracks.append(track)
                    track.mute = 1
        else:
            for track in self.muted_tracks:
                track.mute = 0
            self.muted_tracks = []

    def mute_bank(self, looper, instance):
        for loop_track in self.tracks:
            if instance * 3 <= loop_track.trackNum < instance * 3 + NUM_TRACKS:
                if loop_track.track.mute == 1:
                    loop_track.track.mute = 0
                else:
                    loop_track.track.mute = 1

    def mute_track(self, looper, instance):
        for track in self.get_track(instance, looper):
            if track.track.mute == 1:
                track.track.mute = 0
            elif track.lastState != CLEAR_STATE:
                track.track.mute = 1

    def stop_all_playing_clips(self, looper, instance):
        self.song.stop_all_clips()

    def turn_off_metronome(self, looper, instance):
        if self.metro != -1:
            self.metro = self.song.metronome
        self.song.metronome = 0

class TempTrack(object):
    def __init__(self, name, arm, current_monitoring_state):
        self.name = name
        self.arm = arm
        self.current_monitoring_state = current_monitoring_state
