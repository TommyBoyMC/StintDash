from PySide6.QtCore import QSize, Qt
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

from stintdash.race_details_page import RaceDetailsPage
from stintdash.race_history_page import RaceHistoryPage
from stintdash.widgets import CircularAvatar, DashboardCard, MetricRow, StaticBarChart, StatPill


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
        self.dashboard_page = self._build_dashboard()
        self.race_history_page = RaceHistoryPage()
        self.race_details_page = RaceDetailsPage(self.race_history_page.player_name)
        self.race_history_page.race_selected.connect(self._open_race_details)
        self.race_details_page.back_requested.connect(self._return_to_race_history)
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.race_history_page)
        self.pages.addWidget(self.race_details_page)

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
        if page_index == 1:
            self.race_history_page.refresh_races()

        self._sync_nav_buttons(0 if page_index == 0 else 1)

    def _open_race_details(self, race):
        self.race_details_page.set_race(race)
        self.pages.setCurrentWidget(self.race_details_page)
        self._sync_nav_buttons(1)

    def _return_to_race_history(self):
        self.pages.setCurrentWidget(self.race_history_page)
        self._sync_nav_buttons(1)

    def _sync_nav_buttons(self, active_page_index: int):
        active_button = self.dashboard_nav if active_page_index == 0 else self.race_history_nav
        inactive_button = self.race_history_nav if active_page_index == 0 else self.dashboard_nav

        active_button.setObjectName("NavActive")
        inactive_button.setObjectName("NavInactive")

        for button in (active_button, inactive_button):
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

    def _latest_race_card(self) -> DashboardCard:
        card = DashboardCard("Latest Race", "Most recent session result", highlight=True)

        result = QLabel("P5")
        result.setObjectName("LargeMetricValue")
        result.setAlignment(Qt.AlignmentFlag.AlignLeft)

        result_label = QLabel("RESULT")
        result_label.setObjectName("MetricLabel")

        card.body.addStretch()
        card.body.addWidget(result_label)
        card.body.addWidget(result)
        card.body.addSpacing(12)
        card.body.addWidget(MetricRow("Best Lap", "1:58.427"))
        card.body.addWidget(MetricRow("Track", "Spa-Francorchamps"))
        card.body.addStretch()
        return card

    def _next_daily_race_card(self) -> DashboardCard:
        card = DashboardCard("Next Daily Race", "Scheduled placeholder")
        card.body.addWidget(MetricRow("Starts in", "42 minutes"))
        card.body.addWidget(MetricRow("Track", "Monza"))
        card.body.addStretch()
        return card

    def _career_summary_card(self) -> DashboardCard:
        card = DashboardCard("Career Summary", "Quick stats")
        stats = QHBoxLayout()
        stats.setSpacing(10)
        stats.addWidget(StatPill("Wins", "0"))
        stats.addWidget(StatPill("Podiums", "5"))
        stats.addWidget(StatPill("Fastest Laps", "3"))
        card.body.addLayout(stats, stretch=1)
        return card

    def _weekly_driving_time_card(self) -> DashboardCard:
        card = DashboardCard("Weekly Driving Time", "Last 7 days")
        chart = StaticBarChart(
            values=[35, 55, 44, 68, 92, 78, 50],
            labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        )
        card.body.addWidget(chart, stretch=1)
        return card

    def _most_driven_track_card(self) -> DashboardCard:
        card = DashboardCard("Most Driven Track", "By total sessions")
        value = QLabel("Sebring")
        value.setObjectName("TrackValue")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.body.addStretch()
        card.body.addWidget(value)
        card.body.addStretch()
        return card

    def _most_driven_car_card(self) -> DashboardCard:
        card = DashboardCard("Most Driven Car", "By total sessions")
        value = QLabel("Corvette")
        value.setObjectName("CarValue")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.body.addStretch()
        card.body.addWidget(value)
        card.body.addStretch()
        return card

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
