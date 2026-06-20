"""The placement logic is deterministic, so it's worth a real test — a wrong-corner
marker is the demo killer this module exists to prevent."""
from safestreets.models.condition import NamedZone
from safestreets.vision.geometry import spread_overlapping, zone_to_pixel


def test_corners_map_to_distinct_quadrants():
    w = h = 640
    nw = zone_to_pixel(NamedZone.NW, w, h)
    se = zone_to_pixel(NamedZone.SE, w, h)
    assert nw[0] < w / 2 and nw[1] < h / 2     # NW is top-left
    assert se[0] > w / 2 and se[1] > h / 2     # SE is bottom-right


def test_center_is_centered():
    assert zone_to_pixel(NamedZone.CENTER, 640, 640) == (320, 320)


def test_overlapping_markers_are_spread():
    pts = spread_overlapping([NamedZone.NW, NamedZone.NW], 640, 640)
    assert pts[0] != pts[1]
