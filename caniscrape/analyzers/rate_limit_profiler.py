import asyncio
import aiohttp
import random

GENTLE_PROBE_COUNT = 4
BURST_COUNT = 8
DEFAULT_DELAY = 3.0

BLOCKING_STATUS_CODES = {429, 403, 503, 401}

MODERN_BROWSER_IDENTITIES = [
    # --- Chrome on Windows ---
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    },
    # --- Firefox on Windows (does not use sec-ch-ua) ---
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    },
    # --- Edge on Windows ---
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "sec-ch-ua": '"Chromium";v="130", "Microsoft Edge";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    },
    # --- Chrome on macOS ---
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    },
    # --- Safari on macOS (does not use sec-ch-ua) ---
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    },
    # --- Chrome on macOS (newer OS version) ---
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    },
    # --- Chrome on Android ---
    {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
    },
    # --- Chrome on iPhone ---
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0.6723.90 Mobile/15E148 Safari/604.1",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"iOS"',
    },
    # --- Safari on iPhone (does not use sec-ch-ua) ---
    {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    },
]

async def _make_request(session: aiohttp.ClientSession, url: str) -> int:
    """
    Makes a single asynchronous GET request and returns the status code.
    """
    browser_identity = random.choice(MODERN_BROWSER_IDENTITIES)
    
    try:
        async with session.get(url, timeout=15, headers=browser_identity, allow_redirects=True) as response:
            response.release()
            return response.status
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return 999
    
async def _run_rate_limit_profiler(url: str, baseline_delay: float) -> dict[str, any]:
    """
    Runs the full multi-phase rate limit profile using the provided baseline delay.
    """
    results = {'requests_sent': 0, 'blocking_code': None, 'details': ''}

    async with aiohttp.ClientSession() as session:
        for i in range(GENTLE_PROBE_COUNT):
            status = await _make_request(session, url)
            results['requests_sent'] += 1

            if status in BLOCKING_STATUS_CODES:
                results['blocking_code'] = status
                results['details'] = f'Blocked after {results['requests_sent']} requests with a {baseline_delay:.1f}s delay.'
                return results
            
            if i < GENTLE_PROBE_COUNT - 1:
                await asyncio.sleep(baseline_delay)

        burst_tasks = [_make_request(session, url) for _ in range(BURST_COUNT)]
        burst_statuses = await asyncio.gather(*burst_tasks)

        results['requests_sent'] += len(burst_statuses)

        for status in burst_statuses:
            if status in BLOCKING_STATUS_CODES:
                results['blocking_code'] = status
                results['details'] = f'Blocked during a concurrent burst of {BURST_COUNT} requests.'
                return results
    
    results['details'] = f'No blocking detected after {results['requests_sent']} requests.'
    return results

def profile_rate_limits(url: str, crawl_delay: float | None) -> dict[str, any]:
    """
    Main synchronous entry point. It selects the delay and runs the async profile.
    """
    delay_to_use = crawl_delay if crawl_delay is not None else DEFAULT_DELAY

    try:
        profile_results = asyncio.run(_run_rate_limit_profiler(url, delay_to_use))
        return {'status': 'success', 'results': profile_results}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}