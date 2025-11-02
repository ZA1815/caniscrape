from __future__ import annotations

import random
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from curl_cffi.requests import Session as CurlCffiSession

from ..utils.browser_identities import MODERN_BROWSER_IDENTITIES
from ..utils.impersonate_target import get_impersonate_target

TEST_IDENTITY = random.choice(MODERN_BROWSER_IDENTITIES)

def _extract_visible_text(html_content: str) -> str:
    """
    Parses HTML and extracts the clean, visible text.
    """
    if not html_content:
        return
    soup = BeautifulSoup(html_content, 'html.parser')

    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()
    
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split(' '))
    return '\n'.join(chunk for chunk in chunks if chunk)

def analyze_js_rendering(url: str, proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Analyzes a URL to determine if JavaScript is required to render its main content.
    """
    user_agent = TEST_IDENTITY.get('User-Agent', '')
    impersonate_target = get_impersonate_target(user_agent)

    proxy = random.choice(proxies) if proxies else None
    proxies_dict = {"http": proxy, "https": proxy} if proxy else None
    try:
        with CurlCffiSession(impersonate=impersonate_target, proxies=proxies_dict) as session:
            no_js_response = session.get(url, headers=TEST_IDENTITY, timeout=30)
            no_js_response.raise_for_status()
            no_js_text = _extract_visible_text(no_js_response.text)
            len_no_js = len(no_js_text)

        with sync_playwright() as p:
            launch_options = {'headless': True}
            if proxy:
                launch_options['proxy'] = {'server': proxy}

            browser = p.chromium.launch(**launch_options)
            page = browser.new_page(extra_http_headers=TEST_IDENTITY)

            page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "media"] else route.continue_())
            
            try:
                page.goto(url, wait_until='load', timeout=30000)
                page.wait_for_load_state('networkidle', timeout=5000)
            except:
                pass

            page.wait_for_timeout(2000)

            js_html = page.content()
            browser.close()
        
        js_text = _extract_visible_text(js_html)
        len_js = len(js_text)

        if len_js == 0:
            return {'status': 'error', 'message': 'Could not extract content from the page with JS enabled.'}
        
        difference_percentage = (1 - (len_no_js / len_js)) * 100

        is_required = difference_percentage > 25
        is_single_page_app = difference_percentage > 75

        return {'status': 'success', 'js_required': is_required, 'is_spa': is_single_page_app, 'content_difference_%': round(difference_percentage, 2)}
    
    except Exception as e:
        return {'status': 'error', 'message': str(e)}