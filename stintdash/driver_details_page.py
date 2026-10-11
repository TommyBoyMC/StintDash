from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter

from PySide6.QtCore import QAbstractTableModel, QEvent, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QStyle,
    QGridLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from stintdash.race_data import DriverResult, RaceResult

MISSING_VALUE = "\u2014"
HIGHLIGHT_PURPLE = "#b86cff"
HIGHLIGHT_GREEN = "#40d982"
TEXT_COLOR = "#eef3f8"
HOVER_COLOR = "#121f31"
ROW_SEPARATOR_COLOR = "#7d1f2b"


class DriverLapTableModel(QAbstractTableModel):
    HEADERS = ["Lap", "Sector 1", "Sector 2", "Sector 3", "Lap Time", "Topspeed"]

    def __init__(self):
        super().__init__()
        self._rows: list[dict] = []
        self._race_bests: dict[str, float] = {}
        self._driver_bests: dict[str, float] = {}

    def set_driver(self, race: RaceResult | None, driver: DriverResult | None):
        self.beginResetModel()
        self._rows = self._build_rows(driver) if driver is not None else []
        self._race_bests = _race_best_times(race) if race is not None else {}
        self._driver_bests = self._find_driver_bests()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._rows):
            return None

        row = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return row["values"][index.column()]

        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        if role == Qt.ItemDataRole.ForegroundRole:
            time_key = {1: "s1", 2: "s2", 3: "s3", 4: "lap"}.get(index.column())
            if time_key is None:
                return None

            value = row["times"][time_key]
            if value is None:
                return None

            if _same_time(value, self._race_bests.get(time_key)):
                return QColor(HIGHLIGHT_PURPLE)
            if _same_time(value, self._driver_bests.get(time_key)):
                return QColor(HIGHLIGHT_GREEN)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        return None

    def _build_rows(self, driver: DriverResult) -> list[dict]:
        rows = []
        for lap in sorted(driver.laps, key=lambda item: (_int_or_large(item.number), item.number)):
            s1 = _float_or_none(lap.raw_values.get("s1"))
            s2 = _float_or_none(lap.raw_values.get("s2"))
            s3 = _float_or_none(lap.raw_values.get("s3"))
            lap_time = _float_or_none(lap.time)
            topspeed = _float_or_none(lap.raw_values.get("topspeed"))

            rows.append(
                {
                    "lap": lap,
                    "times": {
                        "s1": s1 if s1 is not None and s1 > 0 else None,
                        "s2": s2 if s2 is not None and s2 > 0 else None,
                        "s3": s3 if s3 is not None and s3 > 0 else None,
                        "lap": lap_time if lap_time is not None and lap_time > 0 else None,
                    },
                    "sector_seconds": {
                        "s1": s1 if s1 is not None and s1 > 0 else None,
                        "s2": s2 if s2 is not None and s2 > 0 else None,
                        "s3": s3 if s3 is not None and s3 > 0 else None,
                    },
                    "values": [
                        lap.number or MISSING_VALUE,
                        _format_sector(s1),
                        _format_sector(s2),
                        _format_sector(s3),
                        _format_lap_time(lap_time),
                        _format_speed(topspeed),
                    ],
                }
            )
        return rows

    def _find_driver_bests(self) -> dict[str, float]:
        bests = {}
        for key in ("s1", "s2", "s3", "lap"):
            valid_times = [
                row["times"][key]
                for row in self._rows
                if row["times"][key] is not None
            ]
            if valid_times:
                bests[key] = min(valid_times)
        return bests


class DriverLapTableDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered_row = -1

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        option = QStyleOptionViewItem(option)
        if index.row() == self.hovered_row:
            painter.save()
            painter.fillRect(option.rect, QColor(HOVER_COLOR))
            painter.restore()

            option.state &= ~QStyle.StateFlag.State_MouseOver
            option.state &= ~QStyle.StateFlag.State_Selected
            option.palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_COLOR))
            option.palette.setColor(QPalette.ColorRole.HighlightedText, QColor(TEXT_COLOR))
            option.palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_COLOR))

        super().paint(painter, option, index)

        painter.save()
        pen = QPen(QColor(ROW_SEPARATOR_COLOR))
        pen.setWidth(1)
        painter.setPen(pen)
        y = option.rect.bottom()
        painter.drawLine(option.rect.left(), y, option.rect.right(), y)
        painter.restore()


class DriverDetailsPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.current_race: RaceResult | None = None
        self.current_driver: DriverResult | None = None
        self._hovered_row = -1

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("RaceDetailsScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("RaceDetailsContent")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(30, 26, 30, 30)
        self.content_layout.setSpacing(22)

        self.content_layout.addLayout(self._build_heading())
        self.content_layout.addLayout(self._build_info_grid())
        self.content_layout.addWidget(self._build_lap_times_section())
        self.content_layout.addStretch()

        self.scroll_area.setWidget(content)
        root_layout.addWidget(self.scroll_area)

    def set_driver(self, race: RaceResult, driver: DriverResult):
        self.current_race = race
        self.current_driver = driver

        name = driver.name or "Driver"
        self.title_label.setText(f"Driver: {name}")
        self.subtitle_label.setText(f"Detailed race statistics for {name}.")
        self.track_label.setText(race.track or MISSING_VALUE)
        self.class_label.setText(driver.car_class or MISSING_VALUE)
        self.duration_label.setText(race.race_duration or MISSING_VALUE)
        self.start_label.setText(_format_position(driver.grid_position))
        self.finish_label.setText(_format_position(driver.position))
        self.track_limits_label.setText(_track_limits_points(race, driver))
        self.best_lap_label.setText(_format_lap_time(_float_or_none(driver.best_lap_time)))
        self.average_lap_label.setText(_average_lap_time(driver))
        self.total_time_label.setText(_format_lap_time(_float_or_none(driver.finish_time)))
        self.max_topspeed_label.setText(_max_topspeed(driver))
        self.theoretical_best_lap_label.setText(_theoretical_best_lap(driver))
        self.pitstops_label.setText(_pitstops(driver))
        self.most_used_tires_label.setText(_most_used_tires(driver))
        self.lap_table_model.set_driver(race, driver)
        self._resize_lap_table()
        self.scroll_area.verticalScrollBar().setValue(0)
        self._set_hovered_row(-1)

    def _build_heading(self) -> QVBoxLayout:
        heading = QVBoxLayout()
        heading.setSpacing(0)

        self.back_button = QPushButton("← Back to Race Details")
        self.back_button.setObjectName("BackButton")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.back_requested.emit)
        self.back_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        heading.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)
        return heading

    def _build_info_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 8)
        grid.setHorizontalSpacing(46)
        grid.setVerticalSpacing(14)

        heading = QVBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.setSpacing(4)
        self.title_label = QLabel("Driver")
        self.title_label.setObjectName("PageTitle")
        self.subtitle_label = QLabel("Detailed race statistics")
        self.subtitle_label.setObjectName("PageSubtitle")
        heading.addWidget(self.title_label)
        heading.addWidget(self.subtitle_label)
        grid.addLayout(heading, 0, 0, 2, 1)

        self.duration_label = self._add_info_field(grid, 0, 1, "Race Duration")
        self.start_label = self._add_info_field(grid, 1, 1, "Start Position")
        self.best_lap_label = self._add_info_field(grid, 0, 2, "Best Lap")
        self.average_lap_label = self._add_info_field(grid, 1, 2, "Average Lap Time")
        self.theoretical_best_lap_label = self._add_info_field(grid, 0, 3, "Theoretical Best Lap")
        self.pitstops_label = self._add_info_field(grid, 1, 3, "Pitstops")
        self.track_label = self._add_info_field(grid, 2, 0, "Track")
        self.finish_label = self._add_info_field(grid, 2, 1, "Finish Position")
        self.total_time_label = self._add_info_field(grid, 2, 2, "Total Time")
        self.most_used_tires_label = self._add_info_field(grid, 2, 3, "Most Used Tires")
        self.class_label = self._add_info_field(grid, 3, 0, "Class")
        self.track_limits_label = self._add_info_field(grid, 3, 1, "Track Limits Points")
        self.max_topspeed_label = self._add_info_field(grid, 3, 2, "Max Topspeed")

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        return grid

    def _add_info_field(self, grid: QGridLayout, row: int, column: int, label: str) -> QLabel:
        field = QWidget()
        layout = QVBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label_widget = QLabel(label.upper())
        label_widget.setObjectName("MetricLabel")
        value_widget = QLabel(MISSING_VALUE)
        value_widget.setObjectName("RaceInfoValue")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        grid.addWidget(field, row, column)
        return value_widget

    def _build_lap_times_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Lap Times")
        title.setObjectName("CardTitle")
        layout.addWidget(title)

        self.lap_table_model = DriverLapTableModel()
        self.lap_table = QTableView()
        self.lap_table.setObjectName("LeaderboardTable")
        self.lap_table.setModel(self.lap_table_model)
        self.lap_table_delegate = DriverLapTableDelegate(self.lap_table)
        self.lap_table.setItemDelegate(self.lap_table_delegate)
        self.lap_table.setShowGrid(False)
        self.lap_table.setAlternatingRowColors(False)
        self.lap_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lap_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.lap_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lap_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lap_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lap_table.verticalHeader().hide()
        self.lap_table.setWordWrap(False)
        self.lap_table.setMouseTracking(True)
        self.lap_table.viewport().setMouseTracking(True)
        self.lap_table.viewport().installEventFilter(self)
        self.lap_table.verticalHeader().setDefaultSectionSize(48)

        header = self.lap_table.horizontalHeader()
        header.setObjectName("RaceHistoryTableHeader")
        header.setStretchLastSection(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.lap_table)
        return section

    def _resize_lap_table(self):
        rows = self.lap_table_model.rowCount()
        row_height = self.lap_table.verticalHeader().defaultSectionSize()
        header_height = self.lap_table.horizontalHeader().height() or 44
        frame = self.lap_table.frameWidth() * 2
        self.lap_table.setFixedHeight(header_height + frame + (rows * row_height))

    def eventFilter(self, watched, event):
        if watched == self.lap_table.viewport():
            if event.type() == QEvent.Type.MouseMove:
                self._set_hovered_row(self.lap_table.indexAt(event.position().toPoint()).row())
            elif event.type() == QEvent.Type.Leave:
                self._set_hovered_row(-1)

        return super().eventFilter(watched, event)

    def _set_hovered_row(self, row: int):
        if row == self._hovered_row:
            return

        self._hovered_row = row
        self.lap_table_delegate.hovered_row = row
        self.lap_table.viewport().update()


def _average_lap_time(driver: DriverResult) -> str:
    valid_laps = [
        seconds
        for seconds in (_float_or_none(lap.time) for lap in driver.laps)
        if seconds is not None and seconds > 0
    ]
    if not valid_laps:
        return MISSING_VALUE
    return _format_lap_time(sum(valid_laps) / len(valid_laps))


def _race_best_times(race: RaceResult | None) -> dict[str, float]:
    if race is None:
        return {}

    bests = {}
    for key in ("s1", "s2", "s3", "lap"):
        valid_times = []
        for driver in race.classification:
            for lap in driver.laps:
                raw_value = lap.time if key == "lap" else lap.raw_values.get(key)
                seconds = _float_or_none(raw_value)
                if seconds is not None and seconds > 0:
                    valid_times.append(seconds)

        if valid_times:
            bests[key] = min(valid_times)
    return bests


def _max_topspeed(driver: DriverResult) -> str:
    speeds = [
        speed
        for speed in (_float_or_none(lap.raw_values.get("topspeed")) for lap in driver.laps)
        if speed is not None and speed > 0
    ]
    if not speeds:
        return MISSING_VALUE
    return _format_speed(max(speeds))


def _theoretical_best_lap(driver: DriverResult) -> str:
    sector_bests = []
    for sector in ("s1", "s2", "s3"):
        valid_sectors = [
            seconds
            for seconds in (_float_or_none(lap.raw_values.get(sector)) for lap in driver.laps)
            if seconds is not None and seconds > 0
        ]
        if not valid_sectors:
            return MISSING_VALUE
        sector_bests.append(min(valid_sectors))
    return _format_lap_time(sum(sector_bests))


def _pitstops(driver: DriverResult) -> str:
    pitstops = driver.pitstops.strip()
    return pitstops if pitstops else MISSING_VALUE


def _most_used_tires(driver: DriverResult) -> str:
    compounds = [_lap_tire_compound(lap.raw_values) for lap in driver.laps]
    compounds = [compound for compound in compounds if compound]
    if not compounds:
        return MISSING_VALUE

    counts = Counter(compounds)
    highest_count = max(counts.values())
    most_common = sorted(compound for compound, count in counts.items() if count == highest_count)
    if len(most_common) == 1:
        return most_common[0]
    return f"Tie: {', '.join(most_common)}"


def _lap_tire_compound(raw_values: dict[str, str]) -> str:
    front = _compound_name(raw_values.get("fcompound", ""))
    rear = _compound_name(raw_values.get("rcompound", ""))
    if front and rear:
        return front if front == rear else f"F: {front} / R: {rear}"
    if front or rear:
        return front or rear

    corners = {
        "FL": _compound_name(raw_values.get("FL", "")),
        "FR": _compound_name(raw_values.get("FR", "")),
        "RL": _compound_name(raw_values.get("RL", "")),
        "RR": _compound_name(raw_values.get("RR", "")),
    }
    present = {corner: compound for corner, compound in corners.items() if compound}
    if not present:
        return ""

    unique = set(present.values())
    if len(unique) == 1 and len(present) >= 2:
        return next(iter(unique))

    front_values = {present[corner] for corner in ("FL", "FR") if corner in present}
    rear_values = {present[corner] for corner in ("RL", "RR") if corner in present}
    if len(front_values) == 1 and len(rear_values) == 1:
        front = next(iter(front_values))
        rear = next(iter(rear_values))
        return front if front == rear else f"F: {front} / R: {rear}"

    return " / ".join(f"{corner}: {compound}" for corner, compound in sorted(present.items()))


def _compound_name(value: str) -> str:
    if not value:
        return ""

    compound = value.strip()
    if "," in compound:
        compound = compound.split(",", 1)[1].strip()
    return compound


def _track_limits_points(race: RaceResult, driver: DriverResult) -> str:
    try:
        root = ET.parse(race.source_file).getroot()
    except (ET.ParseError, OSError, UnicodeDecodeError):
        return MISSING_VALUE

    final_value = None
    for event in root.findall(".//Race/Stream/TrackLimits"):
        values = _event_values(event)
        if not _track_limit_event_matches_driver(values, driver):
            continue

        current_points = _first_value(values, ("CurrentPoints", "currentpoints", "Current Points"))
        parsed_points = _float_or_none(current_points)
        if parsed_points is not None:
            final_value = parsed_points

    if final_value is None:
        return MISSING_VALUE
    return f"{final_value:g}"


def _event_values(event: ET.Element) -> dict[str, str]:
    values = {key: value.strip() for key, value in event.attrib.items() if value and value.strip()}
    for child in event:
        if child.text and child.text.strip():
            values[child.tag] = child.text.strip()
    if event.text and event.text.strip():
        values["Text"] = event.text.strip()
    return values


def _track_limit_event_matches_driver(values: dict[str, str], driver: DriverResult) -> bool:
    driver_name = driver.name.strip().casefold()
    if not driver_name:
        return False

    candidate_keys = (
        "Driver",
        "DriverName",
        "Name",
        "driver",
        "driverName",
        "DriverFullName",
    )
    for key in candidate_keys:
        value = values.get(key, "").strip().casefold()
        if value == driver_name:
            return True

    searchable = " ".join(values.values()).casefold()
    if driver_name and driver_name in searchable:
        return True

    car_number = driver.car_number.strip()
    if car_number and any(value.strip() == car_number for value in values.values()):
        return True

    return False


def _first_value(values: dict[str, str], keys: tuple[str, ...]) -> str:
    lowered = {key.casefold(): value for key, value in values.items()}
    for key in keys:
        value = lowered.get(key.casefold())
        if value:
            return value
    return ""


def _format_position(value: str) -> str:
    position = _int_or_none(value)
    return f"P{position}" if position and position > 0 else MISSING_VALUE


def _format_sector(value: float | None) -> str:
    if value is None or value <= 0:
        return MISSING_VALUE
    return f"{value:.3f}"


def _format_speed(value: float | None) -> str:
    if value is None or value <= 0:
        return MISSING_VALUE
    return f"{value:.2f} km/h"


def _format_lap_time(value: float | None) -> str:
    if value is None or value <= 0:
        return MISSING_VALUE

    total_milliseconds = round(value * 1000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)

    if hours:
        return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"
    return f"{minutes}:{whole_seconds:02d}.{milliseconds:03d}"


def _same_time(value: float | None, other: float | None) -> bool:
    if value is None or other is None:
        return False
    return abs(value - other) <= 1e-9


def _int_or_large(value: str) -> int:
    parsed = _int_or_none(value)
    return parsed if parsed is not None else 9999


def _int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: str | float | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
