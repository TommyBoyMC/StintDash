from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from stintdash.race_data import create_sample_race_results
from stintdash.race_history_model import RaceHistoryTableModel


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
        horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        horizontal_header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalScrollBar().valueChanged.connect(self._maybe_load_more)

        layout.addWidget(self.table, stretch=1)

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
