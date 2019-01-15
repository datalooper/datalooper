from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface
from consts import *
from trackhandler import TrackHandler
from sysex import Sysex
from actions import Actions
from collections import defaultdict
from state import State

class DataLooper(ControlSurface):

    def __init__(self, c_instance):
        super(DataLooper, self).__init__(c_instance)
        self.__c_instance = c_instance

        # shows in Ableton footer
        self.show_message("Powered by DATA Looper")

        # listens to time changes
        self.song().add_current_song_time_listener(self.on_time_change)

        # listens to track add/remove
        self.song().add_tracks_listener(self.on_track_added_or_removed)

        self.tracks = defaultdict(list)

        self.state = State(self.song())

        # creates obj to handle actions
        self.__action_handler = Actions(self, self.tracks, self.song(), self.state)

        # creates obj to handle tracks
        self.__track_handler = TrackHandler(self, self.song(), self.tracks, self.state, self.__action_handler)

        self.__track_handler.scan_tracks()
        # initializes base obj
        self.live = Live.Application.get_application()

    def send_message(self, m):
        self.log_message(m)

    def set_bpm(self, bpm):
        self.song().tempo = bpm

    def on_track_added_or_removed(self):
        self.send_message("on track change")
        self.__track_handler.scan_tracks()

    def on_track_name_changed(self):
        self.send_message("on track name change")
        self.__track_handler.scan_tracks()

    def on_time_change(self):
        time = self.song().get_current_beats_song_time()
        if time.beats != self.state.curBeats:
            self.state.curBeats = time.beats
            looper_status_sysex = (240, 1, 2, 3, DOWNBEAT_COMMAND, 4, 0, 247)
            self.send_midi(looper_status_sysex)

    def disconnect(self):
        self.log_message("looper disconnecting")
        looper_status_sysex = (240, 1, 2, 3, 0, 4, 0, 247)
        self.send_sysex(0, ABLETON_CONNECTED_COMMAND, 0)
        super(DataLooper, self).disconnect()

    def send_midi(self, midi_event_bytes):
        self.__c_instance.send_midi(midi_event_bytes)

    def send_sysex(self, looper, control, data):
        # self.send_message("sending sysex: " + str(looper) + " : " + str(control) + " : " + str(data) )
        looper_status_sysex = (240, looper, control, 3, data, 247)
        self.send_midi(looper_status_sysex)

    def send_program_change(self, program):
        self.send_message("sending program change:" + str(program))
        looper_status_sysex = (192, program)
        self.send_midi(looper_status_sysex)

    def receive_midi(self, midi_bytes):
        if len(midi_bytes) != 3:
            self.handle_sysex(midi_bytes)

    def handle_sysex(self, midi_bytes):
        # {0xF0, 0x41, (byte) *instance, (byte) *bank, (byte) looperNum, (byte) mode, (byte) action, (byte) data1, (byte) data2, sending,  0xF7}
        # [0] : generic
        # [1] : generic
        # [2] : looper instance
        # [3] : looper bank
        # [4] : looper number
        # [5] : mode
        # [6] : action
        # [7] : data1
        # [8] : data2
        # [9] : sending
        # [10] : generic

        sysex = Sysex(midi_bytes)
        self.send_message(self.get_method(sysex.action))
        getattr(self.__action_handler, self.get_method(sysex.action))(sysex)


    def refresh_state(self):
        """Live -> Script
        Send out MIDI to completely update the attached MIDI controller.
        Will be called when requested by the user, after for example having reconnected
        the MIDI cables...
        """
        self.send_sysex(0, ABLETON_CONNECTED_COMMAND, 1)

    @staticmethod
    def get_method(argument):
        action_map = {
            0: "record",
            1: "stop",
            2: "undo",
            3: "clear",
            4: "mute_track",
            5: "new_clip",
            6: "bank",
            7: "change_instance",
            8: "record_bank",
            9: "stop_bank",
            10: "undo_bank",
            11: "clear_bank",
            12: "start_bank",
            13: "mute_bank",
            14: "record_all",
            15: "stop_all",
            16: "undo_all",
            17: "clear_all",
            18: "start_all",
            19: "mute_all",
            20: "toggle_stop_start",
            21: "stop_all_playing_clips",
            22: "mute_all_tracks_playing_clips",
            23: "create_scene",
            24: "metronome_control",
            25: "tap_tempo",
            26: "jump_to_next_bar",
            27: "change_mode",
            28: "new_clips_on_all"
        }
        return action_map.get(argument, "Invalid Action")