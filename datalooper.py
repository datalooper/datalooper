from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface
from consts import *
from trackhandler import TrackHandler
from sysex import Sysex
from actions import Actions
from collections import defaultdict
from state import State
import json
import os
from _Framework.MixerComponent import MixerComponent # Class encompassing several channel strips to form a mixer
from _Framework.EncoderElement import *
from _Framework.ButtonElement import ButtonElement

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

        self.song().add_signature_numerator_listener(self.on_signature_numerator_change)

        self.tracks = defaultdict(list)

        self.state = State(self.song())

        # creates obj to handle actions
        self.__action_handler = Actions(self, self.tracks, self.song(), self.state)

        # creates obj to handle tracks
        self.__track_handler = TrackHandler(self, self.song(), self.tracks, self.state, self.__action_handler)

        self.song().add_is_playing_listener(self.on_is_playing)
        self.__track_handler.scan_tracks(True)
        # initializes base obj
        self.live = Live.Application.get_application()

        self.song().add_metronome_listener(self.on_metro_change)
        self.send_sysex(0x00, 0x01)

        # with self.component_guard():
        #     global _map_modes
        #     _map_modes = Live.MidiMap.MapMode
        #     # mixer
        #     global mixer
        #     num_tracks = 128
        #     num_returns = 24
        #     self.mixer = MixerComponent(num_tracks, num_returns)
        #     self.map_tracks()

    # def map_tracks(self):
    #     # activate mode
    #     for i in range(0, len(self.song().tracks)):
    #         self.mixer.channel_strip(i).set_volume_control(EncoderElement(MIDI_CC_TYPE, 0, i, _map_modes.absolute))
    #         self.mixer.channel_strip(i).set_pan_control(EncoderElement(MIDI_CC_TYPE, 1, i, _map_modes.absolute))
    #         send_controls = [EncoderElement(MIDI_CC_TYPE, 2, i, _map_modes.absolute), EncoderElement(MIDI_CC_TYPE, 3, i, _map_modes.absolute),
    #                          EncoderElement(MIDI_CC_TYPE, 4, i, _map_modes.absolute) ];
    #         self.mixer.channel_strip(i).set_send_controls(send_controls)
    #         self.mixer.channel_strip(i).set_send_controls(send_controls)
    #         self.mixer.channel_strip(i).set_solo_button(ButtonElement(True, MIDI_CC_TYPE, 6, i))

    def on_is_playing(self):
        if not self.song().is_playing:
            self.send_sysex(SONG_STOPPED_COMMAND);

    def on_metro_change(self):
        if not self.state.ignoreMetroCallback:
            self.state.tap_tempo_counter = 0
            self.state.ignoreMetroCallback = False

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
            self.send_sysex(DOWNBEAT_COMMAND, self.state.curBeats)

    def on_signature_numerator_change(self):
        self.send_message("numerator changed")
        self.send_midi((0xF0, 0x1E, 0x01, self.song().signature_numerator, 0xF7))

    def connect(self):
        self.log_message("looper connecting")
        self.send_sysex(0x00, 0x01)

    def disconnect(self):
        self.log_message("looper disconnecting")
        self.send_sysex(0x00, 0x00)

        super(DataLooper, self).disconnect()

    def send_midi(self, midi_event_bytes):
        self.__c_instance.send_midi(midi_event_bytes)

    def send_sysex(self, *data):
        # self.send_message("sending sysex: " + str(looper) + " : " + str(control) + " : " + str(data) )
        sysex = (0xF0, 0x1E) + data + (0xF7,)
        self.send_midi(sysex)

    def send_program_change(self, program):
        self.send_message("sending program change:" + str(program))
        looper_status_sysex = (192, program)
        self.send_midi(looper_status_sysex)

    def receive_midi(self, midi_bytes):
        # super(DataLooper,self).receive_midi(midi_bytes)
        if len(midi_bytes) != 3:
            self.handle_sysex(midi_bytes)
        else:
            self.send_message("non sysex midi received")


    def receive_midi_cc(self, cc_no, cc_value, channel):
        self.log_message(str(cc_no))

    def handle_sysex(self, midi_bytes):
        sysex = Sysex(midi_bytes)
        # self.send_message("midi action byte:")
        # self.send_message(sysex.action)
        self.send_message(self.get_method(sysex.action))
        getattr(self.__action_handler, self.get_method(sysex.action))(sysex)

    def refresh_state(self):
        """Live -> Script
        Send out MIDI to completely update the attached MIDI controller.
        Will be called when requested by the user, after for example having reconnected
        the MIDI cables...
        """
        self.send_sysex(0x00, 0x01)
        # self.send_message("refreshing state")
        super(DataLooper, self).refresh_state()

    @staticmethod
    def get_method(argument):
        action_map = {
            0: "metronome_control",
            1: "looper_control",
            2: "tap_tempo",
            3: "clip_control",
            4: "toggle_stop_start",
            5: "mute_control",
            6: "transport_control",
            7: "scene_control",
            8: "change_mode",
            9: "change_instance",
            10: "move_session_highlight",
            11: "request_state",
            12: "request_midi_map_rebuild",
            13: "unknown",
            14: "start_recording",
            15: "solo_control"
        }
        return action_map.get(argument, "Invalid Action")