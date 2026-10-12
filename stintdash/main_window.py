import re
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from stintdash.driver_details_page import DriverDetailsPage
from stintdash.race_data import RaceResult
from stintdash.race_details_page import RaceDetailsPage
from stintdash.race_history_page import RaceHistoryPage
from stintdash.track_images import center_crop_source, random_track_picture, track_picture_prefix
from stintdash.upcoming_races_page import UpcomingRacesPage
from stintdash.widgets import CircularAvatar, ClickableDashboardCard, DashboardCard, MetricRow, StaticBarChart


class LatestRacePhotoPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._pixmap: QPixmap | None = None
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_image(self, image_path: Path | None):
        if image_path is None:
            self._pixmap = None
        else:
            pixmap = QPixmap(str(image_path))
            self._pixmap = pixmap if not pixmap.isNull() else None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = 10
        rect = self.rect()
        clip_path = QPainterPath()
        clip_path.moveTo(rect.left(), rect.bottom())
        clip_path.lineTo(rect.left(), rect.top() + radius)
        clip_path.quadTo(rect.left(), rect.top(), rect.left() + radius, rect.top())
        clip_path.lineTo(rect.right() - radius, rect.top())
        clip_path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + radius)
        clip_path.lineTo(rect.right(), rect.bottom())
        clip_path.closeSubpath()
        painter.setClipPath(clip_path)

        if self._pixmap:
            source = center_crop_source(self._pixmap, self.size())
            painter.drawPixmap(self.rect(), self._pixmap, source)
        else:
            painter.fillRect(self.rect(), QColor("#101827"))

        super().paintEvent(event)


class LatestRaceCard(QFrame):
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("LatestRaceCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            """
            QFrame#LatestRaceCard {
                background: #0d1826;
                border: 1px solid #203044;
                border-radius: 10px;
            }

            QFrame#LatestRaceCard:hover {
                border: 1px solid #852235;
            }
            """
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StintDash")
        self.setMinimumSize(QSize(1180, 760))
        self.resize(1280, 800)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_top_bar())

        self.pages = QStackedWidget()
        self.race_history_page = RaceHistoryPage()
        self.race_history_page.model.modelReset.connect(self._update_dashboard_race_cards)
        self.dashboard_page = self._build_dashboard()
        self.upcoming_races_page = UpcomingRacesPage()
        self.race_details_page = RaceDetailsPage(self.race_history_page.player_name)
        self.driver_details_page = DriverDetailsPage()
        self.race_history_page.race_selected.connect(self._open_race_details)
        self.race_details_page.back_requested.connect(self._return_to_race_history)
        self.race_details_page.driver_selected.connect(self._open_driver_details)
        self.driver_details_page.back_requested.connect(self._return_to_race_details)
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.race_history_page)
        self.pages.addWidget(self.upcoming_races_page)
        self.pages.addWidget(self.race_details_page)
        self.pages.addWidget(self.driver_details_page)

        layout.addWidget(self.pages)
        self._set_active_page(0)

    def _build_top_bar(self) -> QFrame:
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(76)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(26, 0, 26, 0)
        layout.setSpacing(26)

        logo_area = QHBoxLayout()
        logo_area.setSpacing(11)

        logo_mark = QFrame()
        logo_mark.setObjectName("LogoMark")
        logo_mark.setFixedSize(36, 36)
        logo_layout = QHBoxLayout(logo_mark)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_letters = QLabel("SD")
        logo_letters.setObjectName("LogoLetters")
        logo_letters.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_letters)

        logo_text = QLabel("StintDash")
        logo_text.setObjectName("LogoText")

        logo_area.addWidget(logo_mark)
        logo_area.addWidget(logo_text)
        layout.addLayout(logo_area)

        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)

        self.dashboard_nav = QPushButton("Dashboard")
        self.dashboard_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dashboard_nav.clicked.connect(lambda: self._set_active_page(0))
        nav_layout.addWidget(self.dashboard_nav)

        self.race_history_nav = QPushButton("Race History")
        self.race_history_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.race_history_nav.clicked.connect(lambda: self._set_active_page(1))
        nav_layout.addWidget(self.race_history_nav)

        self.upcoming_races_nav = QPushButton("Upcoming Races")
        self.upcoming_races_nav.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upcoming_races_nav.clicked.connect(lambda: self._set_active_page(2))
        nav_layout.addWidget(self.upcoming_races_nav)

        for label in ("Championship", "Statistics"):
            button = QPushButton(label)
            button.setObjectName("NavInactive")
            button.setEnabled(False)
            button.setCursor(Qt.CursorShape.ArrowCursor)
            nav_layout.addWidget(button)

        layout.addLayout(nav_layout)
        layout.addStretch()

        settings = QPushButton()
        settings.setObjectName("SettingsButton")
        settings.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        settings.setIconSize(QSize(18, 18))
        settings.setFixedSize(36, 36)
        settings.setCursor(Qt.CursorShape.ArrowCursor)
        layout.addWidget(settings)

        profile = QFrame()
        profile.setObjectName("ProfileBox")
        profile.setFixedHeight(42)
        profile_layout = QHBoxLayout(profile)
        profile_layout.setContentsMargins(5, 4, 14, 4)
        profile_layout.setSpacing(9)

        avatar = CircularAvatar("T", 32)

        username = QLabel("Tom Ridder")
        username.setObjectName("Username")

        profile_layout.addWidget(avatar)
        profile_layout.addWidget(username)
        layout.addWidget(profile)

        return top_bar

    def _set_active_page(self, page_index: int):
        self.pages.setCurrentIndex(page_index)
        if page_index in (0, 1):
            self.race_history_page.refresh_races()
        if page_index == 0:
            self._update_dashboard_race_cards()

        self._sync_nav_buttons(page_index if page_index in (0, 1, 2) else 1)

    def _open_upcoming_races(self):
        self._set_active_page(2)

    def _open_race_details(self, race):
        self.race_details_page.set_race(race)
        self.pages.setCurrentWidget(self.race_details_page)
        self._sync_nav_buttons(1)

    def _open_driver_details(self, race, driver):
        self.driver_details_page.set_driver(race, driver)
        self.pages.setCurrentWidget(self.driver_details_page)
        self._sync_nav_buttons(1)

    def _return_to_race_details(self):
        self.pages.setCurrentWidget(self.race_details_page)
        self._sync_nav_buttons(1)

    def _return_to_race_history(self):
        self.pages.setCurrentWidget(self.race_history_page)
        self._sync_nav_buttons(1)

    def _sync_nav_buttons(self, active_page_index: int):
        buttons = (
            (self.dashboard_nav, 0),
            (self.race_history_nav, 1),
            (self.upcoming_races_nav, 2),
        )
        for button, page_index in buttons:
            button.setObjectName("NavActive" if page_index == active_page_index else "NavInactive")
            button.style().unpolish(button)
            button.style().polish(button)

    def _build_dashboard(self) -> QWidget:
        dashboard = QWidget()
        dashboard.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        page_layout = QVBoxLayout(dashboard)
        page_layout.setContentsMargins(30, 26, 30, 30)
        page_layout.setSpacing(22)

        heading = QVBoxLayout()
        heading.setSpacing(4)

        eyebrow = QLabel("LE MANS ULTIMATE COMPANION")
        eyebrow.setObjectName("PageEyebrow")
        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Static home layout preview with placeholder racing data.")
        subtitle.setObjectName("PageSubtitle")

        heading.addWidget(eyebrow)
        heading.addWidget(title)
        heading.addWidget(subtitle)
        page_layout.addLayout(heading)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)

        grid.addWidget(self._latest_race_card(), 0, 0, 2, 1)
        grid.addWidget(self._next_daily_race_card(), 0, 1, 1, 1)
        grid.addWidget(self._career_summary_card(), 0, 2, 1, 1)
        grid.addWidget(self._weekly_driving_time_card(), 1, 1, 2, 1)
        grid.addWidget(self._most_driven_track_card(), 1, 2, 1, 1)
        grid.addWidget(self._most_driven_car_card(), 2, 0, 1, 1)
        grid.addWidget(self._status_card(), 2, 2, 1, 1)

        page_layout.addLayout(grid, stretch=1)
        return dashboard

    def _latest_race_card(self) -> QFrame:
        card = LatestRaceCard()
        card.clicked.connect(self._open_latest_race_details)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.latest_race_photo = LatestRacePhotoPanel()
        layout.addWidget(self.latest_race_photo, stretch=55)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(20, 12, 20, 14)
        bottom_layout.setSpacing(7)

        self.latest_result_value = QLabel("—")
        self.latest_best_lap_value = QLabel("—")
        self.latest_track_value = QLabel("—")
        self.latest_type_value = QLabel("—")
        self.latest_race_image_key: str | None = None
        self.latest_race_image_path: Path | None = None

        title = QLabel("Latest Race")
        title.setObjectName("CardTitle")

        bottom_layout.addWidget(title)
        bottom_layout.addSpacing(2)
        bottom_layout.addLayout(self._latest_race_row("Result", self.latest_result_value))
        bottom_layout.addLayout(self._latest_race_row("Best Lap", self.latest_best_lap_value))
        bottom_layout.addLayout(self._latest_race_row("Track", self.latest_track_value))
        bottom_layout.addLayout(self._latest_race_row("Type", self.latest_type_value))
        bottom_layout.addStretch()

        layout.addWidget(bottom, stretch=45)
        self._update_latest_race_card()
        return card

    def _update_dashboard_race_cards(self):
        self._update_latest_race_card()
        self._update_career_summary_card()
        self._update_multiplayer_dashboard_stats()

    def _latest_race_row(self, label: str, value_label: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        label_widget = QLabel(label.upper())
        label_widget.setObjectName("MetricLabel")
        value_label.setObjectName("MetricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        row.addWidget(label_widget)
        row.addStretch()
        row.addWidget(value_label)
        return row

    def _update_latest_race_card(self):
        if not hasattr(self, "latest_race_photo"):
            return

        latest_race = self.race_history_page.model.all_races[0] if self.race_history_page.model.all_races else None
        self.latest_race = latest_race
        self.latest_result_value.setText(_display_value(latest_race.finish_position if latest_race else ""))
        self.latest_best_lap_value.setText(_display_value(latest_race.best_lap if latest_race else ""))
        self.latest_track_value.setText(_display_value(latest_race.track if latest_race else ""))
        self.latest_type_value.setText(_display_value(latest_race.race_type if latest_race else ""))

        image_key = _latest_race_image_key(latest_race)
        if image_key != self.latest_race_image_key:
            self.latest_race_image_key = image_key
            self.latest_race_image_path = _random_track_picture(latest_race)
        self.latest_race_photo.set_image(self.latest_race_image_path)

    def _open_latest_race_details(self):
        if getattr(self, "latest_race", None) is None:
            return

        self._open_race_details(self.latest_race)

    def _next_daily_race_card(self) -> DashboardCard:
        card = ClickableDashboardCard("Next Daily Race", "Scheduled placeholder")
        card.clicked.connect(self._open_upcoming_races)
        card.body.addWidget(MetricRow("Starts in", "42 minutes"))
        card.body.addWidget(MetricRow("Track", "Monza"))
        card.body.addStretch()
        return card

    def _career_summary_card(self) -> DashboardCard:
        card = DashboardCard("Career Summary", "Quick multiplayer stats.")
        stats = QHBoxLayout()
        stats.setSpacing(10)
        wins_pill, self.career_wins_value = self._career_stat_pill("Wins")
        podiums_pill, self.career_podiums_value = self._career_stat_pill("Podiums")
        fastest_laps_pill, self.career_fastest_laps_value = self._career_stat_pill("Fastest Laps")
        stats.addWidget(wins_pill)
        stats.addWidget(podiums_pill)
        stats.addWidget(fastest_laps_pill)
        card.body.addLayout(stats, stretch=1)
        self._update_career_summary_card()
        return card

    def _career_stat_pill(self, label: str) -> tuple[QFrame, QLabel]:
        pill = QFrame()
        pill.setObjectName("StatPill")
        pill.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(pill)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        value_label = QLabel("0")
        value_label.setObjectName("RedMetricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label_widget = QLabel(label.upper())
        label_widget.setObjectName("MetricLabel")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(value_label)
        layout.addWidget(label_widget)
        layout.addStretch()
        return pill, value_label

    def _update_career_summary_card(self):
        if not hasattr(self, "career_wins_value"):
            return

        wins, podiums, fastest_laps = _career_summary_stats(self.race_history_page.model.all_races)
        self.career_wins_value.setText(str(wins))
        self.career_podiums_value.setText(str(podiums))
        self.career_fastest_laps_value.setText(str(fastest_laps))

    def _weekly_driving_time_card(self) -> DashboardCard:
        card = DashboardCard("Weekly Races Driven", "Last 7 days")
        values, labels, axis_labels, max_value = _weekly_multiplayer_races(self.race_history_page.model.all_races)
        self.weekly_races_chart = StaticBarChart(values=values, labels=labels, axis_labels=axis_labels, max_value=max_value)
        card.body.addWidget(self.weekly_races_chart, stretch=1)
        self._update_multiplayer_dashboard_stats()
        return card

    def _most_driven_track_card(self) -> DashboardCard:
        card = DashboardCard("Most Driven Track", "By total sessions")
        self.most_driven_track_value = QLabel("—")
        self.most_driven_track_value.setObjectName("TrackValue")
        self.most_driven_track_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.most_driven_track_count = QLabel("No multiplayer races")
        self.most_driven_track_count.setObjectName("MetricLabel")
        self.most_driven_track_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.body.addStretch()
        card.body.addWidget(self.most_driven_track_value)
        card.body.addWidget(self.most_driven_track_count)
        card.body.addStretch()
        self._update_multiplayer_dashboard_stats()
        return card

    def _most_driven_car_card(self) -> DashboardCard:
        card = DashboardCard("Most Driven Car", "By total sessions")
        self.most_driven_car_value = QLabel("—")
        self.most_driven_car_value.setObjectName("CarValue")
        self.most_driven_car_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.most_driven_car_count = QLabel("No multiplayer races")
        self.most_driven_car_count.setObjectName("MetricLabel")
        self.most_driven_car_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.body.addStretch()
        card.body.addWidget(self.most_driven_car_value)
        card.body.addWidget(self.most_driven_car_count)
        card.body.addStretch()
        self._update_multiplayer_dashboard_stats()
        return card

    def _update_multiplayer_dashboard_stats(self):
        if hasattr(self, "most_driven_track_value"):
            track, count = _most_common_multiplayer_value(self.race_history_page.model.all_races, _track_stat_key)
            self.most_driven_track_value.setText(track or "—")
            self.most_driven_track_count.setText(_race_count_label(count))

        if hasattr(self, "most_driven_car_value"):
            car, count = _most_common_multiplayer_value(self.race_history_page.model.all_races, _car_stat_key)
            self.most_driven_car_value.setText(car or "—")
            self.most_driven_car_count.setText(_race_count_label(count))

        if hasattr(self, "weekly_races_chart"):
            values, labels, axis_labels, max_value = _weekly_multiplayer_races(self.race_history_page.model.all_races)
            self.weekly_races_chart.set_data(values, labels, axis_labels, max_value)

    def _status_card(self) -> DashboardCard:
        card = DashboardCard("Dashboard Status", "Design preview")

        message = QLabel("Navigation is visible for context. Only this Dashboard screen exists in the first mockup.")
        message.setObjectName("MutedText")
        message.setWordWrap(True)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)

        card.body.addWidget(message)
        card.body.addWidget(divider)
        card.body.addWidget(MetricRow("Build phase", "Static UI"))
        card.body.addStretch()
        return card


def _display_value(value: str) -> str:
    return value if value and value != "-" else "—"


def _latest_race_image_key(race: RaceResult | None) -> str | None:
    if race is None:
        return None
    return race.race_id or str(race.source_file)


def _career_summary_stats(races: list[RaceResult]) -> tuple[int, int, int]:
    wins = 0
    podiums = 0
    fastest_laps = 0
    seen_race_ids = set()

    for race in races:
        race_key = race.race_id or str(race.source_file)
        if race_key in seen_race_ids or not _is_multiplayer_race(race):
            continue

        seen_race_ids.add(race_key)
        finish_position = _player_class_finish_position(race)
        if finish_position == 1:
            wins += 1
        if finish_position is not None and finish_position <= 3:
            podiums += 1
        if _player_has_class_fastest_lap(race):
            fastest_laps += 1

    return wins, podiums, fastest_laps


def _unique_multiplayer_races(races: list[RaceResult]) -> list[RaceResult]:
    unique_races = []
    seen_race_ids = set()
    for race in races:
        race_key = race.race_id or str(race.source_file)
        if race_key in seen_race_ids or not _is_multiplayer_race(race):
            continue

        seen_race_ids.add(race_key)
        unique_races.append(race)
    return unique_races


def _most_common_multiplayer_value(races: list[RaceResult], value_func) -> tuple[str, int]:
    counts = Counter()
    display_values = {}
    for race in _unique_multiplayer_races(races):
        key, display = value_func(race)
        if not key:
            continue

        counts[key] += 1
        display_values[key] = display

    if not counts:
        return "", 0

    highest_count = max(counts.values())
    tied_keys = sorted(key for key, count in counts.items() if count == highest_count)
    selected_key = tied_keys[0]
    return display_values[selected_key], highest_count


def _track_stat_key(race: RaceResult) -> tuple[str, str]:
    track = race.track.strip()
    if not track or track == "-":
        return "", ""

    prefix = track_picture_prefix(track)
    key = prefix.casefold() if prefix else re.sub(r"[^a-z0-9]+", "", track.casefold())
    return key, track


def _car_stat_key(race: RaceResult) -> tuple[str, str]:
    manufacturer = _lmu_car_manufacturer(race)
    if not manufacturer:
        return "", ""

    key = re.sub(r"[^a-z0-9]+", "", manufacturer.casefold())
    return key, manufacturer


def _lmu_car_manufacturer(race: RaceResult) -> str:
    car = race.car.strip()
    parsed_manufacturer = race.car_manufacturer.strip()
    manufacturer_source = f"{car} {parsed_manufacturer}".casefold()
    if not car or car == "-":
        return ""

    known_manufacturers = (
        ("corvette", "Corvette"),
        ("chevrolet", "Corvette"),
        ("aston martin", "Aston Martin"),
        ("mclaren", "McLaren"),
        ("mercedes", "Mercedes"),
        ("lamborghini", "Lamborghini"),
        ("porsche", "Porsche"),
        ("ferrari", "Ferrari"),
        ("lexus", "Lexus"),
        ("ford", "Ford"),
        ("bmw", "BMW"),
    )
    for match, display in known_manufacturers:
        if match in manufacturer_source:
            return display

    if parsed_manufacturer and parsed_manufacturer != "-":
        return parsed_manufacturer
    return car.split()[0]


def _race_count_label(count: int) -> str:
    if count <= 0:
        return "No multiplayer races"
    return "1 race" if count == 1 else f"{count} races"


def _weekly_multiplayer_races(races: list[RaceResult]) -> tuple[list[int], list[str], tuple[str, str, str], float]:
    today = date.today()
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    counts = {day: 0 for day in days}

    for race in _unique_multiplayer_races(races):
        race_day = race.sort_datetime.date()
        if race_day in counts:
            counts[race_day] += 1

    values = [counts[day] for day in days]
    labels = [day.strftime("%a") for day in days[:-1]] + ["Tdy"]
    max_value = _weekly_axis_max(max(values, default=0))
    axis_labels = ("0", _format_axis_tick(max_value / 2), _format_axis_tick(max_value))
    return values, labels, axis_labels, max_value


def _weekly_axis_max(total: int) -> float:
    if total < 5:
        return 5.0

    max_value = 10
    while total > max_value:
        max_value *= 2
    return float(max_value)


def _format_axis_tick(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:g}"


def _is_multiplayer_race(race: RaceResult) -> bool:
    return race.race_type.strip().casefold() == "multiplayer"


def _player_class_finish_position(race: RaceResult) -> int | None:
    class_position = _int_or_none(race.player_driver.class_position)
    if class_position is not None and class_position > 0:
        return class_position

    overall_position = _int_or_none(race.player_driver.position)
    if overall_position is not None and overall_position > 0:
        return overall_position
    return None


def _player_has_class_fastest_lap(race: RaceResult) -> bool:
    player_best = _float_or_none(race.player_driver.best_lap_time)
    if player_best is None or player_best <= 0:
        return False

    player_class = race.player_driver.car_class.strip().casefold()
    relevant_laps = []
    for driver in race.classification:
        if player_class and driver.car_class.strip().casefold() != player_class:
            continue

        best_lap = _float_or_none(driver.best_lap_time)
        if best_lap is not None and best_lap > 0:
            relevant_laps.append(best_lap)

    if not relevant_laps:
        return False
    return abs(player_best - min(relevant_laps)) <= 1e-9


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


def _random_track_picture(race: RaceResult | None) -> Path | None:
    if race is None:
        return None

    return random_track_picture(race.track)
