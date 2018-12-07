address_map = [
    # button 1
    ((-1, -1, 0, 0, 0), ["record_looper"]),
    ((-1, -1, 0, 1, 0), ["record_clip"]),
    ((-1, -1, 0, 2, 1), ["new_clip"]),

    # button 2
    ((-1, -1, 1, 1, 0), ["stop"]),
    ((-1, -1, 1, 2, 1), ["clear"]),

    # button 3
    ((-1, -1, 2, 1, 0), ["undo", "bank_if_clear"]),
    ((-1, -1, 2, 2, 1), ["bank"]),

    # button 4 top
    ((-1, 2, 3, 0, 0), ["clear_all", "exit_new_session"]),
    ((-1, 2, 3, 2, 2), ["enter_new_session"]),

    # button 4 middle
    ((-1, 1, 3, 0, 0), ["mute_all", "tap_tempo"]),
    ((-1, 1, 3, 1, -1), ["mute_all"]),

    # button 4 bottom
    ((-1, 0, 3, 0, 0), ["toggle_start_stop_all"]),

    # move this to teensy, config should be hardwired
    ((-1, 2, 3, 2, 5), ["enter_config"]),
    ((-1, -1, -1, 3, -1), ["change_instance"]),
    ((-1, 127, 127, 127, 127), ["exit_config"])
]