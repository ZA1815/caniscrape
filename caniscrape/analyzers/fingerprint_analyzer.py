from __future__ import annotations
import random
from playwright.sync_api import sync_playwright, Playwright, Page, TimeoutError as PlaywrightTimeoutError
from typing import Any
import json

from ..utils.playwright_proxy_parser import parse_proxy_for_playwright

KNOWN_BOT_DETECTION_SCRIPTS = {
    "PerimeterX (HUMAN)": [
        "client.perimeterx.net",
        "px-cdn.net",
        "collector-px.perimeterx.net"
    ],
    "DataDome": [
        "datadome.co/js",
        "api.datadome.co/js",
        "js.datadome.co"
    ],
    "Akamai Bot Manager": [
        "akam-bm.net",
        "ak-bm.net",
        "ds-aksb-a.akamaihd.net"
    ],
    "Cloudflare Bot Management": [
        "/cf-challenge/",
        "cdn-cgi/challenge-platform",
        "cf_bm"
    ],
    "Imperva (Incapsula)": [
        "incapsula.com",
        "/_Incapsula_Resource"
    ],
    "Kasada": [
        "api.kasada.io",
        "/kasada-api/"
    ],
    "Shape Security (F5)": [
        "shapeshifter.io",
        "shape-only.com",
        "/F5-shape-security-js"
    ],
    "CHEQ": [
        "cheqzone.com",
        "api.cheq.ai"
    ],
    "Radware Bot Manager": [
        "radwarebotmanager.com",
        "/rbm/rbm.js"
    ]
}

KNOWN_BOT_GLOBAL_OBJECTS = {
    "PerimeterX (HUMAN)": ["_px", "PX", "px"],
    "DataDome": ["ddjskey", "datadome"],
    "Akamai Bot Manager": ["bmak"],
    "Imperva (Incapsula)": ["Reese84"],
    "Kasada": ["kasada"],
    "Shape Security (F5)": ["_sd"]
}

JS_PROBE_SCRIPT = """
() => {
    window.__caniscrape_listeners_log = [];
    const log = window.__caniscrape_listeners_log;

    const originalAddEventListener = EventTarget.prototype.addEventListener;

    const suspiciousEvents = ['mousemove', 'mousedown', 'mouseup', 'keydown', 'keyup', 'scroll', 'touchstart', 'touchend'];

    EventTarget.prototype.addEventListener = function(type, listener, options) {
        if (suspiciousEvents.includes(type)) {
            log.push(type);
        }
        return originalAddEventListener.call(this, type, listener, options);
    };
};
"""

def analyze_fingerprinting(url: str, proxies: tuple[str, ...] = ()) ->  dict[str, Any]:
    """
    Launches a headless browser to probe for advanced, client-side protections
    and behavioral analysis
    """
    results = {
        'status': 'error',
        'message': 'Analysis did not complete.',
        'detected_services': [],
        'canvas_fingerprinting_signal': False,
        'behavioral_listeners_detected': []
    }

    captured_script_urls = set()

    try:
        with sync_playwright() as p:
            launch_options = {'headless': True}
            if proxies:
                proxy = random.choice(proxies)
                proxy_config = parse_proxy_for_playwright(proxy)
                if proxy_config:
                    launch_options['proxy'] = proxy_config

            browser = p.chromium.launch(**launch_options)
            page = browser.new_page()

            page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font", "media"] else route.continue_())

            page.add_init_script(JS_PROBE_SCRIPT)

            page.on('request', lambda request: captured_script_urls.add(request.url))

            page.goto(url, wait_until='load', timeout=30000)
            page.wait_for_timeout(3000)

            static_probes = page.evaluate(f"""
            () => {{
                const results = {{
                    canvas_patched: HTMLCanvasElement.prototype.toDataURL.toString().indexOf('native code') === -1,
                    found_globals: []
                }};
                
                const global_objects = {json.dumps(KNOWN_BOT_GLOBAL_OBJECTS)};
                
                for (const [service, objects] of Object.entries(global_objects)) {{
                    for (const obj_name of objects) {{
                        if (window[obj_name]) {{
                            results.found_globals.push(service);
                            break;
                        }}
                    }}
                }}
                return results;
            }}
            """)

            listener_log = page.evaluate('() => window.__caniscrape_listeners_log')

            browser.close()

            for service, patterns in KNOWN_BOT_DETECTION_SCRIPTS.items():
                for url_part in patterns:
                    if any(url_part in script_url for script_url in captured_script_urls):
                        if service not in results['detected_services']:
                            results['detected_services'].append(service)
            
            if static_probes.get('canvas_patched'):
                results['canvas_fingerprinting_signal'] = True
            
            if static_probes.get('found_globals'):
                for service in static_probes['found_globals']:
                    if service not in results['detected_services']:
                        results['detected_services'].append(service)

            if listener_log:
                unique_listeners = sorted(list(set(listener_log)))
                results['behavioral_listeners_detected'] = unique_listeners
            
            results['status'] = 'success'
            results['message'] = 'Analysis complete.'
            return results
    except PlaywrightTimeoutError:
        results['message'] = 'Page load time out.'
        return results
    except Exception as e:
        results['message'] = str(e)
        return results