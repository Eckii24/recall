from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0
    ERROR = 1
    INVALID_ARGUMENTS = 2
    INVALID_CONFIG = 3
    DECK_NOT_FOUND = 4
    CARD_NOT_FOUND = 5
    INVALID_CARD_FORMAT = 6
    INVALID_SIDECAR_STATE = 7
    NO_DUE_CARDS = 8
    WRITE_ERROR = 9
