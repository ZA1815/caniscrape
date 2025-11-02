from __future__ import annotations

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import math
import random

from ..utils.browser_identities import MODERN_BROWSER_IDENTITIES

TEST_IDENTITY = random.choice(MODERN_BROWSER_IDENTITIES)

HONEYPOT_THRESHOLD = 3

def detect_honeypots(url: str, scan_depth: str = 'default', proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Launches a headless browser to analyze a page for honeypots, which are traps for bots.
    """
    try:
        with sync_playwright() as p:
            launch_options = {'headless': True}
            if proxies:
                proxy = random.choice(proxies)
                launch_options['proxy'] = {'server': proxy}\
                
            browser = p.chromium.launch(**launch_options)
            page = browser.new_page(extra_http_headers=TEST_IDENTITY)

            page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "media"] else route.continue_())

            page.goto(url, wait_until='domcontentloaded', timeout=30000)

            links_locator = page.locator('a')
            total_links = links_locator.count()

            if total_links == 0:
                browser.close()
                return {'status': 'success', 'total_links': 0, 'invisible_links': 0, 'honeypot_detected': False}
            
            links_to_check = 0
            if scan_depth == 'thorough':
                links_to_check = math.ceil(total_links * 0.66)
            elif scan_depth == 'deep':
                links_to_check = total_links
            elif scan_depth == 'default':
                links_to_check = min(math.ceil(total_links * 0.33), 250)
            
            invisible_links_count = 0
            for i in range(links_to_check):
                link = links_locator.nth(i)
                if not link.is_visible():
                    invisible_links_count += 1
            
            browser.close()

            honeypot_detected = invisible_links_count > HONEYPOT_THRESHOLD

            return {'status': 'success', 'total_links': total_links, 'invisible_links': invisible_links_count, 'honeypot_detected': honeypot_detected, 'links_checked': links_to_check}
        
    except PlaywrightTimeoutError:
        return {'status': 'error', 'message': 'Page load timed out.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}