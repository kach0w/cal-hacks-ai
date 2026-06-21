"""Configured Anthropic async client with rate-limit protection."""
from __future__ import annotations

import asyncio
import logging
from functools import lru_cache

from anthropic import AsyncAnthropic, RateLimitError

from safestreets.config import get_settings

log = logging.getLogger(__name__)

# Serialize all Claude calls so we never fire >1 at a time and blow the TPM cap.
_SEMAPHORE = asyncio.Semaphore(1)


@lru_cache
def get_anthropic() -> AsyncAnthropic:
    # max_retries=0 — we do our own retry loop so we can log and respect the semaphore.
    return AsyncAnthropic(api_key=get_settings().anthropic_api_key, max_retries=0)


async def call_with_backoff(fn, *, max_attempts: int = 6, base_delay: float = 15.0):
    """Run an Anthropic API call under the global semaphore with exponential backoff on 429."""
    async with _SEMAPHORE:
        delay = base_delay
        for attempt in range(max_attempts):
            try:
                return await fn()
            except RateLimitError:
                if attempt == max_attempts - 1:
                    raise
                log.warning("Rate limited by Anthropic — waiting %.0fs (attempt %d/%d)", delay, attempt + 1, max_attempts)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 120)
