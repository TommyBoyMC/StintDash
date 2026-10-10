from PySide6.QtCore import QAbstractTableModel, QEvent, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from stintdash.lmu_results import DEFAULT_PLAYER_NAME
from stintdash.race_data import DriverResult, RaceResult
from stintdash.widgets import DashboardCard


class RaceLeaderboardModel(QAbstractTableModel):
    HEADERS = ["Position", "Driver", "Car", "Best Lap", "Gap to Leader"]

    def __init__(self, player_name: str = DEFAULT_PLAYER_NAME):
        super().__init__()
        self.player_name = player_name
        self._rows: list[dict] = []
        self._fastest_lap_driver_id: str | None = None

    def set_race(self, race: RaceResult | None):
        self.beginResetModel()
        if race is None:
            self._rows = []
            self._fastest_lap_driver_id = None
        else:
            self._rows = self._build_rows(race)
            self._fastest_lap_driver_id = self._find_fastest_lap_driver_id()
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
            if index.column() in (0, 3, 4):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == Qt.ItemDataRole.ForegroundRole and index.column() == 3:
            if row["driver"].driver_id == self._fastest_lap_driver_id:
                return QColor("#b86cff")

        if role == Qt.ItemDataRole.UserRole:
            return row["driver"]

        if role == Qt.ItemDataRole.UserRole + 1:
            return row["driver"].name.casefold() == self.player_name.casefold()

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.TextAlignmentRole:
            if section in (0, 3, 4):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        return None

    def _build_rows(self, race: RaceResult) -> list[dict]:
        finishers = sorted(
            (driver for driver in race.classification if _is_finisher(driver)),
            key=lambda driver: _int_or_large(driver.position),
        )
        if not finishers:
            return []

        leader = finishers[0]
        leader_finish_time = _float_or_none(leader.finish_time)
        leader_laps = _int_or_none(leader.laps_completed)

        rows = []
        for driver in finishers:
            rows.append(
                {
                    "driver": driver,
                    "best_lap_seconds": _float_or_none(driver.best_lap_time),
                    "values": [
                        _position_value(driver.position),
                        driver.name or "-",
                        driver.car_type or "-",
                        _format_seconds(driver.best_lap_time),
                        _format_gap(driver, leader, leader_finish_time, leader_laps),
                    ],
                }
            )
        return rows

    def _find_fastest_lap_driver_id(self) -> str | None:
        valid_laps = [
            (row["best_lap_seconds"], row["driver"].driver_id)
            for row in self._rows
            if row["best_lap_seconds"] is not None and row["best_lap_seconds"] > 0
        ]
        if not valid_laps:
            return None
        return min(valid_laps, key=lambda item: item[0])[1]


class RaceLeaderboardDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered_row = -1

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        is_player = bool(index.data(Qt.ItemDataRole.UserRole + 1))
        should_fill = index.row() == self.hovered_row or is_player

        if should_fill:
            painter.save()
            color = "#121f31" if index.row() == self.hovered_row else "#10243a"
            painter.fillRect(option.rect, QColor(color))
            painter.restore()

            option = QStyleOptionViewItem(option)
            option.state &= ~QStyle.StateFlag.State_MouseOver

        super().paint(painter, option, index)

        painter.save()
        pen = QPen(QColor("#7d1f2b"))
        pen.setWidth(1)
        painter.setPen(pen)
        y = option.rect.bottom()
        painter.drawLine(option.rect.left(), y, option.rect.right(), y)
        painter.restore()


class RaceDetailsPage(QWidget):
    back_requested = Signal()

    def __init__(self, player_name: str = DEFAULT_PLAYER_NAME):
        super().__init__()
        self.player_name = player_name
        self.current_race: RaceResult | None = None
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
        self.content_layout.addLayout(self._build_top_section())
        self.content_layout.addWidget(self._build_leaderboard_card())
        self.content_layout.addStretch()

        self.scroll_area.setWidget(content)
        root_layout.addWidget(self.scroll_area)

    def set_race(self, race: RaceResult):
        self.current_race = race
        self.track_label.setText(race.track or "-")
        self.track_name_label.setText(race.track or "-")
        self.class_label.setText(race.player_driver.car_class or "-")
        self.duration_label.setText(race.race_duration or "-")
        self.start_label.setText(race.start_position or "-")
        self.finish_label.setText(race.finish_position or "-")
        self.best_lap_label.setText(race.best_lap or "-")
        self.leaderboard_model.set_race(race)
        self._resize_leaderboard()
        self.scroll_area.verticalScrollBar().setValue(0)
        self._set_hovered_row(-1)

    def _build_heading(self) -> QVBoxLayout:
        heading = QVBoxLayout()
        heading.setSpacing(10)

        self.back_button = QPushButton("← Back to Race History")
        self.back_button.setObjectName("BackButton")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.back_requested.emit)
        self.back_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        eyebrow = QLabel("RACE LOG")
        eyebrow.setObjectName("PageEyebrow")
        title = QLabel("Race Details")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Detailed classification from the selected LMU result file")
        subtitle.setObjectName("PageSubtitle")

        heading.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)
        heading.addWidget(eyebrow)
        heading.addWidget(title)
        heading.addWidget(subtitle)
        return heading

    def _build_top_section(self) -> QHBoxLayout:
        top = QHBoxLayout()
        top.setSpacing(18)

        self.info_card = DashboardCard("Race Info", "You can view the race info here.")
        self.info_card.setMinimumHeight(260)
        self.info_card.body.addLayout(self._build_info_grid())

        self.map_card = DashboardCard("Track Map")
        self.map_card.setMinimumHeight(260)
        self.map_card.body.addStretch()

        map_icon = QLabel()
        map_icon.setObjectName("TrackMapIcon")
        map_icon.setPixmap(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton).pixmap(42, 42))
        map_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.track_name_label = QLabel("-")
        self.track_name_label.setObjectName("TrackMapName")
        self.track_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        coming_soon = QLabel("Track map coming soon")
        coming_soon.setObjectName("MutedText")
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.map_card.body.addWidget(map_icon)
        self.map_card.body.addWidget(self.track_name_label)
        self.map_card.body.addWidget(coming_soon)
        self.map_card.body.addStretch()

        top.addWidget(self.info_card, stretch=2)
        top.addWidget(self.map_card, stretch=1)
        return top

    def _build_info_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(42)
        grid.setVerticalSpacing(20)

        self.track_label = self._add_info_field(grid, 0, 0, "Track")
        self.class_label = self._add_info_field(grid, 1, 0, "Class")
        self.duration_label = self._add_info_field(grid, 0, 1, "Race Duration")
        self.start_label = self._add_info_field(grid, 1, 1, "Start Position")
        self.finish_label = self._add_info_field(grid, 2, 1, "Finish Position")
        self.best_lap_label = self._add_info_field(grid, 3, 1, "Best Lap")

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return grid

    def _add_info_field(self, grid: QGridLayout, row: int, column: int, label: str) -> QLabel:
        field = QWidget()
        layout = QVBoxLayout(field)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label_widget = QLabel(label.upper())
        label_widget.setObjectName("MetricLabel")
        value_widget = QLabel("-")
        value_widget.setObjectName("RaceInfoValue")

        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        grid.addWidget(field, row, column)
        return value_widget

    def _build_leaderboard_card(self) -> DashboardCard:
        card = DashboardCard("Race Leaderboard", "Complete finishing classification")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.leaderboard_model = RaceLeaderboardModel(self.player_name)
        self.leaderboard_table = QTableView()
        self.leaderboard_table.setObjectName("LeaderboardTable")
        self.leaderboard_table.setModel(self.leaderboard_model)
        self.leaderboard_delegate = RaceLeaderboardDelegate(self.leaderboard_table)
        self.leaderboard_table.setItemDelegate(self.leaderboard_delegate)
        self.leaderboard_table.setShowGrid(False)
        self.leaderboard_table.setAlternatingRowColors(False)
        self.leaderboard_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.leaderboard_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.leaderboard_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.leaderboard_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.leaderboard_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.leaderboard_table.verticalHeader().hide()
        self.leaderboard_table.setWordWrap(False)
        self.leaderboard_table.setMouseTracking(True)
        self.leaderboard_table.viewport().setMouseTracking(True)
        self.leaderboard_table.viewport().installEventFilter(self)
        self.leaderboard_table.verticalHeader().setDefaultSectionSize(48)

        header = self.leaderboard_table.horizontalHeader()
        header.setObjectName("RaceHistoryTableHeader")
        header.setStretchLastSection(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        card.body.addWidget(self.leaderboard_table)
        return card

    def _resize_leaderboard(self):
        rows = self.leaderboard_model.rowCount()
        row_height = self.leaderboard_table.verticalHeader().defaultSectionSize()
        header_height = self.leaderboard_table.horizontalHeader().height() or 44
        frame = self.leaderboard_table.frameWidth() * 2
        self.leaderboard_table.setFixedHeight(header_height + frame + (rows * row_height))

    def eventFilter(self, watched, event):
        if watched == self.leaderboard_table.viewport():
            if event.type() == QEvent.Type.MouseMove:
                self._set_hovered_row(self.leaderboard_table.indexAt(event.position().toPoint()).row())
            elif event.type() == QEvent.Type.Leave:
                self._set_hovered_row(-1)

        return super().eventFilter(watched, event)

    def _set_hovered_row(self, row: int):
        if row == self._hovered_row:
            return

        self._hovered_row = row
        self.leaderboard_delegate.hovered_row = row
        self.leaderboard_table.viewport().update()


def _is_finisher(driver: DriverResult) -> bool:
    if _int_or_none(driver.position) is None or _int_or_none(driver.laps_completed) is None:
        return False

    status = driver.finish_status.strip().casefold()
    if not status:
        return _float_or_none(driver.finish_time) is not None

    return status.startswith("finished") or "classified" in status


def _format_gap(
    driver: DriverResult,
    leader: DriverResult,
    leader_finish_time: float | None,
    leader_laps: int | None,
) -> str:
    if driver.driver_id == leader.driver_id:
        return _format_total_time(driver.finish_time)

    driver_laps = _int_or_none(driver.laps_completed)
    if leader_laps is not None and driver_laps is not None:
        lap_delta = leader_laps - driver_laps
        if lap_delta > 0:
            return f"+{lap_delta} Lap" if lap_delta == 1 else f"+{lap_delta} Laps"
        if lap_delta < 0:
            return "-"

    driver_finish_time = _float_or_none(driver.finish_time)
    if leader_finish_time is None or driver_finish_time is None:
        return "-"

    gap = driver_finish_time - leader_finish_time
    if gap < 0:
        return "-"
    return f"+{gap:.3f}s"


def _format_total_time(value: str) -> str:
    formatted = _format_seconds(value)
    return formatted if formatted != "-" else "-"


def _format_seconds(value: str) -> str:
    seconds = _float_or_none(value)
    if seconds is None or seconds <= 0:
        return "-"

    total_milliseconds = round(seconds * 1000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)

    if hours:
        return f"{hours}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"
    return f"{minutes}:{whole_seconds:02d}.{milliseconds:03d}"


def _position_value(value: str) -> str:
    position = _int_or_none(value)
    return str(position) if position and position > 0 else "-"


def _int_or_large(value: str) -> int:
    parsed = _int_or_none(value)
    return parsed if parsed is not None else 9999


def _int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
