from __future__ import annotations

import hashlib
import os
import re
import string
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from stintdash.race_data import DriverLap, DriverResult, RaceResult


DEFAULT_PLAYER_NAME = "Tom Ridder"
RESULT_FILE_PATTERN = re.compile(r".*R\d+\.xml$", re.IGNORECASE)
LMU_RESULTS_SUFFIX = Path("steamapps/common/Le Mans Ultimate/UserData/Log/Results")


def discover_results_directory() -> Path | None:
    for candidate in _candidate_results_directories():
        if candidate.is_dir():
            return candidate
    return None


def load_lmu_races(results_dir: Path, player_name: str = DEFAULT_PLAYER_NAME) -> list[RaceResult]:
    if not results_dir.is_dir():
        return []

    races_by_id: dict[str, RaceResult] = {}
    for file_path in sorted(results_dir.glob("*.xml")):
        if not RESULT_FILE_PATTERN.match(file_path.name):
            continue

        race = parse_lmu_result_file(file_path, player_name)
        if race is not None:
            races_by_id[race.race_id] = race

    return sorted(
        races_by_id.values(),
        key=lambda race: (race.sort_datetime, race.source_file.name),
        reverse=True,
    )


def parse_lmu_result_file(file_path: Path, player_name: str = DEFAULT_PLAYER_NAME) -> RaceResult | None:
    try:
        root = ET.parse(file_path).getroot()
    except (ET.ParseError, OSError, UnicodeDecodeError):
        return None

    race_results = root.find("RaceResults")
    if race_results is None:
        return None

    race_node = race_results.find("Race")
    if race_node is None:
        return None

    drivers = tuple(_parse_driver(driver_node) for driver_node in race_node.findall("Driver"))
    player_driver = next(
        (driver for driver in drivers if driver.name.casefold() == player_name.casefold()),
        None,
    )
    if player_driver is None:
        return None

    raw_date = _text(race_node, "TimeString") or _text(race_results, "TimeString")
    sort_datetime = _parse_datetime(raw_date, file_path)
    display_date = sort_datetime.strftime("%d %b %Y") if sort_datetime != datetime.min else "-"

    track_venue = _text(race_results, "TrackVenue")
    race_type = _text(race_results, "Setting") or "-"
    race_id = _race_id(file_path, raw_date, track_venue, race_type)

    return RaceResult(
        race_id=race_id,
        date=display_date,
        track=_display_track(track_venue),
        car=player_driver.car_type or "-",
        car_manufacturer=_car_manufacturer(player_driver.car_type),
        race_type=race_type,
        race_duration=_format_race_duration(_text(race_node, "Minutes") or _text(race_results, "RaceTime")),
        start_position=_format_position(player_driver.grid_position),
        finish_position=_format_position(player_driver.position),
        best_lap=_format_lap_time(player_driver.best_lap_time),
        sort_datetime=sort_datetime,
        source_file=file_path,
        player_driver=player_driver,
        classification=drivers,
    )


def _candidate_results_directories() -> list[Path]:
    steam_roots: list[Path] = []

    for env_name in ("ProgramFiles(x86)", "ProgramFiles"):
        program_files = os.environ.get(env_name)
        if program_files:
            steam_roots.append(Path(program_files) / "Steam")

    steam_roots.extend(
        Path(f"{drive}:") / folder
        for drive in string.ascii_uppercase
        for folder in ("Steam", "SteamLibrary")
    )

    library_roots = []
    for steam_root in steam_roots:
        library_roots.append(steam_root)
        library_roots.extend(_steam_library_roots(steam_root))

    candidates = []
    seen = set()
    for root in library_roots:
        candidate = root / LMU_RESULTS_SUFFIX
        key = str(candidate).casefold()
        if key not in seen:
            seen.add(key)
            candidates.append(candidate)

    return candidates


def _steam_library_roots(steam_root: Path) -> list[Path]:
    library_file = steam_root / "steamapps" / "libraryfolders.vdf"
    try:
        text = library_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    roots = []
    for match in re.finditer(r'"path"\s+"([^"]+)"', text):
        roots.append(Path(match.group(1).replace("\\\\", "\\")))
    return roots


def _parse_driver(driver_node: ET.Element) -> DriverResult:
    raw_values = {
        child.tag: (child.text or "").strip()
        for child in driver_node
        if child.tag != "Lap"
    }
    laps = tuple(_parse_lap(lap_node) for lap_node in driver_node.findall("Lap"))
    driver_identity = "|".join(
        raw_values.get(field, "")
        for field in ("Name", "CarType", "CarNumber", "TeamName")
    )

    return DriverResult(
        driver_id=hashlib.sha1(driver_identity.encode("utf-8", errors="ignore")).hexdigest(),
        name=raw_values.get("Name", ""),
        team_name=raw_values.get("TeamName", ""),
        car_type=raw_values.get("CarType", ""),
        car_class=raw_values.get("CarClass", ""),
        car_number=raw_values.get("CarNumber", ""),
        grid_position=raw_values.get("GridPos", ""),
        position=raw_values.get("Position", ""),
        class_grid_position=raw_values.get("ClassGridPos", ""),
        class_position=raw_values.get("ClassPosition", ""),
        best_lap_time=raw_values.get("BestLapTime", ""),
        finish_time=raw_values.get("FinishTime", ""),
        laps_completed=raw_values.get("Laps", ""),
        pitstops=raw_values.get("Pitstops", ""),
        finish_status=raw_values.get("FinishStatus", ""),
        laps=laps,
        raw_values=raw_values,
    )


def _parse_lap(lap_node: ET.Element) -> DriverLap:
    raw_values = dict(lap_node.attrib)
    for child in lap_node:
        raw_values[child.tag] = (child.text or "").strip()

    number = raw_values.get("num") or raw_values.get("Num") or raw_values.get("Lap") or ""
    time = (lap_node.text or "").strip() or raw_values.get("Time", "")
    return DriverLap(number=number, time=time, raw_values=raw_values)


def _text(node: ET.Element, tag: str) -> str:
    value = node.findtext(tag)
    return value.strip() if value else ""


def _parse_datetime(value: str, file_path: Path) -> datetime:
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    match = re.match(r"(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})", file_path.name)
    if match:
        try:
            return datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(4)),
                int(match.group(5)),
                int(match.group(6)),
            )
        except ValueError:
            pass

    return datetime.min


def _race_id(file_path: Path, raw_date: str, track: str, race_type: str) -> str:
    identity = f"{file_path.resolve()}|{raw_date}|{track}|{race_type}"
    return hashlib.sha1(identity.encode("utf-8", errors="ignore")).hexdigest()


def _display_track(track_venue: str) -> str:
    if not track_venue:
        return "-"

    overrides = {
        "Sebring International Raceway": "Sebring",
        "Circuit de la Sarthe": "Le Mans",
        "Circuit des 24 Heures du Mans": "Le Mans",
        "Autodromo Nazionale Monza": "Monza",
        "Circuit de Spa-Francorchamps": "Spa-Francorchamps",
    }
    return overrides.get(track_venue, track_venue)


def _car_manufacturer(car_type: str) -> str:
    if not car_type:
        return "-"

    lowered = car_type.lower()
    known = {
        "aston martin": "Aston Martin",
        "bmw": "BMW",
        "chevrolet": "Chevrolet",
        "corvette": "Corvette",
        "ferrari": "Ferrari",
        "ford": "Ford",
        "lamborghini": "Lamborghini",
        "lexus": "Lexus",
        "mclaren": "McLaren",
        "mercedes": "Mercedes",
        "porsche": "Porsche",
    }
    for key, manufacturer in known.items():
        if key in lowered:
            return manufacturer

    return car_type.split()[0]


def _format_position(value: str) -> str:
    try:
        position = int(value)
    except (TypeError, ValueError):
        return "-"

    return f"P{position}" if position > 0 else "-"


def _format_lap_time(value: str) -> str:
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return "-"

    if seconds <= 0:
        return "-"

    total_milliseconds = round(seconds * 1000)
    minutes, remainder = divmod(total_milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{minutes}:{whole_seconds:02d}.{milliseconds:03d}"


def _format_race_duration(value: str) -> str:
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        return "-"

    if minutes <= 0:
        return "-"

    if minutes.is_integer():
        return f"{int(minutes)} minutes"

    return f"{minutes:g} minutes"
