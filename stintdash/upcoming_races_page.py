from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class UpcomingTrackImage(QWidget):
    def __init__(self):
        super().__init__()
        self._pixmap: QPixmap | None = None
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_pixmap(self, pixmap: QPixmap | None):
        self._pixmap = pixmap if pixmap and not pixmap.isNull() else None
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        radius = 9
        rect = self.rect()
        path = QPainterPath()
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + radius)
        path.quadTo(rect.left(), rect.top(), rect.left() + radius, rect.top())
        path.lineTo(rect.right() - radius, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + radius)
        path.lineTo(rect.right(), rect.bottom())
        path.closeSubpath()

        painter.setClipPath(path)
        if self._pixmap:
            painter.drawPixmap(rect, self._pixmap, _center_crop_source(self._pixmap, self.size()))
        else:
            painter.fillPath(path, QColor("#101827"))


class UpcomingRacesPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(0)

        layout.addLayout(self._build_header())
        layout.addSpacing(30)
        layout.addLayout(self._build_daily_races_row(), stretch=1)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(18)

        heading = QVBoxLayout()
        heading.setSpacing(4)

        title = QLabel("Daily Races")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Upcoming LMU Races")
        subtitle.setObjectName("PageSubtitle")

        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        header.addWidget(self._build_segmented_control(), 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        return header

    def _build_segmented_control(self) -> QFrame:
        segmented = QFrame()
        segmented.setObjectName("SegmentedControl")

        layout = QHBoxLayout(segmented)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        button_group = QButtonGroup(segmented)
        button_group.setExclusive(True)

        for index, label in enumerate(("Daily", "Weekly", "Special Event")):
            button = QPushButton(label)
            button.setObjectName("SegmentButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor if index == 0 else Qt.CursorShape.ArrowCursor)
            button.setEnabled(index == 0)
            if index == 0:
                button.setChecked(True)
            button_group.addButton(button)
            layout.addWidget(button)

        return segmented

    def _build_daily_races_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(18)

        for title in ("Bronze Daily Race", "Silver Daily Race", "Gold Daily Race"):
            row.addWidget(self._build_daily_card(title), stretch=1)

        return row

    def _build_daily_card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("UpcomingRaceCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card.setMinimumHeight(360)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        layout.addWidget(UpcomingTrackImage(), stretch=2)
        layout.addWidget(self._build_race_info(title), stretch=3)
        return card

    def _build_race_info(self, title: str) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("UpcomingRaceTitle")
        class_label_widget = QLabel("Circuit / Car class")
        class_label_widget.setObjectName("UpcomingRaceMeta")
        next_start = QLabel("Next start: --:--")
        next_start.setObjectName("UpcomingRaceTime")
        starts_in = QLabel("Starts in --:--")
        starts_in.setObjectName("UpcomingRaceCountdown")

        layout.addStretch()
        layout.addWidget(title_label)
        layout.addWidget(class_label_widget)
        layout.addSpacing(8)
        layout.addWidget(next_start)
        layout.addWidget(starts_in)
        layout.addStretch()
        return content


def _center_crop_source(pixmap: QPixmap, target_size):
    if pixmap.isNull() or target_size.width() <= 0 or target_size.height() <= 0:
        return pixmap.rect()

    target_ratio = target_size.width() / target_size.height()
    source_ratio = pixmap.width() / pixmap.height()

    if source_ratio > target_ratio:
        source_width = int(pixmap.height() * target_ratio)
        source_x = (pixmap.width() - source_width) // 2
        return pixmap.rect().adjusted(source_x, 0, -(pixmap.width() - source_x - source_width), 0)

    source_height = int(pixmap.width() / target_ratio)
    source_y = (pixmap.height() - source_height) // 2
    return pixmap.rect().adjusted(0, source_y, 0, -(pixmap.height() - source_y - source_height))
