# datalooper
Official Ableton Remote Script for DataLooper Pedal


commands:
    looper rec (x) : [x, 0, 0, 0]
    looper stop (x): [x, 1, 0, 0]
    looper undo (x): [x, 2, 0, 0]
    looper clear (x): [x, 1, 2, 1]

    clear all loops : [0, 3, 0, 0]
    stop all loops : [1, 3, 0, 0]
    mute all looper : [2, 3, 0, 0]

    new session : [0, 3, 2, 2]
    config mode : [0, 3, 2, 5]




