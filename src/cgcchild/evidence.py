"""Windows evidence extension contracts; observations never grant authority."""
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Protocol


class Truth(str, Enum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class WriterInventory:
    status: Truth = Truth.UNKNOWN


@dataclass(frozen=True)
class AliasAssessment:
    status: Truth = Truth.UNKNOWN


@dataclass(frozen=True)
class CrossRuntimeAssessment:
    status: Truth = Truth.UNKNOWN


@dataclass(frozen=True)
class MappingAssessment:
    status: Truth = Truth.UNKNOWN


@dataclass(frozen=True)
class MetadataMutationAssessment:
    status: Truth = Truth.UNKNOWN


@dataclass(frozen=True)
class FilesystemClosureAssessment:
    writers: WriterInventory = WriterInventory()
    aliases: AliasAssessment = AliasAssessment()
    cross_runtime: CrossRuntimeAssessment = CrossRuntimeAssessment()
    mappings: MappingAssessment = MappingAssessment()
    metadata: MetadataMutationAssessment = MetadataMutationAssessment()

    def report(self):
        # No provider has an accepted production attestation contract yet.
        return dict(components=asdict(self), production_status="UNKNOWN",
                    runtime_consequence="PRODUCTION_MUTATION_DISABLED")


class FilesystemEvidenceProvider(Protocol):
    def assess(self) -> FilesystemClosureAssessment: ...


class WindowsEvidenceProvider:
    def assess(self):
        return FilesystemClosureAssessment()
