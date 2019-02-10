class Sysex:
    def __init__(self, midi_bytes):
        self.action = midi_bytes[2]
        self.data1 = midi_bytes[3]
        self.data2 = midi_bytes[4]
        self.data3 = midi_bytes[5]
        self.data4 = midi_bytes[6]
        self.data5 = midi_bytes[7]
