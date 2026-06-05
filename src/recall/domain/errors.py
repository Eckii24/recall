from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RecallError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


class InvalidArgumentsError(RecallError):
    pass


class InvalidConfigError(RecallError):
    def __init__(self, message: str = "Invalid configuration") -> None:
        super().__init__(message=message)


class DeckNotFoundError(RecallError):
    def __init__(self, deck: str) -> None:
        super().__init__(message=f"Deck not found: {deck}")


class CardNotFoundError(RecallError):
    def __init__(self, deck: str, card_id: str) -> None:
        super().__init__(message=f"Card not found in deck {deck}: {card_id}")


class InvalidCardFormatError(RecallError):
    pass


class InvalidSidecarStateError(RecallError):
    pass


class NoDueCardsError(RecallError):
    def __init__(self, deck: str) -> None:
        super().__init__(message=f"No due cards for deck: {deck}")


class WriteError(RecallError):
    pass
