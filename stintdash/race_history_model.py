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
        "Mode",
    ]

    FIELDS = [
        "date",
        "track",
        "car",
        "race_type",
        "start_position",
        "finish_position",
        "best_lap",
        "mode",
    ]

    INITIAL_ROWS = 25
    BATCH_SIZE = 15

    def __init__(self, races: list[RaceResult]):
        super().__init__()
        self._races = races
        self._visible_rows = min(self.INITIAL_ROWS, len(races))
        self._is_loading = False

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return self._visible_rows

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        race = self._races[index.row()]
        field = self.FIELDS[index.column()]
        value = getattr(race, field)

        if role == Qt.ItemDataRole.DisplayRole:
            return value

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if field in {"start_position", "finish_position", "best_lap", "mode"}:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        if role == Qt.ItemDataRole.ForegroundRole and field == "finish_position":
            if self._position_number(value) <= 3:
                return QColor("#ff5a66")

        if role == Qt.ItemDataRole.ForegroundRole and field == "mode":
            return QColor("#dce6ef" if value == "Online" else "#8c9aab")

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
        return self._visible_rows < len(self._races) and not self._is_loading

    def load_more(self) -> int:
        if not self.can_load_more():
            return 0

        self._is_loading = True
        current_count = self._visible_rows
        next_count = min(current_count + self.BATCH_SIZE, len(self._races))

        self.beginInsertRows(QModelIndex(), current_count, next_count - 1)
        self._visible_rows = next_count
        self.endInsertRows()

        self._is_loading = False
        return next_count - current_count

    @property
    def visible_rows(self) -> int:
        return self._visible_rows

    @staticmethod
    def _position_number(position: str) -> int:
        try:
            return int(position.removeprefix("P"))
        except ValueError:
            return 99
