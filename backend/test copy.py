import asyncio
from safestreets.clients.google_maps import satellite_url, streetview_url, streetview_capture_date

lat, lng = 37.7648, -122.2239  # International Blvd & 35th Ave, Oakland

async def main():
    print(satellite_url(lat, lng))
    print(streetview_url(lat, lng, "north"))
    date = await streetview_capture_date(lat, lng)
    print("capture date:", date)

asyncio.run(main())
