from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import *
from _Framework.EncoderElement import *
from consts import *

class looper(ControlSurface):

	#variables
	looperParams = []
	paramListeners = []
	param_values = []
	cur_beat = 0

	#constants
	RESET_COMMAND = 0
	CHANGE_STATE_COMMAND = 1
	DOWNBEAT_COMMAND = 2

	def __init__(self, c_instance):
		super(looper, self).__init__(c_instance)
		self.__c_instance = c_instance
		self.show_message("Powered by DATA Looper")
		self.song().add_current_song_time_listener(self.on_time_change)
		self.song().add_tracks_listener(self.on_track_change)
		self.scan_tracks()
		self.live = Live.Application.get_application()


	#Detects tracks with 'looper' in the title and listens for param changes
	def scan_tracks(self):
		self.log_message("scanning looper tracks")
		tracks = self.song().tracks
		for t in tracks:
				stringPos = t.name.find('DL#')
				if stringPos != -1:
					#Checks for double digits
					if(isinstance(t.name[stringPos+4 : stringPos+5], int)):
						loopNum = int(t.name[ stringPos+3 : stringPos+5])
					else:
						loopNum = int(t.name[ stringPos+3 : stringPos+4])
					if not t.devices_has_listener(self.scan_tracks):
						t.add_devices_listener(self.scan_tracks)
					self.link_loopers(t)
				elif not t.name_has_listener(self.scan_tracks):
					t.add_name_listener(self.scan_tracks)
	def link_loopers(self, t):
		if(t.devices):
			for device in t.devices:
				if device.name == "Looper":
					self.log_message("found looper: " + t.name)
					state = device.parameters[1]
					self.looperParams.append(device.parameters[1])
					state.add_value_listener(self._on_looper_param_changed)
				else:
					self.log_message("Looper Device Does Not Exist on Track: " + t.name)

	def on_track_change(self):
			self.scan_tracks()
	def on_time_change(self):
		time = self.song.get_current_beats_song_time()
		status = 'playing' if song.is_playing else 'stopped'

		if time.beats != self.cur_beat :
			self.cur_beat = time.beats
			looper_status_sysex = (240, 1, 2, 3, self.DOWNBEAT_COMMAND, 4, 0,247)
			self.send_midi(looper_status_sysex)

	def _on_looper_param_changed(self):
		for index, p in enumerate(self.looperParams):
			self.log_message("Looper " + str(index) + " state: " + str(p.value))
			looper_status_sysex = (240, 1, 2, 3, self.CHANGE_STATE_COMMAND, int(index), int(p.value),247)
			self.send_midi(looper_status_sysex)

	def send_midi(self, midi_event_bytes):
		self.__c_instance.send_midi(midi_event_bytes)

	def disconnect(self):
		super(looper, self).disconnect()

	def receive_midi(self, midi_bytes):
		"""MIDI messages are only received through this function, when explicitly
        forwarded in 'build_midi_map'.
        """
		self.log_message("midi received")
		channel = midi_bytes[0] & 15
		cc_no = midi_bytes[1]
		cc_value = midi_bytes[2]
		self.log_message(channel)
		self.log_message(cc_no)
		self.log_message(cc_value)

		if cc_no == MASTER_STOP:
			if cc_value > 0:
				self.song().is_playing = False
		if midi_bytes[0] == 240 and midi_bytes[1] == 1:
			self.log_message("num received " + str(midi_bytes[7]))
			self.song().tempo = midi_bytes[6]
			self.song().signature_numerator = midi_bytes[7]
			self.song().signature_denominator = midi_bytes[8]

	def build_midi_map(self, midi_map_handle):
		"""Live -> Script
		Build DeviceParameter Mappings, that are processed in Audio time, or
		forward MIDI messages explicitly to our receive_midi_functions.
		Which means that when you are not forwarding MIDI, nor mapping parameters, you will
		never get any MIDI messages at all.
		"""
		script_handle = self.__c_instance.handle()
		self.log_message("building map")
		Live.MidiMap.forward_midi_note(script_handle, midi_map_handle, 13, MASTER_STOP)
