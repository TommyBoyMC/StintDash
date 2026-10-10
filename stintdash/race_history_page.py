from pathlib import Path

from PySide6.QtCore import QEvent, QSettings, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
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

from stintdash.lmu_results import DEFAULT_PLAYER_NAME, discover_results_directory, load_lmu_races
from stintdash.race_data import RaceResult
from stintdash.race_history_model import RaceHistoryTableModel


class RaceScanThread(QThread):
    races_loaded = Signal(list, str)

    def __init__(self, results_dir: Path, player_name: str):
        super().__init__()
        self.results_dir = results_dir
        self.player_name = player_name

    def run(self):
        races = load_lmu_races(self.results_dir, self.player_name)
        self.races_loaded.emit(races, str(self.results_dir))


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
    race_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("StintDash", "StintDash")
        self.player_name = self.settings.value("playerName", DEFAULT_PLAYER_NAME, str)
        self.results_dir: Path | None = None
        self._scan_thread: RaceScanThread | None = None
        self.model = RaceHistoryTableModel([])
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
        self.table.clicked.connect(self._open_selected_race)

        self.empty_label = QLabel("No races found.")
        self.empty_label.setObjectName("NoRacesLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()

        layout.addWidget(self.table, stretch=1)
        layout.addWidget(self.empty_label, stretch=1)
        self._update_empty_state()
        self.refresh_races()

    def _build_filters(self) -> QWidget:
        filter_bar = QWidget()

        layout = QHBoxLayout(filter_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.track_filter = self._create_filter_combo(["All Tracks"])
        self.car_filter = self._create_filter_combo(["All Cars"])
        self.position_filter = self._create_filter_combo(["All Positions"])
        self.race_type_filter = self._create_filter_combo(["All Types", "Multiplayer", "Race Weekend"])

        label = QLabel("Filters:")
        label.setObjectName("FilterLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.track_filter, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.car_filter, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.position_filter, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.race_type_filter, 0, Qt.AlignmentFlag.AlignVCenter)

        self.track_filter.currentTextChanged.connect(self._apply_filters)
        self.car_filter.currentTextChanged.connect(self._apply_filters)
        self.position_filter.currentTextChanged.connect(self._apply_filters)
        self.race_type_filter.currentTextChanged.connect(self._apply_filters)

        return filter_bar

    def _create_filter_combo(self, items: list[str]) -> QComboBox:
        combo = QComboBox()
        combo.setObjectName("RaceFilterCombo")
        combo.addItems(items)
        combo.setMaxVisibleItems(5)
        combo.setMinimumWidth(160)
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
            {race.finish_position for race in self.model.all_races if race.finish_position != "-"},
            key=lambda position: int(position.removeprefix("P")),
        )
        return ["All Positions", *positions]

    def refresh_races(self):
        if self._scan_thread is not None and self._scan_thread.isRunning():
            return

        results_dir = self._results_directory()
        if results_dir is None:
            self.model.set_races([])
            self._refresh_filter_options()
            self._update_empty_state()
            return

        self._scan_thread = RaceScanThread(results_dir, self.player_name)
        self._scan_thread.races_loaded.connect(self._on_races_loaded)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        self._scan_thread.finished.connect(self._clear_scan_thread)
        self._scan_thread.start()

    def _results_directory(self) -> Path | None:
        if self.results_dir and self.results_dir.is_dir():
            return self.results_dir

        saved_dir = self.settings.value("resultsDirectory", "", str)
        if saved_dir:
            saved_path = Path(saved_dir)
            if saved_path.is_dir():
                self.results_dir = saved_path
                return saved_path

        discovered_dir = discover_results_directory()
        if discovered_dir:
            self.results_dir = discovered_dir
            self.settings.setValue("resultsDirectory", str(discovered_dir))
            return discovered_dir

        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select LMU Results Folder",
            str(Path.home()),
        )
        if not selected_dir:
            return None

        self.results_dir = Path(selected_dir)
        self.settings.setValue("resultsDirectory", selected_dir)
        return self.results_dir

    def _on_races_loaded(self, races: list[RaceResult], results_dir: str):
        self.results_dir = Path(results_dir)
        self.settings.setValue("resultsDirectory", results_dir)
        self.model.set_races(races)
        self._refresh_filter_options()
        self.table.verticalScrollBar().setValue(0)
        self._load_pending = False
        self._set_hovered_row(-1)
        self._update_empty_state()

    def _refresh_filter_options(self):
        self._set_combo_items(
            self.track_filter,
            ["All Tracks", *sorted({race.track for race in self.model.all_races if race.track != "-"})],
            "All Tracks",
        )
        self._set_combo_items(
            self.car_filter,
            ["All Cars", *sorted({race.car_manufacturer for race in self.model.all_races if race.car_manufacturer != "-"})],
            "All Cars",
        )
        self._set_combo_items(self.position_filter, self._position_filter_options(), "All Positions")
        self._set_combo_items(
            self.race_type_filter,
            ["All Types", "Multiplayer", "Race Weekend"],
            "All Types",
        )

    def _set_combo_items(self, combo: QComboBox, items: list[str], fallback: str):
        current = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        combo.setCurrentText(current if current in items else fallback)
        combo.blockSignals(False)
        self._set_filter_popup_height(combo)
        self._apply_filters()

    def _clear_scan_thread(self):
        self._scan_thread = None

    def _apply_filters(self):
        self.model.set_filters(
            self.track_filter.currentText(),
            self.car_filter.currentText(),
            self.position_filter.currentText(),
            self.race_type_filter.currentText(),
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

    def _open_selected_race(self, index):
        race = self.model.race_at(index.row())
        if race is not None:
            self.race_selected.emit(race)

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
