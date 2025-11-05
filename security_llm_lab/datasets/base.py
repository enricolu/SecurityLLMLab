"""Base dataset abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol


@dataclass(slots=True)
class DatasetArtifact:
    """Metadata describing an extracted dataset artifact."""

    name: str
    path: Path
    description: str = ""


class SecurityDataset(Protocol):
    """Protocol that all dataset loaders should follow."""

    def prepare(self, destination: Path) -> Iterator[DatasetArtifact]:
        """Download and prepare the dataset inside ``destination``.

        Implementations should yield :class:`DatasetArtifact` objects that
        describe the resulting files.
        """

    def describe_sources(self) -> Iterable[str]:
        """Return references to the dataset documentation or repositories."""


__all__ = ["DatasetArtifact", "SecurityDataset"]
