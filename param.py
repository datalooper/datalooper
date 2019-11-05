import Live

class Param:
    def __init__(self, parent, param, song):
        self.param = param
        self.parent = parent
        param.add_value_listener(self.on_param_changed)
        self.value = -999
        self.song = song
        self.is_first_record = True
        self.timer = Live.Base.Timer(callback=self.timer_callback, interval=1, repeat=False)
        self.value_timer = Live.Base.Timer(callback=self.value_timer_callback, interval=1, repeat=False)

        song.add_record_mode_listener(self.on_record_mode_changed)

    def on_param_changed(self):
        if self.song.record_mode:
            self.value = self.param.value

    def on_record_mode_changed(self):
        if self.song.record_mode == 0 and self.value != -999:
            if self.value != self.param.value:
                self.value_timer.start()
            elif self.is_first_record:
                self.timer.start()
                self.is_first_record = False
        elif self.song.record_mode and self.value != -999:
            self.value = self.param.value
            self.timer.start()

    def timer_callback(self):
        self.parent.send_message("resetting param to min then value")
        self.param.value = self.param.min
        self.param.value = self.value

    def value_timer_callback(self):
        self.param.value = self.value