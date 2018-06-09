from __future__ import with_statement
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.DeviceComponent import DeviceComponent
from _Framework.MixerComponent import MixerComponent # Class encompassing several channel strips to form a mixer
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from _Framework.InputControlElement import *
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.SessionComponent import SessionComponent
from _Framework.EncoderElement import *
from Launchpad.ConfigurableButtonElement import ConfigurableButtonElement
from consts import *

class looper(ControlSurface):

	def __init__(self, c_instance):
		super(looper, self).__init__(c_instance)
		self.__c_instance = c_instance
		global looperParams
		global paramListeners
		global param_values
		global cur_beat
		global live
		#changes with multiple loopers, 1 = 1,2,3; 2 = 4,5,6; 3 = 7,8,9...etc
		paramListeners = []
		looperParams = []
		tracks = self.song().tracks
		live = Live.Application.get_application()
		self.declare_constants()
		self.cur_beat = 0
		#Detects tracks with 'looper' in the title and listens for param changes
		for t in tracks:
			stringPos = t.name.find('DL#')
			if stringPos != -1:
				if(isinstance(t.name[stringPos+4 : stringPos+5], int)):
					loopNum = int(t.name[ stringPos+3 : stringPos+5])
				else:
					loopNum = int(t.name[ stringPos+3 : stringPos+4])
				if(t.devices):
					for device in t.devices:
						if device.name == "Looper":
							state = device.parameters[1]
							looperParams.append(device.parameters[1])
							state.add_value_listener(self._on_looper_param_changed)
						else:
							self.log_message("Looper Device Does Not Exist on Track: " + t.name)
		self.show_message("Powered by DATA Looper")
		self.song().add_current_song_time_listener(self.on_time_change)

	def declare_constants(self):
		global RESET_COMMAND
		global CHANGE_STATE_COMMAND
		global DOWNBEAT_COMMAND
		RESET_COMMAND = 0
		CHANGE_STATE_COMMAND = 1
		DOWNBEAT_COMMAND = 2

	def on_time_change(self):
		song = live.get_document()
		time = song.get_current_beats_song_time()
		tempo = song.tempo
		status = 'playing' if song.is_playing else 'stopped'

		if time.beats != self.cur_beat :
			self.cur_beat = time.beats
			looper_status_sysex = (240, 1, 2, 3, DOWNBEAT_COMMAND, 4, 0,247)
			self.send_midi(looper_status_sysex)


	def _on_looper_param_changed(self):
		for index, p in enumerate(looperParams):
			self.log_message("Looper " + str(index) + " state: " + str(p.value))
			looper_status_sysex = (240, 1, 2, 3, CHANGE_STATE_COMMAND, int(index), int(p.value),247)
			self.send_midi(looper_status_sysex)

	def send_midi(self, midi_event_bytes):
		self.__c_instance.send_midi(midi_event_bytes)
	def _mode1(self):
		self.show_message("_mode1 is active")


	def _set_active_mode(self):
		global active_mode
		# activate mode
		if active_mode == "_mode1":
			self._mode1()
		if hasattr(self, '_set_track_select_led'):
			self._set_track_select_led()
		if hasattr(self, '_turn_on_device_select_leds'):
			self._turn_off_device_select_leds()
			self._turn_on_device_select_leds()
		if hasattr(self, '_all_prev_device_leds'):
			self._all_prev_device_leds()
		if hasattr(self, '_all_nxt_device_leds'):
			self._all_nxt_device_leds()
		if hasattr(self, 'update_all_ab_select_LEDs'):
			self.update_all_ab_select_LEDs(1)

	def _remove_active_mode(self):
		global active_mode
		# remove activate mode
		if active_mode == "_mode1":
			self._remove_mode1()

	def _activate_mode1(self,value):
		global active_mode
		global shift_previous_is_active
		if value > 0:
			shift_previous_is_active = "off"
			self._remove_active_mode()
			active_mode = "_mode1"
			self._set_active_mode()

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
