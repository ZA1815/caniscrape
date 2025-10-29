from __future__ import annotations

import requests
from urllib.parse import urlparse, urlunparse
import random
from curl_cffi.requests import Session as CurlCffiSession

from ..utils.browser_identities import MODERN_BROWSER_IDENTITIES
from ..utils.impersonate_target import get_impersonate_target

def check_robots_txt(url: str, proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Fetches and parses robots.txt to check for scraping directives.
    Returns crawl delay and whether scraping is disallowed for all user agents.
    """
    try:
        parsed_url = urlparse(url)
        robots_url = urlunparse((parsed_url.scheme, parsed_url.netloc, 'robots.txt', '', '', ''))

        if proxies:
            proxy = random.choice(proxies)

            chosen_identity = random.choice(MODERN_BROWSER_IDENTITIES)
            user_agent = chosen_identity.get('User-Agent', '')
            impersonate_target = get_impersonate_target(user_agent)

            with CurlCffiSession(impersonate=impersonate_target) as session:
                response = session.get(robots_url, headers=chosen_identity, timeout=15, allow_redirects=True, proxy=proxy)
        
        else:
            chosen_identity = random.choice(MODERN_BROWSER_IDENTITIES)
            user_agent = chosen_identity.get('User-Agent', '')
            impersonate_target = get_impersonate_target(user_agent)

            with CurlCffiSession(impersonate=impersonate_target) as session:
                response = session.get(robots_url, headers=chosen_identity, timeout=15, allow_redirects=True)

        if response.status_code == 200:
            if 'text/html' in response.headers.get('Content-Type', '').lower():
                return {'status': 'not_found'}

            crawl_delay = None
            scraping_disallowed = False
            is_generic_agent_block = False

            lines = response.text.splitlines()
            for line in lines:
                line = line.strip().lower()
                if not line or line.startswith('#'):
                    continue

                if line.startswith('user-agent:'):
                    agent = line.split(':', 1)[1].strip()
                    if agent == '*':
                        is_generic_agent_block = True
                    else:
                        is_generic_agent_block = False
                
                if is_generic_agent_block:
                    if line.startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path == '/':
                            scraping_disallowed = True
                    elif line.startswith('crawl-delay:'):
                        try:
                            delay_str = line.split(':', 1)[1].strip()
                            crawl_delay = float(delay_str)
                        except(ValueError, IndexError):
                            pass
            return {'status': 'success', 'crawl_delay': crawl_delay, 'scraping_disallowed': scraping_disallowed}
        
        elif 400 <= response.status_code < 500:
            return {'status': 'not_found'}
        else:
            print("Entering else block")
            return {'status': 'error', 'message': response.status_code}
        
    except requests.RequestException as e:
        return {'status': 'error', 'message': str(e)}