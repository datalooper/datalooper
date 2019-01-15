class Sysex:
    def __init__(self, midi_bytes):
        self.instance = midi_bytes[2]
        self.bank = midi_bytes[3]
        self.looper_num = midi_bytes[4]
        self.mode = midi_bytes[5]
        self.action = midi_bytes[6]
        self.data1 = midi_bytes[7]
        self.data2 = midi_bytes[8]
