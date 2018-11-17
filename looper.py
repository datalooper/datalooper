from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *
from _Framework.EncoderElement import *
from consts import *
from trackhandler import TrackHandler
import math


class looper(ControlSurface):
    # variables
    looperParams = []
    paramListeners = []
    param_values = []
    cur_beat = 0

    def __init__(self, c_instance):
        super(looper, self).__init__(c_instance)
        self.__c_instance = c_instance
        # shows in Ableton footer
        self.show_message("Powered by DATA Looper")

        # listens to time changes
        self.song().add_current_song_time_listener(self.on_time_change)

        # listens to track add/remove
        self.song().add_tracks_listener(self.on_track_change)

        # creates obj to handle tracks
        self.__track_handler = TrackHandler(self, self.song())

        # looks for key'd tracks
        self.scan_tracks()

        # initializes base obj
        self.live = Live.Application.get_application()

        self.song().add_session_record_status_listener(self.session_status)

    def refresh_state(self):
        self.log_message("refreshing state")

    def session_status(self):
        self.log_message(str(self.song().session_record_status))

    # Detects tracks with 'looper' in the title and listens for param changes
    def scan_tracks(self):
        self.log_message("scanning looper tracks")
        # get all tracks
        tracks = self.song().tracks

        # clear CL# identified tracks
        self.__track_handler.clear_tracks()

        # iterate through all tracks
        for track in tracks:
            # check for tracks with naming convention
            for key in TRACK_KEYS:
                # checks if key exists in name
                string_pos = track.name.find(key)
                if string_pos != -1:
                    # Checks for double digits
                    if len(track.name) >= string_pos + 5 and track.name[string_pos + 4: string_pos + 5].isdigit():
                        # 0 indexed
                        track_num = int(track.name[string_pos + 3: string_pos + 5]) - 1
                    else:
                        # 0 indexed
                        track_num = int(track.name[string_pos + 3: string_pos + 4]) - 1
                    self.__track_handler.append_tracks(track, track_num, key)
                # adds name change listener to all tracks
                if not track.name_has_listener(self.scan_tracks):
                    track.add_name_listener(self.scan_tracks)

    def send_message(self, m):
        self.log_message(m)

    def set_bpm(self, bpm):
        self.song().jump_by(1-self.song().current_song_time % 1)
        self.song().tempo = bpm

    def on_track_change(self):
        self.scan_tracks()

    def on_time_change(self):
        time = self.song().get_current_beats_song_time()
        if time.beats != self.cur_beat:
            self.cur_beat = time.beats
            looper_status_sysex = (240, 1, 2, 3, DOWNBEAT_COMMAND, 4, 0, 247)
            self.send_midi(looper_status_sysex)

    def disconnect(self):
        self.log_message("looper disconnecting")
        looper_status_sysex = (240, 1, 2, 3, 0, 4, 0, 247)
        self.send_midi(looper_status_sysex)
        super(looper, self).disconnect()

    def send_midi(self, midi_event_bytes):
        self.__c_instance.send_midi(midi_event_bytes)

    def send_sysex(self, looper, control, data):
        #self.send_message("sending sysex: " + str(looper) + " : " + str(control) + " : " + str(data) )
        looper_status_sysex = (240, looper, control, 3, data, 247)
        self.send_midi(looper_status_sysex)

    def send_program_change(self, program):
        self.send_message("sending program change:" + str(program))
        looper_status_sysex = (192, program)
        self.send_midi(looper_status_sysex)

    def receive_midi(self, midi_bytes):
        """MIDI messages are only received through this function, when explicitly
        forwarded in 'build_midi_map'.
        """
        if (((midi_bytes[0] & 240) == NOTE_ON_STATUS)):
            self.receive_midi_notes(midi_bytes)
        elif (((midi_bytes[0] & 240) == CC_STATUS)):
            self.receive_midi_cc(midi_bytes)
        elif len(midi_bytes) != 3:
            self.handle_sysex(midi_bytes)

    def build_midi_map(self, midi_map_handle):
        """Live -> Script
		Build DeviceParameter Mappings, that are processed in Audio time, or
		forward MIDI messages explicitly to our receive_midi_functions.
		Which means that when you are not forwarding MIDI, nor mapping parameters, you will
		never get any MIDI messages at all.
		"""
        script_handle = self.__c_instance.handle()
        #self.log_message("building map")
        for i in range(128):
            Live.MidiMap.forward_midi_note(script_handle, midi_map_handle, CHANNEL, i)
            Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, CHANNEL, i)


    def receive_midi_notes(self, midi_bytes):
        note_num = midi_bytes[1]

    def receive_midi_cc(self, midi_bytes):
        cc_num = midi_bytes[1]

    def handle_sysex(self, midi_bytes):
        # ex: [0xF0, 0x41, looper instance, looper number, control number, 0x12, press/release/long press, long press seconds]
        # [0] : generic
        # [1] : generic
        # [2] : looper instance
        # [3] : looper number
        # [4] : control number
        # [5] : receiving (generic)
        # [6] : press/release/long press
        # [7] : long press seconds

        self.send_message("sysex received: " + str(midi_bytes))
        instance = midi_bytes[2]
        looper_num = midi_bytes[3]
        control_num = midi_bytes[4]
        action = midi_bytes[6]
        long_press_seconds = midi_bytes[7]

        data = [instance, looper_num, control_num, action, long_press_seconds]

        address_map = {
            (-1, -1, 0, 1, 0): self.__track_handler.record,
            (-1, -1, 0, 2, 1): self.__track_handler.new_clip,
            (-1, -1, 1, 1, 0): self.__track_handler.stop,
            (-1, -1, 2, 1, 0): self.__track_handler.undo,
            (-1, -1, 2, 2, 1): self.__track_handler.bank,
            (-1, -1, 1, 2, 1): self.__track_handler.clear,
            (-1, 0, 3, 1, 0): self.__track_handler.clear_all,
            (-1, 2, 3, 1, 0): self.__track_handler.toggle_start_stop_all,
            (-1, 1, 3, 0, 0): self.__track_handler.mute_all,
            (-1, 1, 3, 1, -1): self.__track_handler.mute_all,
            (-1, 0, 3, 2, 2): self.__track_handler.new_session,
            (-1, 0, 3, 2, 1): self.__track_handler.exit_new_session,
            (-1, 0, 3, 2, 5): self.__track_handler.enter_config,
            (-1, -1, -1, 3, -1): self.__track_handler.change_instance,
            (255, 255, 255, 255, 255): self.__track_handler.exit_config

        }

        needle = ()
        for keys in address_map.keys():
            for idx, key in enumerate(keys):
                if key != -1 and key != data[idx]:
                    break
                elif len(keys) - 1 == idx:
                    needle = keys

        # Get the function from switcher dictionary
        func = address_map.get(needle)
        # Execute the function
        if func is not None:
            print func(instance, looper_num)


