from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
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
    def __init__(self, values: list[int], labels: list[str]):
        super().__init__()
        self.values = values
        self.labels = labels
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        left = 8
        right = 8
        top = 8
        label_space = 24
        chart_height = height - top - label_space - 8
        chart_width = width - left - right
        max_value = max(self.values) if self.values else 1

        grid_pen = QPen(QColor("#1d2b3c"))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for i in range(3):
            y = top + int(chart_height * i / 2)
            painter.drawLine(left, y, width - right, y)

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
