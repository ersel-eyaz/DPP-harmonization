# This module defines simple dataset containers for the sandbox.
# It groups raw observations and harmonized records into reusable collection objects.
# These containers make it easier to organize, pass, and extend small experimental datasets.

from pydantic import BaseModel, Field

from schemas import RawObservation, HarmonizationRecord


class RawDataset(BaseModel):
    observations: list[RawObservation] = Field(default_factory=list)

    def add(self, observation: RawObservation) -> None:
        self.observations.append(observation)

    def extend(self, observations: list[RawObservation]) -> None:
        self.observations.extend(observations)


class HarmonizedDataset(BaseModel):
    records: list[HarmonizationRecord] = Field(default_factory=list)

    def add(self, record: HarmonizationRecord) -> None:
        self.records.append(record)

    def extend(self, records: list[HarmonizationRecord]) -> None:
        self.records.extend(records)