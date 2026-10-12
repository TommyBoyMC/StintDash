from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


class DashboardCard(QFrame):
    def __init__(self, title: str, subtitle: str | None = None, highlight: bool = False):
        super().__init__()
        self.setObjectName("DashboardCard")
        if highlight:
            self.setProperty("highlight", True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(20, 18, 20, 18)
        self.body.setSpacing(14)

        header = QVBoxLayout()
        header.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        header.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("CardKicker")
            header.addWidget(subtitle_label)

        self.body.addLayout(header)


class ClickableDashboardCard(DashboardCard):
    clicked = Signal()

    def __init__(self, title: str, subtitle: str | None = None, highlight: bool = False):
        super().__init__(title, subtitle, highlight)
        self.setProperty("clickable", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MetricRow(QWidget):
    def __init__(self, label: str, value: str):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        label_widget = QLabel(label.upper())
        label_widget.setObjectName("MetricLabel")
        value_widget = QLabel(value)
        value_widget.setObjectName("MetricValue")
        value_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)


class StatPill(QFrame):
    def __init__(self, label: str, value: str):
        super().__init__()
        self.setObjectName("StatPill")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("RedMetricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label_widget = QLabel(label.upper())
        label_widget.setObjectName("MetricLabel")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(value_label)
        layout.addWidget(label_widget)
        layout.addStretch()


class StaticBarChart(QWidget):
    def __init__(self, values: list[int], labels: list[str], axis_labels: tuple[str, str, str] | None = None, max_value: float | None = None):
        super().__init__()
        self.values = values
        self.labels = labels
        self.axis_labels = axis_labels
        self.max_value = max_value
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, values: list[int], labels: list[str], axis_labels: tuple[str, str, str] | None = None, max_value: float | None = None):
        self.values = values
        self.labels = labels
        self.axis_labels = axis_labels
        self.max_value = max_value
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        left = 34 if self.axis_labels else 8
        right = 8
        top = 8
        label_space = 24
        chart_height = height - top - label_space - 8
        chart_width = width - left - right
        max_value = self.max_value if self.max_value else (max(self.values) if self.values else 1)

        grid_pen = QPen(QColor("#1d2b3c"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for i in range(3):
            y = top + int(chart_height * i / 2)
            painter.drawLine(left, y, width - right, y)
            if self.axis_labels:
                painter.setPen(QColor("#7c8a9b"))
                painter.drawText(0, y - 8, left - 6, 16, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self.axis_labels[2 - i])
                painter.setPen(grid_pen)

        slot = chart_width / len(self.values)
        bar_width = min(28, slot * 0.42)

        for index, value in enumerate(self.values):
            x = left + slot * index + (slot - bar_width) / 2
            bar_height = chart_height * (value / max_value)
            y = top + chart_height - bar_height

            bar_color = QColor("#e21b2f" if index in (4, 5) else "#2e8dff")
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bar_color)
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), 4, 4)

            painter.setPen(QColor("#7c8a9b"))
            painter.drawText(
                int(left + slot * index),
                height - 16,
                int(slot),
                16,
                Qt.AlignmentFlag.AlignCenter,
                self.labels[index],
            )


class CircularAvatar(QWidget):
    def __init__(self, fallback_text: str, size: int = 32):
        super().__init__()
        self._pixmap: QPixmap | None = None
        self._fallback_text = fallback_text
        self.setObjectName("ProfileAvatar")
        self.setFixedSize(size, size)

    def set_pixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        side = min(self.width(), self.height())
        rect_x = (self.width() - side) / 2
        rect_y = (self.height() - side) / 2

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addEllipse(rect_x, rect_y, side, side)
        painter.setClipPath(path)

        if self._pixmap and not self._pixmap.isNull():
            source_side = min(self._pixmap.width(), self._pixmap.height())
            source_x = (self._pixmap.width() - source_side) // 2
            source_y = (self._pixmap.height() - source_side) // 2
            cropped = self._pixmap.copy(source_x, source_y, source_side, source_side)
            painter.drawPixmap(0, 0, int(side), int(side), cropped)
        else:
            painter.fillPath(path, QColor("#e21b2f"))
            painter.setPen(QColor("#ffffff"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._fallback_text)

        painter.setClipping(False)
        pen = QPen(QColor("#ff4052"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawEllipse(int(rect_x), int(rect_y), int(side) - 1, int(side) - 1)
