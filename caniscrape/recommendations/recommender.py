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
        tools.add('A CAPTCHA solving service (e.g., 2Captcha, Capsolver, Anti-Captcha).')
        strategy.add('Integrate the CAPTCHA solver into your script to handle challenges when they appear.')

    if results.get('behavioral', {}).get('honeypot_detected'):
        strategy.add('Scrape carefully with a headless browser. Do not interact with or request invisible elements.')

    rate_limit_results = results.get('rate_limit', {}).get('results', {})
    if rate_limit_results.get('blocking_code'):
        tools.add('A pool of high-quality proxies (residential or mobile) to rotate IP addresses.')
        strategy.add('Implement delays between requests (e.g., 3-5 seconds).')
        strategy.add('Rotate User-Agents and other headers on every request.')
    
    wafs_list = results.get('waf', {}).get('wafs', [])
    if wafs_list:
        first_waf = wafs_list[0]
        if isinstance(first_waf, dict):
            waf_name = first_waf.get('name', '')
        else:
            waf_name = first_waf[0] if first_waf else ''
        
        if 'Cloudflare' in waf_name or 'DataDome' in waf_name or 'PerimeterX' in waf_name:
            tools.add('A pool of high-quality proxies (residential or mobile) to rotate IP addresses.')
            strategy.add('Use a high-quality, non-generic User-Agent for all requests.')

    fingerprint_results = results.get('fingerprint', {})
    if fingerprint_results.get('status') == 'success':
        detected_services = fingerprint_results.get('detected_services', [])
        behavioral_listeners = fingerprint_results.get('behavioral_listeners_detected', [])
        canvas_signal = fingerprint_results.get('canvas_fingerprinting_signal', False)
        
        if detected_services:
            services_str = ', '.join(detected_services)
            strategy.add(f'Site uses advanced bot detection ({services_str}). Use undetected-chromedriver or playwright-stealth.')
            tools.add('An anti-detection browser automation library (e.g., undetected-chromedriver, playwright-stealth).')
        
        if behavioral_listeners:
            strategy.add('Site monitors user behavior (mouse, keyboard, scroll). Simulate realistic human-like movements.')
            strategy.add('Add random delays and jitter between actions to appear more human.')
        
        if canvas_signal:
            strategy.add('Canvas fingerprinting detected. Use a browser automation tool with built-in evasion (not basic requests).')

    integrity_results = results.get('integrity', {})
    if integrity_results.get('status') == 'success':
        modified_functions = integrity_results.get('modified_functions', {})
        
        if modified_functions:
            has_canvas_mods = any('Canvas' in func for func in modified_functions.keys())
            has_timing_mods = any('Date.now' in func or 'performance.now' in func for func in modified_functions.keys())
            
            if has_canvas_mods:
                strategy.add('Site modifies canvas functions (strong fingerprinting). Avoid basic automation libraries.')
            
            if has_timing_mods:
                strategy.add('Site monitors timing patterns. Vary your request timing to appear less robotic.')
            
            if not (has_canvas_mods or has_timing_mods):
                strategy.add('Site modifies browser functions. Use advanced evasion techniques and test thoroughly.')

    if not tools:
        tools.add('Standard HTTP clients (like requests or aiohttp) should be sufficient.')
    if not strategy:
        strategy.add('A simple, direct scraping approach should work.')

    return {'tools': sorted(list(tools)), 'strategy': sorted(list(strategy))}