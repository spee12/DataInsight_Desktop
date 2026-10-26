from dataclasses import dataclass, field
from typing import List
from domain.entities import DatasetProfile, Chart

@dataclass(frozen=True)
class DatasetInfoDTO:
    file_name: str
    row_count: int
    column_count: int
    file_path: str

@dataclass(frozen=True)
class AnalysisResultDTO:
    dataset_info: DatasetInfoDTO
    profile: DatasetProfile
    recommended_charts: List[Chart] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)