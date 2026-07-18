"""Load and validate version-controlled alignment evaluation data."""

import json
from pathlib import Path
from typing import NotRequired, TypedDict, cast

from src.evaluation.models import (
    AlignmentLabel,
    EvaluationDataset,
    EvaluationDocumentPair,
    EvaluationExample,
    EvaluationSection,
)


class _SectionPayload(TypedDict):
    id: str
    title: str
    content: str


class _LabelPayload(TypedDict):
    old_section_ids: list[str]
    new_section_ids: list[str]
    relationship: str
    difficulty: NotRequired[str]
    notes: NotRequired[str]


class _DocumentPairPayload(TypedDict):
    id: str
    old_sections: list[_SectionPayload]
    new_sections: list[_SectionPayload]
    labels: list[_LabelPayload]


class _DatasetPayload(TypedDict):
    name: str
    document_pairs: list[_DocumentPairPayload]


def load_evaluation_dataset(path: Path) -> EvaluationDataset:
    """Load a JSON evaluation dataset into immutable typed models.

    Args:
        path: JSON file containing labeled document pairs.

    Returns:
        A validated evaluation dataset.

    Raises:
        ValueError: If identifiers are duplicated, unknown, or structurally invalid.
    """
    with path.open(encoding="utf-8") as dataset_file:
        payload = cast(_DatasetPayload, json.load(dataset_file))

    document_pairs = tuple(_load_document_pair(item) for item in payload["document_pairs"])
    pair_ids = [pair.identifier for pair in document_pairs]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("Document pair identifiers must be unique.")
    return EvaluationDataset(name=payload["name"], document_pairs=document_pairs)


def _load_document_pair(payload: _DocumentPairPayload) -> EvaluationDocumentPair:
    old_sections = tuple(_load_section(item) for item in payload["old_sections"])
    new_sections = tuple(_load_section(item) for item in payload["new_sections"])
    old_ids = {section.identifier for section in old_sections}
    new_ids = {section.identifier for section in new_sections}

    if len(old_ids) != len(old_sections) or len(new_ids) != len(new_sections):
        raise ValueError(f"Section identifiers must be unique in {payload['id']}.")

    examples = tuple(
        _load_example(payload["id"], item, old_ids, new_ids) for item in payload["labels"]
    )
    return EvaluationDocumentPair(
        identifier=payload["id"],
        old_sections=old_sections,
        new_sections=new_sections,
        examples=examples,
    )


def _load_section(payload: _SectionPayload) -> EvaluationSection:
    return EvaluationSection(
        identifier=payload["id"], title=payload["title"], content=payload["content"]
    )


def _load_example(
    document_pair_id: str,
    payload: _LabelPayload,
    old_ids: set[str],
    new_ids: set[str],
) -> EvaluationExample:
    old_section_ids = tuple(payload["old_section_ids"])
    new_section_ids = tuple(payload["new_section_ids"])
    relationship = AlignmentLabel(payload["relationship"])

    unknown_old = set(old_section_ids) - old_ids
    unknown_new = set(new_section_ids) - new_ids
    if unknown_old or unknown_new:
        raise ValueError(
            f"Label in {document_pair_id} references unknown sections: "
            f"old={sorted(unknown_old)}, new={sorted(unknown_new)}."
        )
    _validate_relationship_shape(document_pair_id, relationship, old_section_ids, new_section_ids)
    return EvaluationExample(
        document_pair_id=document_pair_id,
        old_section_ids=old_section_ids,
        new_section_ids=new_section_ids,
        relationship=relationship,
        difficulty=payload.get("difficulty"),
        notes=payload.get("notes"),
    )


def _validate_relationship_shape(
    document_pair_id: str,
    relationship: AlignmentLabel,
    old_ids: tuple[str, ...],
    new_ids: tuple[str, ...],
) -> None:
    valid_shape = {
        AlignmentLabel.MATCHED: len(old_ids) == 1 and len(new_ids) == 1,
        AlignmentLabel.ADDED: not old_ids and len(new_ids) == 1,
        AlignmentLabel.REMOVED: len(old_ids) == 1 and not new_ids,
        AlignmentLabel.AMBIGUOUS: len(old_ids) >= 1 and len(new_ids) >= 1,
        AlignmentLabel.SPLIT: len(old_ids) == 1 and len(new_ids) > 1,
        AlignmentLabel.MERGED: len(old_ids) > 1 and len(new_ids) == 1,
    }[relationship]
    if not valid_shape:
        raise ValueError(
            f"Invalid {relationship.value} label shape in {document_pair_id}: "
            f"old={old_ids}, new={new_ids}."
        )
