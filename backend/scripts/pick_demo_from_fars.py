"""Find a real, documented fatal pedestrian crash to anchor the demo's opening story."""
from __future__ import annotations

import asyncio

from safestreets.clients.nhtsa import get_case_list


async def main() -> None:
    cases = await get_case_list(state=6, from_year=2022, to_year=2024)  # 6 = California
    print(f"fetched {len(cases)} cases; filter for pedestrian fatalities near your city")
    # TODO: filter by person type (pedestrian) and proximity to a candidate intersection


if __name__ == "__main__":
    asyncio.run(main())
