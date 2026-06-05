from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from recall.domain.entities import Flashcard, NormalizeResult, ParsedDeck, ParseIssue

ID_PATTERN = re.compile(r"^[a-zA-Z0-9._:-]+$")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
ID_COMMENT_PATTERN = re.compile(r"^\s*<!--\s*recall:id=([^>]*)\s*-->\s*$")
FENCE_PATTERN = re.compile(r"^(```+|~~~+)")


@dataclass(slots=True)
class CandidateCard:
    level: int
    question: str
    line: int
    answer_lines: list[str] = field(default_factory=list)
    card_id: str | None = None
    id_present: bool = False
    awaiting_id: bool = True


def _strip_frontmatter(lines: list[str]) -> tuple[int, list[str]]:
    if len(lines) >= 3 and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return index + 1, lines[index + 1 :]
    return 0, lines


def _is_card_heading(
    title: str, level: int, auto_mode: bool, min_heading_level: int
) -> bool:
    return level >= min_heading_level if auto_mode else "#flashcard" in title.split()


def _clean_question(title: str) -> str:
    return " ".join(part for part in title.split() if part != "#flashcard").strip()


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "card"


def generate_card_id(deck_name: str, question: str, used_ids: set[str]) -> str:
    base = f"{deck_name}-{_slugify(question)}"
    candidate = base
    suffix = 2
    while candidate in used_ids:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used_ids.add(candidate)
    return candidate


def parse_markdown_deck(
    markdown: str, deck_name: str, auto_mode: bool = False, min_heading_level: int = 2
) -> ParsedDeck:
    original_lines = markdown.splitlines()
    start_offset, lines = _strip_frontmatter(original_lines)
    deck = ParsedDeck(deck_name=deck_name)
    used_ids: set[str] = set()
    in_fence = False
    candidates: list[CandidateCard] = []
    active: CandidateCard | None = None

    for relative_index, line in enumerate(lines):
        line_number = start_offset + relative_index + 1
        if FENCE_PATTERN.match(line.strip()):
            in_fence = not in_fence
        if in_fence:
            if active is not None:
                active.answer_lines.append(line)
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            if active is not None and level <= active.level:
                candidates.append(active)
                active = None
            if active is None and _is_card_heading(
                title, level, auto_mode, min_heading_level
            ):
                active = CandidateCard(
                    level=level, question=_clean_question(title), line=line_number
                )
                continue
        if active is None:
            continue
        id_match = ID_COMMENT_PATTERN.match(line)
        if active.awaiting_id and id_match:
            active.card_id = id_match.group(1).strip()
            active.id_present = True
            active.awaiting_id = False
            continue
        if active.awaiting_id and line.strip() == "":
            continue
        if active.awaiting_id:
            deck.issues.append(
                ParseIssue(
                    code="missing_id",
                    message="Missing explicit recall:id directly under heading",
                    line=active.line,
                )
            )
            active.awaiting_id = False
        active.answer_lines.append(line)

    if active is not None:
        candidates.append(active)

    for candidate in candidates:
        card_id = candidate.card_id
        answer = "\n".join(candidate.answer_lines).strip()
        if card_id is None and not candidate.id_present:
            deck.issues.append(
                ParseIssue(
                    code="missing_id",
                    message="Missing explicit recall:id directly under heading",
                    line=candidate.line,
                )
            )
            continue
        if not ID_PATTERN.match(str(card_id)):
            deck.issues.append(
                ParseIssue(
                    code="invalid_id",
                    message=f"Invalid card id: {card_id}",
                    line=candidate.line,
                )
            )
        elif str(card_id) in used_ids:
            deck.issues.append(
                ParseIssue(
                    code="duplicate_id",
                    message=f"Duplicate card id: {card_id}",
                    line=candidate.line,
                )
            )
        else:
            used_ids.add(str(card_id))
        if not answer.strip():
            deck.issues.append(
                ParseIssue(
                    code="empty_answer",
                    message=f"Card {card_id} has an empty answer",
                    line=candidate.line,
                )
            )
        deck.cards.append(
            Flashcard(
                card_id=str(card_id),
                question=candidate.question,
                answer=answer,
                heading_level=candidate.level,
                line=candidate.line,
            )
        )
    return deck


def normalize_deck_markdown(
    markdown: str,
    deck_name: str,
    write: bool = False,
    path: Path | None = None,
    auto_mode: bool = False,
    min_heading_level: int = 2,
) -> NormalizeResult:
    lines = markdown.splitlines()
    start_offset, _visible_lines = _strip_frontmatter(lines)
    used_ids: set[str] = set()
    output_lines = list(lines)
    inserts: list[tuple[int, str]] = []
    missing_ids: list[str] = []
    in_fence = False
    absolute_index = start_offset

    while absolute_index < len(lines):
        line = lines[absolute_index]
        stripped = line.strip()
        if FENCE_PATTERN.match(stripped):
            in_fence = not in_fence
            absolute_index += 1
            continue
        if in_fence:
            absolute_index += 1
            continue
        heading_match = HEADING_PATTERN.match(line)
        if not heading_match:
            absolute_index += 1
            continue
        level = len(heading_match.group(1))
        title = heading_match.group(2)
        if not _is_card_heading(title, level, auto_mode, min_heading_level):
            absolute_index += 1
            continue
        question = _clean_question(title)
        next_index = absolute_index + 1
        while next_index < len(lines) and lines[next_index].strip() == "":
            next_index += 1
        if next_index < len(lines):
            id_match = ID_COMMENT_PATTERN.match(lines[next_index])
            if id_match:
                used_ids.add(id_match.group(1).strip())
                absolute_index += 1
                continue
        new_id = generate_card_id(deck_name, question, used_ids)
        inserts.append((absolute_index + 1, f"<!-- recall:id={new_id} -->"))
        missing_ids.append(new_id)
        absolute_index += 1

    for delta, (insert_at, value) in enumerate(inserts):
        output_lines.insert(insert_at + delta, value)

    content = "\n".join(output_lines) + (
        "\n" if markdown.endswith("\n") or markdown == "" else ""
    )
    changed = bool(inserts)
    written = write and changed and path is not None
    if path is not None and written:
        path.write_text(content, encoding="utf-8")
    return NormalizeResult(
        deck_name=deck_name,
        content=content,
        changed=changed,
        missing_ids=missing_ids,
        written=written,
    )
