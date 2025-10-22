from __future__ import annotations

import warnings
import logging

warnings.filterwarnings("ignore", message="Event loop is closed", category=RuntimeWarning)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

import asyncio
import aiohttp
import random
from curl_cffi.requests import AsyncSession

from ..utils.browser_identities import MODERN_BROWSER_IDENTITIES
from ..utils.impersonate_target import get_impersonate_target

GENTLE_PROBE_COUNT = 4
BURST_COUNT = 8
DEFAULT_DELAY = 3.0

BLOCKING_STATUS_CODES = {429, 403, 503, 401}

BROWSER_IDENTITY = random.choice(MODERN_BROWSER_IDENTITIES)

async def _make_request(session: aiohttp.ClientSession, url: str, proxies: tuple[str, ...] = ()) -> int:
    """
    Makes a single asynchronous GET request and returns the status code.
    """
    proxy = random.choice(proxies) if proxies else None
    try:
        async with session.get(url, headers=BROWSER_IDENTITY, timeout=15, allow_redirects=True, proxy=proxy) as response:
            response.release()
            return response.status
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return 999

async def _make_impersonated_request(url: str, impersonate_target: str, proxies: tuple[str, ...] = ()) -> int:
    proxy = random.choice(proxies) if proxies else None
    proxies_dict = {"http": proxy, "https": proxy} if proxy else None
    try:
        async with AsyncSession(impersonate=impersonate_target, proxies=proxies_dict) as session:
            response = await session.get(url, headers=BROWSER_IDENTITY, timeout=15, allow_redirects=True)
            return response.status_code
    except Exception:
        return 999
    
async def _run_rate_limit_profiler(url: str, baseline_delay: float, impersonate: bool = False, proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Runs the full multi-phase rate limit profile using the provided baseline delay.
    """
    results = {'requests_sent': 0, 'blocking_code': None, 'details': ''}

    if impersonate:
        user_agent = BROWSER_IDENTITY.get('User-Agent', '')
        impersonate_target = get_impersonate_target(user_agent)
        request_func = lambda: _make_impersonated_request(url, impersonate_target, proxies)
    else:
        session_manager = aiohttp.ClientSession()
        session = await session_manager.__aenter__()
        request_func = lambda: _make_request(session, url, proxies)

    try:
        for i in range(GENTLE_PROBE_COUNT):
            status = await request_func()
            results['requests_sent'] += 1
            if status in BLOCKING_STATUS_CODES:
                results['blocking_code'] = status
                results['details'] = f'Blocked after {results["requests_sent"]} requests with a {baseline_delay:.1f}s delay.'
                return results
            if i < GENTLE_PROBE_COUNT - 1:
                await asyncio.sleep(baseline_delay)

        burst_tasks = [request_func() for _ in range(BURST_COUNT)]
        burst_statuses = await asyncio.gather(*burst_tasks)
        results['requests_sent'] += len(burst_statuses)

        for status in burst_statuses:
            if status in BLOCKING_STATUS_CODES:
                results['blocking_code'] = status
                results['details'] = f'Blocked during a concurrent burst of {BURST_COUNT} requests.'
                return results
    finally:
        # --- Teardown Phase ---
        if session_manager:
            await session_manager.__aexit__(None, None, None)

    results['details'] = f'No blocking detected after {results["requests_sent"]} requests.'
    return results

async def profile_rate_limits(url: str, crawl_delay: float | None, impersonate: bool = False, proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Main synchronous entry point. It selects the delay and runs the async profile.
    """
    delay_to_use = crawl_delay if crawl_delay is not None else DEFAULT_DELAY

    try:
        profile_results = await _run_rate_limit_profiler(url, delay_to_use, impersonate, proxies)
        return {'status': 'success', 'results': profile_results}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}