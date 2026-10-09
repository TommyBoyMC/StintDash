APP_STYLESHEET = """
* {
    font-family: "Segoe UI", "Inter", "Arial";
    color: #eef3f8;
}

QMainWindow,
QWidget#Root {
    background: #07101b;
}

QFrame#TopBar {
    background: #0a1421;
    border-bottom: 1px solid #18283a;
}

QFrame#LogoMark,
QFrame#ProfileAvatar {
    background: #e21b2f;
    border: 1px solid #ff4052;
    border-radius: 18px;
}

QLabel#LogoText {
    color: #ffffff;
    font-size: 21px;
    font-weight: 800;
    letter-spacing: 0px;
}

QLabel#LogoLetters,
QLabel#AvatarLetters {
    color: #ffffff;
    font-weight: 900;
}

QPushButton#NavActive {
    background: #e21b2f;
    color: #ffffff;
    border: 1px solid #ff4052;
    border-radius: 7px;
    padding: 9px 16px;
    font-size: 13px;
    font-weight: 800;
}

QPushButton#NavInactive {
    background: transparent;
    color: #718094;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 9px 14px;
    font-size: 13px;
    font-weight: 700;
}

QPushButton#NavInactive:hover {
    background: #101c2c;
    color: #dce6ef;
    border: 1px solid #1f2f43;
}

QPushButton#NavInactive:disabled {
    background: transparent;
    color: #4f5e70;
    border: 1px solid transparent;
}

QPushButton#SettingsButton {
    background: #101c2c;
    border: 1px solid #22344a;
    border-radius: 17px;
    color: #dce6ef;
    font-size: 18px;
    font-weight: 700;
}

QPushButton#SettingsButton:hover {
    background: #142238;
}

QFrame#ProfileBox {
    background: #0f1b2b;
    border: 1px solid #24364c;
    border-radius: 20px;
}

QLabel#Username {
    color: #ffffff;
    font-size: 13px;
    font-weight: 800;
}

QLabel#PageEyebrow {
    color: #e21b2f;
    font-size: 12px;
    font-weight: 900;
}

QLabel#PageTitle {
    color: #ffffff;
    font-size: 28px;
    font-weight: 900;
}

QLabel#PageSubtitle {
    color: #8290a1;
    font-size: 13px;
    font-weight: 600;
}

QFrame#DashboardCard {
    background: #0d1826;
    border: 1px solid #203044;
    border-radius: 10px;
}

QFrame#DashboardCard[highlight="true"] {
    border: 1px solid #852235;
    background: #111927;
}

QLabel#CardTitle {
    color: #ffffff;
    font-size: 14px;
    font-weight: 900;
}

QLabel#CardKicker {
    color: #68788c;
    font-size: 11px;
    font-weight: 800;
}

QLabel#MetricLabel {
    color: #7d8ca0;
    font-size: 11px;
    font-weight: 800;
}

QLabel#MetricValue {
    color: #ffffff;
    font-size: 19px;
    font-weight: 900;
}

QLabel#LargeMetricValue {
    color: #ffffff;
    font-size: 36px;
    font-weight: 900;
}

QLabel#RedMetricValue {
    color: #ff3448;
    font-size: 31px;
    font-weight: 900;
}

QLabel#TrackValue,
QLabel#CarValue {
    color: #ffffff;
    font-size: 26px;
    font-weight: 900;
}

QLabel#MutedText {
    color: #7a899b;
    font-size: 12px;
    font-weight: 700;
}

QFrame#StatPill {
    background: #101c2c;
    border: 1px solid #26384e;
    border-radius: 8px;
}

QFrame#Divider {
    background: #223247;
}

QTableView#RaceHistoryTable {
    background: #0d1826;
    alternate-background-color: #0d1826;
    border: 1px solid #203044;
    border-radius: 10px;
    gridline-color: transparent;
    color: #eef3f8;
    selection-background-color: #17263a;
    selection-color: #ffffff;
    outline: 0;
}

QTableView#RaceHistoryTable::item {
    border: 0px;
    padding: 0 12px;
}

QTableView#RaceHistoryTable::item:hover {
    background: #121f31;
}

QTableView#RaceHistoryTable::item:selected {
    background: #17263a;
}

QHeaderView#RaceHistoryTableHeader {
    background: #0f1b2b;
}

QHeaderView::section {
    background: #0f1b2b;
    color: #aeb9c8;
    border: 0px;
    border-bottom: 1px solid #7d1f2b;
    padding: 12px 12px;
    font-size: 11px;
    font-weight: 900;
}

QScrollBar:vertical {
    background: #0a1421;
    width: 12px;
    margin: 6px 3px 6px 3px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #27384e;
    min-height: 44px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #e21b2f;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
"""
