from __future__ import annotations

def generate_recommendations(results: dict[str, any]) -> dict[str, list[str]]:
    """
    Generates a list of required tools and strategy tips based on the analysis.
    """
    tools = set()
    strategy = set()

    if results.get('js', {}).get('js_required'):
        tools.add('A headless browser like Playwright or Selenium for JavaScript rendering.')
        strategy.add('Ensure your scraper waits for dynamic content to load before extracting data.')

    if results.get('tls', {}).get('status') == 'active':
        tools.add('A library with browser impersonation like curl_cffi, or a full headless browser.')
        strategy.add('Standard Python HTTP clients (like requests/aiohttp) will be blocked.')

    if results.get('captcha', {}).get('captcha_detected'):
        tools.add('A CAPTCHA solving service (e.g., 2Captcha, Anti-Captcha).')
        strategy.add('Integrate the CAPTCHA solver into your script to handle challenges when they appear.')

    if results.get('behavioral', {}).get('honeypot_detected'):
        strategy.add('Scrape carefully with a headless browser. Do not interact with or request invisible elements.')

    rate_limit_results = results.get('rate_limit', {}).get('results', {})
    if rate_limit_results.get('blocking_code'):
        tools.add('A pool of high-quality proxies (residential or mobile) to rotate IP addresses.')
        strategy.add('Implement delays between requests (e.g., 3-5 seconds).')
        strategy.add('Rotate User-Agents and other headers on every request.')
    
    waf_name = results.get('waf', {}).get('wafs', [[None]])[0][0] or ''
    if 'Cloudflare' in waf_name or 'DataDome' in waf_name or 'PerimeterX' in waf_name:
        tools.add('A pool of high-quality proxies (residential or mobile) to rotate IP addresses.')
        strategy.add('Use a high-quality, non-generic User-Agent for all requests.')

    if not tools:
        tools.add('Standard HTTP clients (like requests or aiohttp) should be sufficient.')
    if not strategy:
        strategy.add('A simple, direct scraping approach should work.')

    return {'tools': sorted(list(tools)), 'strategy': sorted(list(strategy))}