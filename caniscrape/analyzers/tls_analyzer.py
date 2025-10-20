from __future__ import annotations

import asyncio
import aiohttp
from curl_cffi.requests import AsyncSession
import random

from ..utils.browser_identities import MODERN_BROWSER_IDENTITIES
from ..utils.impersonate_target import get_impersonate_target

async def _run_tls_test(url: str) -> dict[str, any]:
    """
    Conducts a controlled experiment to detect TLS fingerprinting using a single,
    randomly chosen browser identity for both requests.
    """
    results = {'python_request_blocked': None, 'browser_request_blocked': None}
    chosen_identity = random.choice(MODERN_BROWSER_IDENTITIES)
    user_agent = chosen_identity.get('User-Agent', '')

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=chosen_identity, timeout=20, allow_redirects=True) as response:
                results['python_request_blocked'] = response.status >= 400
    except (aiohttp.ClientError, asyncio.TimeoutError):
        results['python_request_blocked'] = True
    
    try:
        impersonate_target = get_impersonate_target(user_agent)
        async with AsyncSession(impersonate=impersonate_target) as session:
            response = await session.get(url, headers=chosen_identity, timeout=20, allow_redirects=True)
            results['browser_request_blocked'] = response.status_code >= 400
    except Exception as e:
        results['browser_request_blocked'] = True

    return results

def analyze_tls_fingerprint(url: str) -> dict[str, any]:
    """
    Main synchronous entry point. It runs the TLS test and interprets the results.
    """
    test_results = asyncio.run(_run_tls_test(url))

    python_blocked = test_results['python_request_blocked']
    browser_blocked = test_results['browser_request_blocked']

    if python_blocked and not browser_blocked:
        return {'status': 'active', 'details': 'Site blocks standard Python clients but allows browser-like clients.'}
    elif not python_blocked and not browser_blocked:
        return {'status': 'inactive', 'details': 'Site does not appear to block based on TLS fingerprint.'}
    else:
        return {'status': 'inconclusive', 'details': 'Could not determine fingerprinting status, site may be blocking all requests'}