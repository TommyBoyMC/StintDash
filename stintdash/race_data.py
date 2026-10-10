from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class RaceResult:
    date: str
    track: str
    car: str
    race_type: str
    start_position: str
    finish_position: str
    best_lap: str


TRACK_LAPS = {
    "Bahrain": (154, 706),
    "Barcelona": (103, 318),
    "Le Mans": (230, 512),
    "Paul Ricard": (139, 125),
    "COTA": (124, 856),
    "Daytona": (105, 972),
    "Fuji": (129, 381),
    "Imola": (142, 186),
    "Interlagos": (130, 614),
    "Lusail": (112, 406),
    "Road Atlanta": (78, 934),
    "Monza": (106, 833),
    "Portimao": (139, 944),
    "Sebring": (118, 742),
    "Silverstone": (120, 291),
    "Spa-Francorchamps": (118, 427),
    "Longbeach": (79, 508),
    "Laguna Seca": (83, 221),
}

CARS = [
    "Ford Mustang LMGT3",
    "McLaren 720S LMGT3 Evo",
    "Mercedes-AMG LMGT3",
    "BMW M4 LMGT3",
    "Aston Martin Vantage AMR LMGT3",
    "Corvette Z06 GT3.R",
    "Ferrari 296 LMGT3",
    "Lamborghini Huracan LMGT3 Evo2",
    "Lexus RC F LMGT3",
    "Porsche 911 GT3 R",
]

RACE_TYPES = ["Daily Race", "Weekly Race", "Race Weekend"]


def _lap_time(track: str, index: int) -> str:
    base_seconds, base_ms = TRACK_LAPS[track]
    seconds = base_seconds + ((index * 7) % 10) - 4
    milliseconds = (base_ms + index * 137) % 1000
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}.{milliseconds:03d}"


def create_sample_race_results(total: int = 112) -> list[RaceResult]:
    start_date = date(2026, 10, 8)
    tracks = list(TRACK_LAPS.keys())
    races: list[RaceResult] = []

    for index in range(total):
        track = tracks[index % len(tracks)]
        car = CARS[(index * 2 + index // 5) % len(CARS)]
        race_type = RACE_TYPES[index % len(RACE_TYPES)]
        race_date = start_date - timedelta(days=index // 2)

        start_position = ((index * 5) % 24) + 1
        finish_position = ((start_position + 16 - (index % 9)) % 24) + 1
        if index in (2, 9, 18, 31, 44, 57, 71, 88):
            finish_position = (index % 3) + 1

        races.append(
            RaceResult(
                date=race_date.strftime("%d %b %Y"),
                track=track,
                car=car,
                race_type=race_type,
                start_position=f"P{start_position}",
                finish_position=f"P{finish_position}",
                best_lap=_lap_time(track, index),
            )
        )

    return races
