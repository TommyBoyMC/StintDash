from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from stintdash.race_data import RaceResult


class RaceHistoryTableModel(QAbstractTableModel):
    HEADERS = [
        "Date",
        "Track",
        "Car",
        "Race Type",
        "Start Position",
        "Finish Position",
        "Best Lap",
    ]

    FIELDS = [
        "date",
        "track",
        "car",
        "race_type",
        "start_position",
        "finish_position",
        "best_lap",
    ]

    INITIAL_ROWS = 25
    BATCH_SIZE = 15

    def __init__(self, races: list[RaceResult]):
        super().__init__()
        self._all_races = races
        self._filtered_races = list(races)
        self._visible_rows = min(self.INITIAL_ROWS, len(self._filtered_races))
        self._is_loading = False
        self._track_filter = "All Tracks"
        self._car_filter = "All Cars"
        self._position_filter = "All Positions"
        self._race_type_filter = "All Types"

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._visible_rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._filtered_races):
            return None

        race = self._filtered_races[index.row()]
        field = self.FIELDS[index.column()]
        value = getattr(race, field)

        if role == Qt.ItemDataRole.DisplayRole:
            return value

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if field in {"start_position", "finish_position", "best_lap"}:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        if role == Qt.ItemDataRole.ForegroundRole and field == "finish_position":
            if self._position_number(value) <= 3:
                return QColor("#ff5a66")

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.TextAlignmentRole:
            if section >= 4:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def can_load_more(self) -> bool:
        return self._visible_rows < len(self._filtered_races) and not self._is_loading

    def load_more(self) -> int:
        if not self.can_load_more():
            return 0

        self._is_loading = True
        current_count = self._visible_rows
        next_count = min(current_count + self.BATCH_SIZE, len(self._filtered_races))

        self.beginInsertRows(QModelIndex(), current_count, next_count - 1)
        self._visible_rows = next_count
        self.endInsertRows()

        self._is_loading = False
        return next_count - current_count

    @property
    def visible_rows(self) -> int:
        return self._visible_rows

    @property
    def total_matching_rows(self) -> int:
        return len(self._filtered_races)

    @property
    def all_races(self) -> list[RaceResult]:
        return self._all_races

    def race_at(self, row: int) -> RaceResult | None:
        if 0 <= row < min(self._visible_rows, len(self._filtered_races)):
            return self._filtered_races[row]
        return None

    def set_races(self, races: list[RaceResult]):
        self.beginResetModel()
        self._all_races = races
        self._filtered_races = [
            race for race in self._all_races if self._matches_filters(race)
        ]
        self._visible_rows = min(self.INITIAL_ROWS, len(self._filtered_races))
        self._is_loading = False
        self.endResetModel()

    def set_filters(self, track: str, car: str, position: str, race_type: str):
        self.beginResetModel()
        self._track_filter = track
        self._car_filter = car
        self._position_filter = position
        self._race_type_filter = race_type
        self._filtered_races = [
            race for race in self._all_races if self._matches_filters(race)
        ]
        self._visible_rows = min(self.INITIAL_ROWS, len(self._filtered_races))
        self.endResetModel()

    def _matches_filters(self, race: RaceResult) -> bool:
        if self._track_filter != "All Tracks" and race.track != self._track_filter:
            return False

        if (
            self._car_filter != "All Cars"
            and self._car_filter.lower() not in race.car.lower()
            and self._car_filter.lower() != race.car_manufacturer.lower()
        ):
            return False

        if self._position_filter != "All Positions" and race.finish_position != self._position_filter:
            return False

        if self._race_type_filter != "All Types" and race.race_type != self._race_type_filter:
            return False

        return True

    @staticmethod
    def _position_number(position: str) -> int:
        try:
            return int(position.removeprefix("P"))
        except ValueError:
            return 99
