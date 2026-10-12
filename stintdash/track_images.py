import random
import re
from pathlib import Path

from PySide6.QtCore import QRect, QSize
from PySide6.QtGui import QPixmap


ASSETS_PICTURES_DIR = Path(__file__).resolve().parents[1] / "assets" / "pictures"


def center_crop_source(pixmap: QPixmap, target_size: QSize) -> QRect:
    if pixmap.isNull() or target_size.width() <= 0 or target_size.height() <= 0:
        return QRect()

    target_ratio = target_size.width() / target_size.height()
    source_ratio = pixmap.width() / pixmap.height()

    if source_ratio > target_ratio:
        source_width = int(pixmap.height() * target_ratio)
        source_x = (pixmap.width() - source_width) // 2
        return QRect(source_x, 0, source_width, pixmap.height())

    source_height = int(pixmap.width() / target_ratio)
    source_y = (pixmap.height() - source_height) // 2
    return QRect(0, source_y, pixmap.width(), source_height)


def random_track_picture(track: str) -> Path | None:
    prefix = track_picture_prefix(track)
    if not prefix:
        return None

    candidates = []
    for index in (1, 2, 3):
        pattern = f"{prefix}-picture-{index}.*"
        candidates.extend(
            path
            for path in ASSETS_PICTURES_DIR.glob(pattern)
            if path.suffix.casefold() in {".png", ".jpg", ".jpeg"}
        )

    return random.choice(candidates) if candidates else None


def track_picture_prefix(track: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", track.casefold())
    if not normalized:
        return ""

    aliases = (
        (("bahrain",), "Bahrain"),
        (("barcelona", "circuitdebarcelona", "barca"), "Barca"),
        (("lemans", "sarthe", "circuitdelasarthe", "circuitdes24heuresdumans"), "Sarthe"),
        (("paulricard",), "PaulRicard"),
        (("cota", "circuitoftheamericas"), "COTA"),
        (("daytona",), "Daytona"),
        (("fuji",), "Fuji"),
        (("imola",), "Imola"),
        (("interlagos",), "Interlagos"),
        (("lusail",), "Lusail"),
        (("roadatlanta",), "RoadAtlanta"),
        (("monza",), "Monza"),
        (("portimao",), "Portimao"),
        (("sebring",), "Sebring"),
        (("silverstone",), "Silverstone"),
        (("spafrancorchamps", "spa"), "Spa"),
        (("longbeach",), "LongBeach"),
        (("lagunaseca", "laguna"), "Laguna"),
    )
    for needles, prefix in aliases:
        if any(needle in normalized for needle in needles):
            return prefix
    return ""
