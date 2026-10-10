from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from stintdash.race_data import create_sample_race_results
from stintdash.race_history_model import RaceHistoryTableModel


TRACK_FILTERS = [
    "All Tracks",
    "Bahrain",
    "Barcelona",
    "Le Mans",
    "Paul Ricard",
    "COTA",
    "Daytona",
    "Fuji",
    "Imola",
    "Interlagos",
    "Lusail",
    "Road Atlanta",
    "Monza",
    "Portimao",
    "Sebring",
    "Silverstone",
    "Spa-Francorchamps",
    "Longbeach",
    "Laguna Seca",
]

CAR_FILTERS = [
    "All Cars",
    "Ford",
    "McLaren",
    "Mercedes",
    "BMW",
    "Aston Martin",
    "Corvette",
    "Ferrari",
    "Lamborghini",
    "Lexus",
    "Porsche",
]


class RaceHistoryDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        super().paint(painter, option, index)

        painter.save()
        pen = QPen(QColor("#7d1f2b"))
        pen.setWidth(1)
        painter.setPen(pen)
        y = option.rect.bottom()
        painter.drawLine(option.rect.left(), y, option.rect.right(), y)
        painter.restore()


class RaceHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.model = RaceHistoryTableModel(create_sample_race_results())
        self._load_pending = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(22)

        heading = QVBoxLayout()
        heading.setSpacing(4)

        eyebrow = QLabel("RACE LOG")
        eyebrow.setObjectName("PageEyebrow")
        title = QLabel("Race History")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Your previous races and results")
        subtitle.setObjectName("PageSubtitle")

        heading.addWidget(eyebrow)
        heading.addWidget(title)
        heading.addWidget(subtitle)
        layout.addLayout(heading)

        layout.addWidget(self._build_filters())

        self.table = QTableView()
        self.table.setObjectName("RaceHistoryTable")
        self.table.setModel(self.model)
        self.table.setItemDelegate(RaceHistoryDelegate(self.table))
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.verticalHeader().hide()
        self.table.setWordWrap(False)
        self.table.setMouseTracking(True)

        horizontal_header = self.table.horizontalHeader()
        horizontal_header.setObjectName("RaceHistoryTableHeader")
        horizontal_header.setStretchLastSection(False)
        horizontal_header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalScrollBar().valueChanged.connect(self._maybe_load_more)

        self.empty_label = QLabel("No races found.")
        self.empty_label.setObjectName("NoRacesLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()

        layout.addWidget(self.table, stretch=1)
        layout.addWidget(self.empty_label, stretch=1)

    def _build_filters(self) -> QFrame:
        filter_bar = QFrame()
        filter_bar.setObjectName("FilterBar")

        layout = QHBoxLayout(filter_bar)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        self.track_filter = self._create_filter_combo(TRACK_FILTERS)
        self.car_filter = self._create_filter_combo(CAR_FILTERS)
        self.position_filter = self._create_filter_combo(self._position_filter_options())

        layout.addWidget(self._filter_group("Track", self.track_filter))
        layout.addWidget(self._filter_group("Car", self.car_filter))
        layout.addWidget(self._filter_group("Position", self.position_filter))
        layout.addStretch()

        self.track_filter.currentTextChanged.connect(self._apply_filters)
        self.car_filter.currentTextChanged.connect(self._apply_filters)
        self.position_filter.currentTextChanged.connect(self._apply_filters)

        return filter_bar

    def _filter_group(self, label: str, combo: QComboBox) -> QWidget:
        group = QWidget()
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        text = QLabel(label.upper())
        text.setObjectName("FilterLabel")
        layout.addWidget(text)
        layout.addWidget(combo)
        return group

    def _create_filter_combo(self, items: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName("RaceFilterCombo")
        combo.addItems(items)
        combo.setMaxVisibleItems(4)
        combo.setMinimumWidth(190)
        combo.setView(QListView())
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        combo.view().setFixedHeight(4 * 34 + 2)
        return combo

    def _position_filter_options(self) -> list[str]:
        positions = sorted(
            {race.finish_position for race in self.model.all_races},
            key=lambda position: int(position.removeprefix("P")),
        )
        return ["All Positions", *positions]

    def _apply_filters(self):
        self.model.set_filters(
            self.track_filter.currentText(),
            self.car_filter.currentText(),
            self.position_filter.currentText(),
        )
        self.table.verticalScrollBar().setValue(0)
        self._load_pending = False
        self._update_empty_state()

    def _update_empty_state(self):
        has_rows = self.model.rowCount() > 0
        self.table.setVisible(has_rows)
        self.empty_label.setVisible(not has_rows)

    def _maybe_load_more(self, value: int):
        scrollbar = self.table.verticalScrollBar()
        if self._load_pending or not self.model.can_load_more():
            return

        if scrollbar.maximum() - value > 180:
            return

        self._load_pending = True
        QTimer.singleShot(0, self._append_next_batch)

    def _append_next_batch(self):
        self.model.load_more()
        self._load_pending = False
