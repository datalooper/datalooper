from claudiotrack import ClAudioTrack
from clmiditrack import ClMidiTrack
from consts import *
from dltrack import DlTrack
from collections import defaultdict


class TrackHandler:

    """ Class handling looper & clip tracks """
    def __init__(self, parent, song):
        self.__parent = parent
        self.song = song
        self.tracks = defaultdict(list)

    def disconnect(self):
        self.__parent.disconnect()

    # Detects tracks with 'looper' in the title and listens for param changes
    def scan_tracks(self):
        self.send_message("scanning for DataLooper tracks")
        # get all tracks
        tracks = self.song().tracks

        # clear CL# identified tracks
        self.clear_tracks()
        track_nums = []

        # iterate through all tracks
        for track in tracks:
            # check for tracks with naming convention
            for key in TRACK_KEYS:
                # checks if key exists in name
                string_pos = track.name.find(key)
                if string_pos != -1:
                    # Checks for double digits
                    if len(track.name) >= string_pos + 5 and track.name[string_pos + 4: string_pos + 5].isdigit():
                        track_num = int(track.name[string_pos + 3: string_pos + 5]) - 1
                    else:
                        track_num = int(track.name[string_pos + 3: string_pos + 4]) - 1
                    track_nums.append(track_num)
                    self.append_tracks(track, track_num, key)
            # adds name change listener to all tracks
            if not track.name_has_listener(self.scan_tracks):
                track.add_name_listener(self.scan_tracks)
        self.clear_unused_tracks(track_nums)
        # sets tracks that have more than 1 instance, so LED control can be efficiently checked later
        self.duplicates = set([x for x in track_nums if track_nums.count(x) > 1])

        return tracks

    def clear_unused_tracks(self, track_nums):
        # Sends clear to tracks on pedal that aren't linked. IE, if there's CL#1 & CL#2, track 3 will get a clear state
        i = 0
        while i < NUM_TRACKS:
            if i not in track_nums:
                self.send_sysex(i, CHANGE_STATE_COMMAND, CLEAR_STATE)
            i += 1

    def clear_tracks(self):
        for track in self.tracks:
            track.remove_track()
        self.tracks = []

    def append_tracks(self, track, trackNum, track_key):
        if track_key == DATALOOPER_KEY:
            # adds a listener to tracks detected as DataLoopers to rescan for looper when a devices is added
            if not track.devices_has_listener(self.__parent.scan_tracks):
                track.add_devices_listener(self.__parent.scan_tracks)
            # checks for devices
            if track.devices:
                for device in track.devices:
                    if device.name == "Looper":
                        self.send_message("adding looper track")
                        self.tracks[str(trackNum)].append(DlTrack(self, track, device, trackNum, self.song))
                    else:
                        self.send_message("Looper Device Does Not Exist on Track: " + track.name)
        elif track_key == CLIPLOOPER_KEY:
            if track.has_midi_input:
                self.send_message("adding clip midi track")
                self.tracks[str(trackNum)].append(ClMidiTrack(self, track, trackNum, self.song))
            elif track.has_audio_input:
                self.send_message("adding clip audio track")
                self.tracks[str(trackNum)].append(ClAudioTrack(self, track, trackNum, self.song))

    def send_midi(self, midi):
        self.__parent.send_midi(midi)

    def send_message(self, message):
        self.__parent.send_message(message)
