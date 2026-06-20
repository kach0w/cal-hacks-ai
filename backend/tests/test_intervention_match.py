from safestreets.intervention import funding_match, matcher
from safestreets.models.condition import Confidence, NamedZone, ObservedCondition


def _cond(text: str) -> ObservedCondition:
    return ObservedCondition(
        zone=NamedZone.NW, observation=text, source_view="satellite",
        confidence=Confidence.HIGH,
    )


def test_vegetation_maps_to_clearance_and_maintenance_funding():
    iv = matcher.match(_cond("mature shrubs obscure pedestrian sightline"))
    assert iv is not None and iv.key == "vegetation"
    programs = funding_match.programs_for(iv)
    assert any(p.key == "maintenance" for p in programs)


def test_curb_extension_matches_parking_blind_spot():
    iv = matcher.match(_cond("no curb extension; parking extends to crosswalk line"))
    assert iv is not None and iv.key == "curb_extension"
