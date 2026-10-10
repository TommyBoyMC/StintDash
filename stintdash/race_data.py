from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class DriverLap:
    number: str
    time: str
    raw_values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DriverResult:
    name: str
    team_name: str
    car_type: str
    car_class: str
    car_number: str
    grid_position: str
    position: str
    class_grid_position: str
    class_position: str
    best_lap_time: str
    laps_completed: str
    pitstops: str
    finish_status: str
    laps: tuple[DriverLap, ...] = ()
    raw_values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RaceResult:
    race_id: str
    date: str
    track: str
    car: str
    car_manufacturer: str
    race_type: str
    start_position: str
    finish_position: str
    best_lap: str
    sort_datetime: datetime
    source_file: Path
    player_driver: DriverResult
    classification: tuple[DriverResult, ...] = ()
