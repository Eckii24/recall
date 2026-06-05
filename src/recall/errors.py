from __future__ import annotations

from dataclasses import dataclass

from recall.exit_codes import ExitCode


@dataclass(slots=True)
class RecallError(Exception):
    message: str
    exit_code: ExitCode

    def __str__(self) -> str:
        return self.message


class InvalidArgumentsError(RecallError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, exit_code=ExitCode.INVALID_ARGUMENTS)


class InvalidConfigError(RecallError):
    def __init__(self, message: str = "Invalid configuration") -> None:
        super().__init__(message=message, exit_code=ExitCode.INVALID_CONFIG)


class DeckNotFoundError(RecallError):
    def __init__(self, deck: str) -> None:
        super().__init__(
            message=f"Deck not found: {deck}", exit_code=ExitCode.DECK_NOT_FOUND
        )


class CardNotFoundError(RecallError):
    def __init__(self, deck: str, card_id: str) -> None:
        super().__init__(
            message=f"Card not found in deck {deck}: {card_id}",
            exit_code=ExitCode.CARD_NOT_FOUND,
        )


class InvalidCardFormatError(RecallError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, exit_code=ExitCode.INVALID_CARD_FORMAT)


class InvalidSidecarStateError(RecallError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, exit_code=ExitCode.INVALID_SIDECAR_STATE)


class NoDueCardsError(RecallError):
    def __init__(self, deck: str) -> None:
        super().__init__(
            message=f"No due cards for deck: {deck}", exit_code=ExitCode.NO_DUE_CARDS
        )


class WriteError(RecallError):
    def __init__(self, message: str) -> None:
        super().__init__(message=message, exit_code=ExitCode.WRITE_ERROR)
