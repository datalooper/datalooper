from param import Param

class ParamTracker:
    def __init__(self, track, parent, song, trackNum):
        self.parent = parent
        self.track = track
        self.trackNum = trackNum
        self.params = []
        self.song = song
        self.build_param_store()

    def build_param_store(self):
        # self.track.mixer_device.volume.add_value_listener(self.on_volume_changed)
        # self.track.mixer_device.panning.add_value_listener(self.on_panning_changed)

        for device in self.track.devices:
            if device.class_name != "Looper":
                for param in device.parameters:
                    self.params.append(Param(self.parent, param, self.song))
        self.params.append(Param(self.parent, self.track.mixer_device.panning, self.song))
        self.params.append(Param(self.parent, self.track.mixer_device.volume, self.song))
        for send in self.track.mixer_device.sends:
            self.params.append(Param(self.parent, send, self.song))




