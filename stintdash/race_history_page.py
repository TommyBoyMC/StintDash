from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListView,
    QStyle,
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered_row = -1

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        if index.row() == self.hovered_row:
            painter.save()
            painter.fillRect(option.rect, QColor("#121f31"))
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


class RaceHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.model = RaceHistoryTableModel(create_sample_race_results())
        self._load_pending = False
        self._hovered_row = -1

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

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(18)
        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(self._build_filters(), 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        heading.addWidget(eyebrow)
        heading.addLayout(title_row)
        heading.addWidget(subtitle)
        layout.addLayout(heading)

        self.table = QTableView()
        self.table.setObjectName("RaceHistoryTable")
        self.table.setModel(self.model)
        self.table_delegate = RaceHistoryDelegate(self.table)
        self.table.setItemDelegate(self.table_delegate)
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
        self.table.viewport().setMouseTracking(True)
        self.table.viewport().installEventFilter(self)

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

    def _build_filters(self) -> QWidget:
        filter_bar = QWidget()

        layout = QHBoxLayout(filter_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.track_filter = self._create_filter_combo(TRACK_FILTERS)
        self.car_filter = self._create_filter_combo(CAR_FILTERS)
        self.position_filter = self._create_filter_combo(self._position_filter_options())

        label = QLabel("Filters:")
        label.setObjectName("FilterLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.track_filter, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.car_filter, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.position_filter, 0, Qt.AlignmentFlag.AlignVCenter)

        self.track_filter.currentTextChanged.connect(self._apply_filters)
        self.car_filter.currentTextChanged.connect(self._apply_filters)
        self.position_filter.currentTextChanged.connect(self._apply_filters)

        return filter_bar

    def _create_filter_combo(self, items: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName("RaceFilterCombo")
        combo.addItems(items)
        combo.setMaxVisibleItems(5)
        combo.setMinimumWidth(190)
        combo.setView(QListView())
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        combo.view().setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._set_filter_popup_height(combo)
        return combo

    def _set_filter_popup_height(self, combo: QComboBox):
        view = combo.view()
        view.ensurePolished()

        visible_rows = min(5, combo.count())
        if visible_rows == 0:
            return

        fallback_item_height = max(30, combo.fontMetrics().height()) + 14
        item_heights = [
            max(view.sizeHintForRow(row), fallback_item_height)
            for row in range(visible_rows)
        ]
        popup_padding = 8
        popup_border = view.frameWidth() * 2
        view.setFixedHeight(sum(item_heights) + popup_padding + popup_border)

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
        self._set_hovered_row(-1)

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

    def eventFilter(self, watched, event):
        if watched == self.table.viewport():
            if event.type() == QEvent.Type.MouseMove:
                self._set_hovered_row(self.table.indexAt(event.position().toPoint()).row())
            elif event.type() == QEvent.Type.Leave:
                self._set_hovered_row(-1)

        return super().eventFilter(watched, event)

    def _set_hovered_row(self, row: int):
        if row == self._hovered_row:
            return

        old_row = self._hovered_row
        self._hovered_row = row
        self.table_delegate.hovered_row = row

        if old_row >= 0:
            self.table.viewport().update()

        if row >= 0:
            self.table.viewport().update()
