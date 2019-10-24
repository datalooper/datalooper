from param import Param

class ParamTracker:
    def __init__(self, track, parent, song, trackNum):
        self.parent = parent
        self.track = track
        self.trackNum = trackNum
        self.params = []
        self.song = song
        self.build_param_store()
        self.vol_change_counter = 0
        self.volume = -999
        self.panning = -999
        self.pan_change_counter = 0
        song.add_record_mode_listener(self.on_record_mode_changed)
        self.is_first_volume = True
        self.is_first_pan = True

    def build_param_store(self):
        self.track.mixer_device.volume.add_value_listener(self.on_volume_changed)
        self.track.mixer_device.panning.add_value_listener(self.on_panning_changed)

        for device in self.track.devices:
            if device.class_name != "Looper":
                for param in device.parameters:
                    self.params.append(Param(self.parent, param, self.song))

    def on_volume_changed(self):
        if self.song.record_mode:
            self.volume = self.track.mixer_device.volume.value

    def on_panning_changed(self):
        if self.song.record_mode:
            self.panning = self.track.mixer_device.panning.value

    def on_record_mode_changed(self):
        if self.song.record_mode == 0:
            if self.volume != -999 and (self.is_first_volume or self.volume != self.track.mixer_device.volume.value):
                self.is_first_volume = False
                self.parent.send_sysex(13, self.trackNum, int(self.volume * 127), 1)

            if self.panning != -999 and (self.is_first_pan or self.panning != self.track.mixer_device.panning.value):
                self.is_first_pan = False
                self.parent.send_sysex(13, self.trackNum, int((self.panning + 1) * 63.5), 2)



