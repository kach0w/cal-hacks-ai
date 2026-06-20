import asyncio
from safestreets.clients.google_maps import satellite_url, streetview_url, streetview_capture_date
from safestreets.models.intersection import Intersection, ImageRef, ViewDirection
from safestreets.vision.stage1_blind import run_blind_pass
from safestreets.vision.stage2_corroborate import corroborate
from safestreets.intervention.matcher import match
from safestreets.lastmile.ask import build_social_post, build_council_report

# Hardcoded community data for the demo intersection
DEMO_COMMUNITY_DATA = {
    "crash_data": [
        {"year": 2023, "type": "pedestrian", "narrative": "pedestrian struck during turning movement", "precision": "intersection"},
        {"year": 2022, "type": "pedestrian", "narrative": "vehicle failed to yield at crosswalk", "precision": "intersection"},
        {"year": 2021, "type": "pedestrian", "narrative": "right-turn conflict, visibility obscured", "precision": "intersection"},
        {"year": 2021, "type": "cyclist", "narrative": "cyclist struck, sight line obstruction cited", "precision": "intersection"},
        {"year": 2020, "type": "pedestrian", "narrative": "pedestrian fatality, speed cited", "precision": "intersection"},
    ],
    "complaints_311": [
        {"id": "311-2847221", "date": "2022-07-14", "category": "crosswalk marking", "text": "crosswalk completely gone, paint faded years ago"},
        {"id": "311-2901443", "date": "2023-02-03", "category": "vegetation", "text": "bushes on corner blocking view of pedestrians"},
        {"id": "311-2756100", "date": "2021-09-20", "category": "signal timing", "text": "no time to cross before cars turn"},
    ],
    "news": [
        {"source": "East Bay Times", "date": "2023-03-14", "excerpt": "witness said she couldn't see the pedestrian until it was too late, shrubs on the corner"},
        {"source": "Oakland Local", "date": "2021-11-02", "excerpt": "residents have complained about faded crosswalk markings for years with no response"},
    ],
    "council": [
        {"date": "2022-06-07", "body": "Oakland City Council", "excerpt": "International Blvd corridor mentioned twice, no action recorded"},
    ],
}

INTERSECTIONS = [
    (37.8716, -122.2727, "Telegraph Ave & Bancroft Way, Berkeley"),
    (37.8699, -122.2680, "Telegraph Ave & Durant Ave, Berkeley"),
    (37.8684, -122.2596, "College Ave & Ashby Ave, Berkeley"),
    (37.8759, -122.2985, "San Pablo Ave & Gilman St, Berkeley"),
    (37.8649, -122.3010, "San Pablo Ave & Ashby Ave, Berkeley"),
]

async def build_intersection(lat: float, lng: float, address: str, city: str) -> Intersection:
    raw_date = await streetview_capture_date(lat, lng)
    capture_date = f"{raw_date}-01" if raw_date and len(raw_date) == 7 else raw_date
    slug = address.lower().replace(" ", "-").replace(",", "").replace("&", "and")[:40]
    images = [
        ImageRef(direction=ViewDirection.SATELLITE, url=satellite_url(lat, lng)),
        ImageRef(direction=ViewDirection.NORTH,     url=streetview_url(lat, lng, "north"),  capture_date=capture_date),
        ImageRef(direction=ViewDirection.SOUTH,     url=streetview_url(lat, lng, "south"),  capture_date=capture_date),
        ImageRef(direction=ViewDirection.EAST,      url=streetview_url(lat, lng, "east"),   capture_date=capture_date),
        ImageRef(direction=ViewDirection.WEST,      url=streetview_url(lat, lng, "west"),   capture_date=capture_date),
    ]
    return Intersection(id=slug, address=address, lat=lat, lng=lng, city=city, images=images)


async def run_one(lat: float, lng: float, address: str):
    print(f"\n{'='*60}")
    print(f"  {address}")
    print(f"{'='*60}")
    intersection = await build_intersection(lat, lng, address, "Berkeley")

    conditions = await run_blind_pass(intersection)
    print("Stage 1:")
    for c in conditions:
        print(f"  [{c.zone.value}] [{c.confidence.value.upper()}] — [{c.observation}]")

    print("Stage 2 (corroboration):")
    findings = await corroborate(conditions, DEMO_COMMUNITY_DATA)
    for f in findings:
        sources = ", ".join(c.source for c in f.corroboration) or "none"
        print(f"  [{f.condition.zone.value}] {f.status.value} — {sources}")

    print("Stage 3 (intervention match):")
    for f in findings:
        f.intervention = match(f.condition)
        if f.intervention:
            print(f"  [{f.condition.zone.value}] → {f.intervention.name}")
        else:
            print(f"  [{f.condition.zone.value}] → NO MATCH: {f.condition.observation[:60]}")

    print("Stage 4 (last-mile packet):")
    social = await build_social_post(findings, intersection, DEMO_COMMUNITY_DATA)
    print(f"\n  SOCIAL POST:\n  {social}\n")
    report = await build_council_report(findings, intersection, DEMO_COMMUNITY_DATA)
    print(f"  COUNCIL REPORT:\n{report}")


async def main():
    lat, lng, address = INTERSECTIONS[0]
    await run_one(lat, lng, address)


asyncio.run(main())
