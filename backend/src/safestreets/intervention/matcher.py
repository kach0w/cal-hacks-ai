"""Maps a finding's observed condition to a candidate intervention.

The mapping below is a deterministic baseline keyed on condition text. For richer
matching you can hand the condition + intervention library to Claude and let it pick,
but a judge trusts a transparent rule more than an opaque LLM choice here.
"""
from __future__ import annotations

from safestreets.intervention.library import interventions
from safestreets.models.condition import ObservedCondition
from safestreets.models.intervention import Intervention

# crude keyword -> intervention key map; refine during the build
_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("curb", "parking", "right-turn", "bulb"), "curb_extension"),
    (("vegetation", "shrub", "bush", "tree", "sightline", "sight line"), "vegetation"),
    (("crosswalk", "faded", "marking", "unmarked"), "hi_vis_crosswalk"),
    (("lpi", "leading pedestrian", "signal timing", "concurrent"), "lpi"),
    (("stop bar", "stop-bar", "encroach"), "stop_bar"),
    (("speed", "high-speed", "fast"), "speed_camera"),
    (("refuge", "island", "multilane", "wide"), "refuge_island"),
    (("left-turn", "left turn"), "left_turn_phase"),
    (("uncontrolled", "mid-block", "midblock", "rrfb", "beacon"), "rrfb"),
    (("raised",), "raised_crosswalk"),
]


def match(condition: ObservedCondition) -> Intervention | None:
    text = condition.observation.lower()
    lib = interventions()
    for words, key in _KEYWORDS:
        if any(w in text for w in words) and key in lib:
            return lib[key]
    return None
