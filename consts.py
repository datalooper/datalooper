MASTER_STOP = 127
MASTER_MUTE = 126
CHANNEL = 13
NUM_TRACKS = 3
NUM_CONTROLS = 4

RECORD_CONTROL = 0
STOP_CONTROL = 1
UNDO_CONTROL = 2
CLEAR_CONTROL = 3

RESET_COMMAND = 0
INSTANCE_CHANGE = 6

CHANGE_STATE_COMMAND = 1
DOWNBEAT_COMMAND = 2
REQUEST_CONTROL_COMMAND = 3

DATALOOPER_KEY = 'DL#'
CLIPLOOPER_KEY = 'CL#'
TRACK_KEYS = [DATALOOPER_KEY, CLIPLOOPER_KEY]

NOTE_OFF_STATUS = 128
NOTE_ON_STATUS = 144
CC_STATUS = 176


# QUANTIZE VALUES
GLOBAL = 0.0
NO_QUANTIZATION = 1.0
EIGHT_BARS = 2.0
FOUR_BARS = 3.0
TWO_BARS = 4.0
ONE_BAR = 5.0
HALF_NOTE = 6.0
HALF_TRIPLET = 7.0
QUARTER_NOTE = 8.0
QUARTER_TRIPLET = 9.0
EIGHTH_NOTE = 10.0
EIGHTH_TRIPLET = 11.0
SIXTEENTH_NOTE = 12.0
SIXTEENTH_NOTE_TRIPLET = 13.0
THIRTY_SECOND_NOTE = 14.0

# LOOPER PARAMS
DEVICE_ON = 0
STATE = 1

STOP_STATE = 0
RECORDING_STATE = 1
PLAYING_STATE = 2
OVERDUB_STATE = 3
CLEAR_STATE = 4
OFF_STATE = 5
NEW_SESSION_STATE = 6

FEEDBACK = 2
REVERSE = 3
MONITOR = 4
SPEED = 5
QUANTIZATION = 6

SONG_CONTROL = 7

NO_TEMPO_CONTROL = 0
FOLLOW_SONG_TEMPO = 1
SET_AND_FOLLOW_SONG_TEMPO = 2

TEMPO_CONTROL = 8


LOOPER_TRACK = 0
CLIP_TRACK = 1

# 30 ticks to 1/32 note
# bar : quarter notes : sixteenth notes : (ticks / 30 ) = 32 notes

# bar * 960 | quarter  * 240 | sixteenth * 60


# DATALOOPER SYSEX PROTOCOL ADDRESS MAP#


# 00 00 00 program state
#   -initialize 00
#   -exit 01
# 00 00 01 master commands
#   -stop all 00
#   -clear all 01
#   -mute all 02
# 00 00 02 looper 1
#   -rec/play/ovr 00
#   -stop 01
#   -undo/redo 02
#   -clear 03
# 00 00 03 looper 2
#   -rec/play/ovr 00
#   -stop 01
#   -undo/redo 02
#   -clear 03
# 00 00 04 looper 3
#   -rec/play/ovr 00
#   -stop 01
#   -undo/redo 02
#   -clear 03
# 00 00 05 mode switch
#   -enter new session mode
#   -enter config mode
# 00 00 07 time
#   -on downbeat